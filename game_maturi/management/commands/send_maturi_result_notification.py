"""
祭り結果発表通知コマンド

結果発表日の11時に参加者へ結果通知を送信する
Heroku Schedulerで毎日11時（JST = UTC 02:00）に実行

通知内容:
1. 予想成績ランキング（正解数・正解率）
2. 忍者小説ランキング（逃げ切り作品 = 外れた人が多かった小説）
"""
from django.core.management.base import BaseCommand
from django.core.mail import send_mail, get_connection
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core import signing
from django.db import transaction
from django.db.models import Count, Q
from game_maturi.models import MaturiGame, GamePrediction
import logging
import time

User = get_user_model()
logger = logging.getLogger(__name__)


def get_unsubscribe_url(user):
    """配信停止URL生成"""
    token = signing.dumps(user.id, salt='email_unsubscribe')
    return f"{settings.BASE_URL}/accounts/unsubscribe/{token}/"


def get_prediction_rankings(game):
    """
    予想成績ランキングを取得
    戻り値: [(user, correct_count, total_count, accuracy), ...]
    """
    # 祭りの小説を取得
    novels = game.maturi_novels.all()
    total_novels = novels.count()

    if total_novels == 0:
        return []

    # 参加者ごとの予想を集計
    rankings = []

    # 予想した全ユーザーを取得
    predictors = GamePrediction.objects.filter(
        maturi_game=game
    ).values_list('predictor', flat=True).distinct()

    for predictor_id in predictors:
        predictor = User.objects.get(id=predictor_id)
        predictions = GamePrediction.objects.filter(
            maturi_game=game,
            predictor=predictor
        ).select_related('novel', 'novel__original_author', 'predicted_author')

        total = predictions.count()
        correct = sum(1 for p in predictions if p.predicted_author_id == p.novel.original_author_id)
        accuracy = (correct / total * 100) if total > 0 else 0

        rankings.append({
            'user': predictor,
            'correct': correct,
            'total': total,
            'accuracy': accuracy
        })

    # 正解数で降順ソート、同数なら正解率でソート
    rankings.sort(key=lambda x: (-x['correct'], -x['accuracy']))

    return rankings


def get_ninja_novels(game):
    """
    忍者小説ランキングを取得（逃げ切り作品 = 正解者が少なかった小説）
    戻り値: [(novel, correct_count, total_predictions), ...]
    """
    novels = game.maturi_novels.all()
    ninja_rankings = []

    for novel in novels:
        predictions = GamePrediction.objects.filter(
            maturi_game=game,
            novel=novel
        )
        total_predictions = predictions.count()

        # 正解数をカウント（predicted_author == original_author）
        correct_count = sum(
            1 for p in predictions
            if p.predicted_author_id == novel.original_author_id
        )

        ninja_rankings.append({
            'novel': novel,
            'correct_count': correct_count,
            'total_predictions': total_predictions,
            'incorrect_count': total_predictions - correct_count
        })

    # 正解者数で昇順ソート（正解者が少ない順 = 逃げ切り度が高い）
    ninja_rankings.sort(key=lambda x: (x['correct_count'], -x['total_predictions']))

    return ninja_rankings[:3]  # 上位3作品


def get_rank_emoji(rank):
    """順位に応じた絵文字を返す"""
    if rank == 1:
        return '🏆優勝'
    elif rank == 2:
        return '🥈2位'
    elif rank == 3:
        return '🥉3位'
    else:
        return f'  {rank}位'


class Command(BaseCommand):
    help = '祭り結果発表通知を参加者に送信する（毎日11時JST実行）'

    def handle(self, *args, **options):
        # 🔥 JST時間取得
        now = timezone.localtime(timezone.now()).date()

        with transaction.atomic():
            # 結果発表日で、未送信の祭りを取得
            # 結果発表期間 = prediction_end_date の翌日 から maturi_end_date の前日まで
            # 結果発表日（prediction_end_date + 1日）が今日で、未送信のもの
            result_games = MaturiGame.objects.filter(
                result_notification_sent=False,
                is_author_revealed=True  # 作者公開済みのもの
            ).select_for_update(of=('self',))

            # 結果発表日が今日のゲームをフィルタ
            target_games = []
            for game in result_games:
                # 結果発表日 = prediction_end_date + 1日
                from datetime import timedelta
                result_date = game.prediction_end_date + timedelta(days=1)
                if result_date == now:
                    target_games.append(game)

            if not target_games:
                self.stdout.write(self.style.WARNING('送信対象の祭りはありません'))
                return

            # メール送信接続を再利用（効率化）
            connection = get_connection()
            connection.open()

            try:
                for game in target_games:
                    self.stdout.write(f'🎉 祭り結果通知送信開始: {game.title}')

                    # 予想成績ランキングを取得
                    rankings = get_prediction_rankings(game)

                    # 忍者小説ランキングを取得
                    ninja_novels = get_ninja_novels(game)

                    if not rankings:
                        self.stdout.write(self.style.WARNING(f'{game.title}: 予想データがありません'))
                        continue

                    # ランキング文字列を作成
                    ranking_text = ''
                    for i, r in enumerate(rankings, 1):
                        rank_emoji = get_rank_emoji(i)
                        ranking_text += f'{rank_emoji}  {r["user"].nickname}    {r["correct"]}/{r["total"]}（{r["accuracy"]:.1f}%）\n'

                    # 忍者小説文字列を作成
                    ninja_text = ''
                    for i, n in enumerate(ninja_novels, 1):
                        ninja_text += f'🥷{i}位 「{n["novel"].title}」- 正解者{n["correct_count"]}人\n'

                    # 結果ページURL
                    result_url = f"{settings.BASE_URL}/game_maturi/game_top/{game.id}/"

                    # 参加者（予想したユーザー）に送信
                    sent_count = 0
                    error_count = 0

                    predictor_ids = GamePrediction.objects.filter(
                        maturi_game=game
                    ).values_list('predictor', flat=True).distinct()

                    users = User.objects.filter(
                        id__in=predictor_ids,
                        is_active=True,
                        email_confirmed=True
                    )

                    for user in users:
                        try:
                            subject = f'【超短編小説会】🎉 {game.title} 結果発表！'
                            unsubscribe_url = get_unsubscribe_url(user)

                            message = f"""
{user.nickname} 様

🎉 祭りの結果が発表されました！

━━━━━━━━━━━━━━━━━━━━
■ 予想成績ランキング
━━━━━━━━━━━━━━━━━━━━
{ranking_text}
━━━━━━━━━━━━━━━━━━━━
■ 忍者小説ランキング（逃げ切り作品）
━━━━━━━━━━━━━━━━━━━━
{ninja_text}
━━━━━━━━━━━━━━━━━━━━

詳細はこちら: {result_url}

---
このメールの配信を停止する場合は、以下のリンクをクリックしてください。
{unsubscribe_url}

超短編小説会
                            """.strip()

                            send_mail(
                                subject,
                                message,
                                settings.DEFAULT_FROM_EMAIL,
                                [user.email],
                                fail_silently=False,
                                connection=connection,
                            )
                            sent_count += 1
                            masked_email = user.email[:3] + '***'
                            logger.info(f'祭り結果通知送信成功: {masked_email}')

                            # 🔥🔥🔥 レート制限対策：5秒待機 🔥🔥🔥
                            time.sleep(5)

                        except Exception as e:
                            error_count += 1
                            masked_email = user.email[:3] + '***'
                            logger.error(f'祭り結果通知送信失敗: {masked_email} - {str(e)}', exc_info=True)
                            continue

                    # 送信済みフラグを立てる
                    game.result_notification_sent = True
                    game.save()

                    self.stdout.write(
                        self.style.SUCCESS(f'✅ {game.title}: {sent_count}件送信成功、{error_count}件エラー')
                    )

            finally:
                connection.close()

        self.stdout.write(self.style.SUCCESS('📧 祭り結果通知送信完了'))
