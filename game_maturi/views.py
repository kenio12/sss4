from django.shortcuts import render, redirect, get_object_or_404  # Added get_object_or_404 here
from django.http import JsonResponse
import json
from .forms import MaturiNovelForm
from novels.models import Novel  # Assuming MaturiGame is in the same module as Novel
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone  # Add this import
# 正しいモジュールから MaturiGame をインポート
from .models import MaturiGame, Phrase  # Import Phrase model from models.py
from django.contrib import messages  # Added this import
import logging
from datetime import timedelta
from django.db import models
from .models import GamePrediction
from accounts.models import User  # カスタムユーザーモデルをインポート
from django.http import Http404
import random
from django.db.models import Prefetch
from django.db.models import F
from datetime import datetime
from functools import wraps
from django.views.decorators.http import require_http_methods
from freezegun import freeze_time
from datetime import datetime, timedelta, time
from django.conf import settings  # settingsをインポート
from collections import defaultdict
from datetime import date

# Create your views here.
logger = logging.getLogger('game_maturi.views')  # ここを変更

# @freeze_time("2024-12-20")  # 12月16日に固定
def game_maturi_top(request, game_id):
    logger.debug("=== View Debug ===")
    logger.debug(f"Function called: game_maturi_top")
    logger.debug(f"Game ID: {game_id}")
    if request.user.is_authenticated:
        logger.debug(f"User: {request.user.nickname}")
    else:
        logger.debug(f"User: 未ログイン")
    
    game = get_object_or_404(MaturiGame, id=game_id)
    novels = game.maturi_novels.filter(status='published')
    active_authors = game.entrants.all().order_by('nickname')
    now = timezone.localtime(timezone.now())  # 🔥 JST時間取得

    # 最後に終了したゲームを取得
    last_finished_game = MaturiGame.objects.filter(
        maturi_end_date__lt=now.date()  # 🔥 日付比較用に.date()追加
    ).order_by('-maturi_end_date').first()
    
    # novel_predictionsをここで初期化
    novel_predictions = {}

    # ユーザーがゲームに参加しているかチェック
    is_user_entered = False
    
    if request.user.is_authenticated:
        is_user_entered = game.entrants.filter(id=request.user.id).exists()
        
        # ユーザーの予想データを取得
        predictions = GamePrediction.objects.filter(
            maturi_game=game,
            predictor=request.user
        ).select_related('novel', 'predicted_author')
        
        for pred in predictions:
            novel_predictions[pred.novel.id] = {
                'predicted_author': {
                    'id': pred.predicted_author.id,
                    'nickname': pred.predicted_author.nickname
                }
            }

    # 🔥 予想期間中または予想期間終了後は公開済みの小説を取得
    # 執筆期間中かつ予想期間前のみ空にする（ゲームの公平性のため）
    if game.is_prediction_period() or game.is_prediction_period_finished():
        novels = game.maturi_novels.filter(
            status='published'  # 公開済みの小説のみに限定
        ).select_related('author', 'original_author').order_by('-published_date')  # 公開日の降順で並び替え
    else:
        novels = []

    # ユーザーの小説を取得（maturi_game_idが空でもゲーム期間中のものは表示）
    user_novels = []
    if request.user.is_authenticated and is_user_entered:
        from novels.models import Novel
        # original_authorが自分の小説を取得（ゲーム期間中のもの全て）
        user_novels = Novel.objects.filter(
            original_author=request.user,
            created_at__date__gte=game.maturi_start_date,
            created_at__date__lte=game.maturi_end_date
        ).order_by('-updated_at')  # 更新日の降順で並び替え

    # 基本のコンテキストを作成
    context = {
        'game': game,
        'novels': novels,
        'active_authors': active_authors,
        'last_finished_game': last_finished_game,
        'is_user_entered': is_user_entered,
        'novel_predictions': novel_predictions,  # 初期化済みの辞書を渡す
        'now': timezone.localtime(timezone.now()).date(),  # 🔥 JST日付取得
        'user_novels': user_novels,  # これを追加
    }

    # 予測期間が終了しているかどうかをチェック
    if game.is_prediction_period_finished():
        # GamePredictionのクエリを最適化
        predictions = GamePrediction.objects.filter(
            maturi_game=game
        ).select_related(
            'novel',
            'novel__original_author',
            'predictor',
            'predicted_author',
            'novel__original_author'
        ).prefetch_related(
            'novel__author'
        )

        # 予想データを一括取得
        all_predictions = GamePrediction.objects.filter(
            maturi_game=game
        ).select_related(
            'novel',
            'novel__original_author',
            'predictor',
            'predicted_author'
        )

        # 作品ごとの正解率を計算
        novel_stats = {}
        for novel in novels:
            # この作品に対する全予想を取得
            novel_preds = predictions.filter(novel=novel)
            total = novel_preds.count()
            correct = novel_preds.filter(
                predicted_author_id=F('novel__original_author_id')
            ).count()

            novel_stats[novel.id] = {
                'total': total,
                'correct': correct,
                'fraction': f"{correct}/{total}" if total > 0 else "0/0"
            }

        # ユーザーの予測と統計
        user_predictions = []
        stats = {'total': 0, 'correct': 0, 'accuracy': 0}

        if request.user.is_authenticated:
            user_predictions = predictions.filter(predictor=request.user)

            # ユーザーの予測データを格納
            user_novel_predictions = {}
            for pred in user_predictions:
                user_novel_predictions[pred.novel.id] = {
                    'predicted_author': pred.predicted_author,
                    'is_correct': pred.predicted_author_id == pred.novel.original_author_id
                }

        # 統計情報の計算
        total = user_predictions.count() if request.user.is_authenticated else 0
        correct = sum(1 for p in user_predictions if p.predicted_author_id == p.novel.original_author_id) if request.user.is_authenticated else 0
        
        user_stats = {
            'total': total,
            'correct': correct,
            'accuracy': (correct / total * 100) if total > 0 else 0
        }

        # 予想した全ユーザーの統計情報を計算（エントリーしてなくても予想した人は対象）
        participants_stats = []
        # 予想した全ユーザーを取得（重複なし）
        all_predictors = set(pred.predictor for pred in predictions)
        for predictor in all_predictors:
            predictor_predictions = predictions.filter(predictor=predictor)
            total = predictor_predictions.count()
            correct = sum(1 for p in predictor_predictions if p.predicted_author_id == p.novel.original_author_id)
            predictor_stats = {
                'total': total,
                'correct': correct,
                'accuracy': (correct / total * 100) if total > 0 else 0
            }
            participants_stats.append((predictor, predictor_stats))

        # 正解率で降順ソート（同率の場合は正解数で）
        participants_stats.sort(key=lambda x: (-x[1]['accuracy'], -x[1]['correct']))

        # 🥷 忍者小説ランキング（逃げ切り作品 = 正解者が少なかった小説）
        # 🔥 自分の小説に対する自分の予想は除外する（分子にも分母にも入れない）
        # 🔥 同じ正解数なら同率順位、3人以上同率1位なら2位以下は表示しない
        ninja_novels = []
        for novel in novels:
            # 自分の小説に対する自分の予想を除外してフィルタ
            novel_preds = predictions.filter(novel=novel).exclude(
                predictor_id=novel.original_author_id
            )
            total_preds = novel_preds.count()
            correct_count = novel_preds.filter(
                predicted_author_id=F('novel__original_author_id')
            ).count()
            ninja_novels.append({
                'novel': novel,
                'correct_count': correct_count,
                'total_predictions': total_preds,
                'incorrect_count': total_preds - correct_count
            })
        # 正解者数で昇順ソート（正解者が少ない順 = 逃げ切り度が高い）
        ninja_novels.sort(key=lambda x: (x['correct_count'], -x['total_predictions']))

        # 🔥 同率順位を計算して表示数を決定
        if ninja_novels:
            # 順位を付与（同じ正解数なら同率順位）
            current_rank = 1
            prev_correct = None
            ranked_novels = []
            for i, n in enumerate(ninja_novels):
                if prev_correct is not None and n['correct_count'] != prev_correct:
                    current_rank = i + 1
                n['rank'] = current_rank
                prev_correct = n['correct_count']
                ranked_novels.append(n)

            # 1位が3人以上いたら1位だけ表示、それ以外は3位まで表示
            first_place_count = sum(1 for n in ranked_novels if n['rank'] == 1)
            if first_place_count >= 3:
                ninja_novels = [n for n in ranked_novels if n['rank'] == 1]
            else:
                ninja_novels = [n for n in ranked_novels if n['rank'] <= 3]

        # context更新
        context.update({
            'all_predictions': predictions,
            'novel_predictions': user_predictions if request.user.is_authenticated else {},  # 変更！
            'predictions': user_predictions if request.user.is_authenticated and user_predictions else None,  # 予想がない場合はNone
            'novel_stats': novel_stats,
            'participants': participants_stats,
            'user_stats': user_stats,
            'total_predictions': total if total > 0 else 0,  # ユーザーの予想数
            'correct_predictions': correct if total > 0 else 0,  # ユーザーの正解数
            'accuracy': (correct / total * 100) if total > 0 else 0,  # ユーザーの正解率
            'active_authors': active_authors,
            'now': timezone.localtime(timezone.now()).date(),  # 🔥 JST日付取得
            'ninja_novels': ninja_novels,  # 🥷 忍者小説ランキング
        })

        # ユーザーの予想結果を計算
        if request.user.is_authenticated:
            user_predictions = all_predictions.filter(predictor=request.user)
            total_predictions = user_predictions.count()
            correct_predictions = sum(1 for p in user_predictions 
                                    if p.predicted_author_id == p.novel.original_author_id)
            accuracy = (correct_predictions / total_predictions * 100) if total_predictions > 0 else 0

            context.update({
                'total_predictions': total_predictions,
                'correct_predictions': correct_predictions,
                'accuracy': accuracy,
            })

    return render(request, 'game_maturi/game_maturi_top.html', context)

# @freeze_time("2024-12-20")
@login_required
def post_or_edit_maturi_novel(request, novel_id=None):
    if novel_id:
        novel = get_object_or_404(Novel, id=novel_id)
        # 小説へのアクセス権限チェックを追加
        if novel.status == 'draft' and novel.original_author != request.user:
            raise Http404("この小説は非公開です。")
    else:
        novel = None

    current_game = MaturiGame.find_current_game()
    is_writing_period = current_game and current_game.is_writing_period()

    if request.method == 'POST':
        form_data = request.POST.copy()
        
        # actionを取得（これを追加）
        action = request.POST.get('action', 'draft')  # デフォルトは'draft'

        # 🔥 デバッグログ追加（2026-01-11）🔥
        import logging
        debug_logger = logging.getLogger(__name__)
        debug_logger.info(f'🔥 祭り小説POST: action={action}, novel_id={novel_id}')

        # ここで先にformを定義
        if novel and novel.status == 'published':
            form_data['status'] = 'published'
            form = MaturiNovelForm(form_data, instance=novel)
        else:
            form = MaturiNovelForm(form_data, instance=novel, is_writing_period=is_writing_period)
        
        # 頭文字のふりがなのチェック
        if not form_data.get('initial', '').strip():
            messages.error(request, '🚨 【公開できません】タイトルの頭文字のふりがなを選択してください！頭文字がないと公開ボタンが効きません。')
            context = {
                'form': form,
                'novel': novel,
                'edit': novel_id is not None,
                'is_writing_period': is_writing_period,
                'current_game': current_game,
                'game': current_game,
                'can_publish': current_game and current_game.can_publish_novel()
            }
            return render(request, 'game_maturi/post_or_edit_maturi_novel.html', context)

        # 🔥 デバッグログ追加（2026-01-11）- フォームバリデーション確認 🔥
        debug_logger.info(f'🔥 フォームバリデーション: is_valid={form.is_valid()}')
        if not form.is_valid():
            debug_logger.error(f'🔥 フォームエラー: {form.errors}')

        if form.is_valid():
            saved_novel = form.save(commit=False)

            # 祭り作家取得または作成
            try:
                maturi_writer = User.objects.get(nickname='祭り作家')
            except User.DoesNotExist:
                # 祭り作家が存在しない場合は作成
                maturi_writer, _ = User.objects.get_or_create(
                    username='maturi_writer',
                    defaults={
                        'nickname': '祭り作家',
                        'email': 'maturi@example.com',
                        'user_type': User.MATURI_WRITER,
                        'is_active': True,
                        'email_confirmed': True
                    }
                )
                maturi_writer.set_unusable_password()
                maturi_writer.save()
            
            # 以降は既存のユーザー
            if not saved_novel.author:
                saved_novel.author = maturi_writer
                saved_novel.original_author = request.user
            else:
                saved_novel.author = maturi_writer
                if not saved_novel.original_author:
                    saved_novel.original_author = request.user
            
            # アクションに応じてステータスを設定
            if action == 'schedule_publish':
                saved_novel.scheduled_at = current_game.novel_publish_start_date
                saved_novel.scheduled_publish_date = current_game.prediction_start_date
                saved_novel.status = 'scheduled'
                saved_novel.save()
                messages.success(request, f'小説を予約公開しました。{current_game.prediction_start_date.strftime("%Y年%m月%d日")}に自動的に公開されます。')
                return redirect('accounts:view_profile')
            elif action in ['publish', 'edit_published']:
                saved_novel.status = 'published'
            elif action == 'edit_scheduled':
                # 🔥 予約公開の編集保存（2026-01-11バグ修正）
                # ステータスはscheduledのまま維持
                saved_novel.status = 'scheduled'
            elif action in ['draft', 'rest']:
                saved_novel.status = 'draft'
            elif action == 'cancel_schedule':  # 予約公開取り消しの処理を追加
                saved_novel.status = 'draft'  # ステータスを下書きに戻す
                messages.success(request, '予約公開を取り消しました。')
            
            saved_novel.save()

            # 祭りゲームとの関連付け（🔥 執筆期間中も対応 - 2026-01-11バグ修正）
            # find_current_game() は祭り本番期間のみなので、執筆期間中は None になる
            # find_active_game_for_writing() で執筆期間中の祭りも取得できるようにした
            active_game = MaturiGame.find_active_game_for_writing()
            if active_game and not active_game.maturi_novels.filter(id=saved_novel.id).exists():
                active_game.maturi_novels.add(saved_novel)
                active_game.save()

            # 削除アクションの処理を修正
            if action == 'delete':
                if novel:
                    # 現在のゲームを取得
                    current_game = MaturiGame.find_current_game()
                    if current_game:
                        # 祭りゲームから小説を削除
                        current_game.maturi_novels.remove(novel)
                    
                    # 2. この小説に関連する全ての予想を削除
                    GamePrediction.objects.filter(novel=novel).delete()
                    
                    # 3. 小説自体を削除
                    novel.delete()
                    messages.success(request, '小説を削除しました。')
                    return redirect('accounts:view_profile')

            # リダイレクト処理
            if action == 'rest':
                messages.success(request, '小説を保存して休憩します。')
                return redirect('accounts:view_profile')
            elif action in ['draft', 'edit_scheduled', 'edit_published']:
                # 🔥 編集保存後は同じ編集ページにリダイレクト（プレビュー反映のため）
                messages.success(request, '小説が保存されました！')
                return redirect('game_maturi:post_or_edit_maturi_novel', novel_id=saved_novel.id)
            else:
                messages.success(request, '小説が保存されました！')
                return redirect('novels:novel_detail', novel_id=saved_novel.id)
        else:
            # form.is_valid()がFalseの時のエラー表示
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'祭り小説フォームエラー: {form.errors}')
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')

    else:
        form = MaturiNovelForm(instance=novel, is_writing_period=is_writing_period)

    context = {
        'form': form,
        'novel': novel,
        'edit': novel_id is not None,
        'is_writing_period': is_writing_period,
        'current_game': current_game,
        'game': current_game,
        'can_publish': current_game and current_game.can_publish_novel()
    }
    
    return render(request, 'game_maturi/post_or_edit_maturi_novel.html', context)

@csrf_exempt
@login_required
def auto_save_maturi_novel(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            title = data.get('title', '')
            content = data.get('content', '')
            novel_id = data.get('novel_id')
            genre = data.get('genre', '未分類')  # ジャンルをJSONから取得（デフォルトは未分類）
            initial = data.get('initial', '')  # 🔥 頭文字のふりがなを追加（2026-01-11バグ修正）

            # 祭り作家を取得
            maturi_writer = User.objects.get(nickname='祭り作家')

            if novel_id:
                # 既存の小説を更新
                novel = Novel.objects.get(id=novel_id)
                novel.title = title
                novel.content = content
                novel.genre = genre  # 選択されたジャンルを保存
                novel.initial = initial  # 🔥 頭文字のふりがなを保存（2026-01-11バグ修正）
                novel.author = maturi_writer  # 祭り作家として保存
                novel.save()
            else:
                # 新規小説を作成
                novel = Novel.objects.create(
                    title=title,
                    content=content,
                    author=maturi_writer,  # 祭り作家として保存
                    original_author=request.user,  # 実際の作者は別フィールドに保存
                    genre=genre,  # 選択されたジャンルを保存
                    initial=initial  # 🔥 頭文字のふりがなを保存（2026-01-11バグ修正）
                )
            
            return JsonResponse({
                'status': 'success',
                'novel_id': novel.id
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

@csrf_exempt
@login_required
def check_maturi_writing_eligibility(request):
    today = timezone.localtime(timezone.now()).date()
    
    active_games = MaturiGame.objects.filter(
        start_date__lte=today,
        end_date__gte=today,
        participants__in=[request.user]
    )
    
    if active_games.exists():
        game = active_games.first()
        game_id = game.id
    else:
        game_id = None

    context = {
        'game_id': game_id,
        'current_game': game,  # 既存のgameオブジェトを使用
    }
    return render(request, 'game_maturi/game_maturi_top.html', context)

# ロガー設定
logger = logging.getLogger(__name__)

# 既存のコード...
# @freeze_time("2024-12-20")
@login_required
def entry_action(request, game_id):
    # 既存のコードをチェック
    if not request.user.is_authenticated:  # 念のための追加チェック
        messages.error(request, '祭りにエントリーするには、ログインが必要です。')
        return redirect('accounts:login')  # ログインページにリダイレクト
    
    game = get_object_or_404(MaturiGame, pk=game_id)
    user_entered = game.is_user_entered(request.user)
    
    # デバッグ出力を追加
    now = timezone.localtime(timezone.now())  # 🔥 JST時間取得
    logger.debug(f"=== Entry Period Debug ===")
    logger.debug(f"Current time: {now}")
    logger.debug(f"Entry period: {game.entry_start_date} to {game.entry_end_date}")
    logger.debug(f"Is entry period: {game.is_entry_period()}")
    
    context = {
        'game': game,
        'user_entered': user_entered
    }
    if not game.is_entry_period():
        messages.error(request, 'エンリー期間ではありません。')
        logger.debug("Not in entry period")
        return redirect('game_maturi:game_maturi_top', game_id=game_id)
    elif game.is_user_entered(request.user):
        messages.error(request, 'すでにエントリーしていす。')
        logger.debug("User already entered")
        return redirect('game_maturi:game_maturi_top', game_id=game_id)
    else:
        if request.method == 'POST':
            game.entrants.add(request.user)
            messages.success(request, 'エントリーが完了しまた')
            logger.debug("Entry successful")
            return redirect('game_maturi:game_maturi_top', game_id=game_id)
        else:
            logger.debug("GET request on entry action")
            return redirect('game_maturi:game_maturi_top', game_id=game_id)

@require_http_methods(["POST"])
@login_required
@csrf_exempt
def submit_prediction(request):
    try:
        # POSTデータをJSONとしてパース
        data = json.loads(request.body)
        predictions = data.get('predictions', {})
        game_id = data.get('game_id')
        game = get_object_or_404(MaturiGame, id=game_id)

        # 予想期間のチェック
        if not game.is_prediction_period():
            return JsonResponse({
                'success': False,
                'message': '予想期間外です。'
            }, status=400)

        # 既存の予想を取得
        existing_predictions = GamePrediction.objects.filter(
            maturi_game=game,
            predictor=request.user
        )

        for novel_id, author_id in predictions.items():
            if author_id == '':  # 予想取り消しの場合
                # 既存の予想を削除
                GamePrediction.objects.filter(
                    novel_id=novel_id,
                    predictor=request.user,
                    maturi_game=game
                ).delete()
            else:
                # 予想を更新または作成
                GamePrediction.objects.update_or_create(
                    novel_id=novel_id,
                    predictor=request.user,
                    maturi_game=game,
                    defaults={'predicted_author_id': author_id}
                )

        return JsonResponse({
            'success': True,
            'message': '予想を保存しました'
        })

    except Exception as e:
        logger.error(f"予想処理エラー: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)

# @freeze_time("2024-12-20")  # 12月16日に固定
def prediction_period_finished_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # 現在のゲームを探す
        now = timezone.localtime(timezone.now())  # 🔥 JST時間取得
        current_game = MaturiGame.objects.filter(
            maturi_end_date__gte=now.date()  # 🔥 JST日付で比較
        ).order_by('maturi_start_date').first()

        if not current_game:
            # 終了した最新の祭りを取得
            current_game = MaturiGame.objects.filter(
                maturi_end_date__lt=now.date()  # 🔥 JST日付で比較
            ).order_by('-maturi_end_date').first()
        
        if not current_game:
            messages.warning(request, '祭りが見つかりません。')
            return redirect('game_maturi:game_maturi_top', game_id=current_game.id)
            
        if not current_game.is_prediction_period_finished():
            messages.warning(request, '予想期間が終了するまで結果は表示できません。')
            return redirect('game_maturi:game_maturi_top', game_id=current_game.id)
            
        return view_func(request, *args, **kwargs)
    return _wrapped_view

@login_required
@prediction_period_finished_required
def prediction_result(request, user_id):
    predictor = get_object_or_404(User, id=user_id)
    
    # 現在のゲームを探す（デコータと同じロジック）
    now = timezone.localtime(timezone.now())  # 🔥 JST時間取得
    current_game = MaturiGame.objects.filter(
        maturi_end_date__gte=now.date()  # 🔥 JST日付で比較
    ).order_by('maturi_start_date').first()

    if not current_game:
        current_game = MaturiGame.objects.filter(
            maturi_end_date__lt=now.date()  # 🔥 JST日付で比較
        ).order_by('-maturi_end_date').first()

    if not current_game:
        messages.warning(request, '祭りが見つかりません。')
        return redirect('home')  # homeページにリダイレクト

    # 以下は既存のコード
    predictions = GamePrediction.objects.filter(
        predictor=predictor,
        maturi_game=current_game
    ).select_related(
        'novel', 
        'novel__original_author', 
        'predicted_author'
    ).order_by('novel__title')

    total_predictions = predictions.count()
    correct_predictions = sum(1 for p in predictions 
                            if p.predicted_author_id == p.novel.original_author_id)
    
    accuracy = (correct_predictions / total_predictions * 100) if total_predictions > 0 else 0

    context = {
        'predictor': predictor,
        'predictions': predictions,
        'total_predictions': total_predictions,
        'correct_predictions': correct_predictions,
        'accuracy': accuracy,
        'current_game': current_game,
        'game': current_game,  # テンプレートで使用するgame変数を追加
    }
    
    return render(request, 'game_maturi/includes/prediction_result.html', context)

@login_required
@prediction_period_finished_required
def game_results(request, game_id):
    current_game = get_object_or_404(MaturiGame, id=game_id)
    
    # 全ての予想を取得
    all_predictions = GamePrediction.objects.filter(
        maturi_game_id=game_id
    ).select_related(
        'predictor',
        'predicted_author',
        'novel',
        'novel__original_author'
    )

    # グインユーザーの予想を取得
    novel_predictions = {}
    predictor_stats = {}
    if request.user.is_authenticated:
        user_predictions = all_predictions.filter(predictor=request.user)
        
        # 予想情報をnovel_idをキーにして格納
        for pred in user_predictions:
            novel_predictions[str(pred.novel.id)] = pred

        # ユーザーの統計情報を計算
        total = user_predictions.count()
        correct = sum(1 for p in user_predictions 
                     if p.predicted_author_id == p.novel.original_author_id)

        predictor_stats[request.user] = {
            'total': total,
            'correct': correct,
            'accuracy': (correct / total * 100) if total > 0 else 0
        }

    # 作品ごとの正解率を計算
    novel_stats = {}
    novels = current_game.published_novels.all()

    for novel in novels:
        # この作品に対する全予想を取得
        novel_preds = all_predictions.filter(novel=novel)
        total = novel_preds.count()
        correct = novel_preds.filter(
            predicted_author_id=F('novel__original_author_id')
        ).count()

        novel_stats[novel.id] = {
            'total': total,
            'correct': correct,
            'fraction': f"{correct}/{total}" if total > 0 else "0/0"
        }

    context = {
        'current_game': current_game,
        'predictor_stats': predictor_stats,
        'novels': current_game.published_novels.all(),
        'novel_predictions': novel_predictions,  # ユーザーの予想情報（616行目で初期化したもの）
        'all_predictions': all_predictions,
        'novel_stats': novel_stats,
    }
    
    return render(request, 'game_maturi/includes/game_results.html', context)

def maturi_list(request):
    """祭り一覧を表示するビュー"""
    now = timezone.localtime(timezone.now()).date()  # 🔥 JST日付取得

    # 過去の祭り開始日の降順）
    past_games = MaturiGame.objects.filter(
        maturi_end_date__lt=now,
        maturi_end_date__isnull=False
    ).order_by('-maturi_start_date')

    # 現在開催中の祭り（開始日の降順）
    current_games = MaturiGame.objects.filter(
        maturi_start_date__lte=now,
        maturi_end_date__gte=now
    ).order_by('-maturi_start_date')

    # 開催予定の祭り（開始日の降順）
    upcoming_games = MaturiGame.objects.filter(
        maturi_start_date__gt=now,
        maturi_start_date__isnull=False
    ).order_by('-maturi_start_date')

    context = {
        'current_games': current_games,
        'upcoming_games': upcoming_games,
        'past_games': past_games,
    }
    
    return render(request, 'game_maturi/maturi_list.html', context)

# def game_maturi_detail(request, game_id):
#     game = get_object_or_404(MaturiGame, pk=game_id)
#     print(f"\n=== Game Detail Debug ===")
#     print(f"Game ID: {game_id}")
#     print(f"User ID: {request.user.id if request.user.is_authenticated else 'Not logged in'}")

#     # contextの初期化
#     context = {
#         'game': game,
#         'request': request,  # テンプレートでリクエスト情報を使用するため
#     }

#     # 公開済みの小説を取得
#     novels = Novel.objects.filter(
#         maturi_games=game,
#         status='published'
#     ).select_related('original_author')
#     print(f"公開済み小説数: {novels.count()}")

#     # 参加者を取得
#     active_authors = game.entrants.all()

#     # 全ての予想を取得（変数名変更なし - これは他では使われていない）
#     all_predictions = GamePrediction.objects.filter(
#         maturi_game=game
#     ).select_related(
#         'predictor',
#         'predicted_author',
#         'novel',
#         'novel__original_author'
#     )

#     # ユーザーの予想を取得（変数名を変更）
#     current_user_predictions = []  # user_predictions → current_user_predictions
#     if request.user.is_authenticated:
#         current_user_predictions = all_predictions.filter(predictor=request.user)

#     # 作品ごとの正解率を計算
#     novel_stats = {}
#     for novel in novels:
#         print(f"Processing novel {novel.id}: {novel.title}")  # デバッグ出力
        
#         # この作品に対する全予想を取得
#         novel_predictions = all_predictions.filter(novel=novel)  # ここを修正：predictions -> all_predictions
#         total = novel_predictions.count()
        
#         # 正解数をカウント（クエリを最適化）
#         correct = novel_predictions.filter(
#             predicted_author_id=F('novel__original_author_id')
#         ).count()
        
#         print(f"Novel {novel.id}: {total} predictions, {correct} correct")  # デバッグ出力
        
#         # 結果を保存
#         novel_stats[novel.id] = {
#             'total': total,
#             'correct': correct,
#             'fraction': f"{correct}/{total}" if total > 0 else "0/0"
#         }

#     # 正解率で降順ソート
#     participants_stats.sort(key=lambda x: (-x[1]['accuracy'], -x[1]['correct']))

    # ユーザーの予想情報を取得
    # correct_predictions = 0
    # accuracy = 0
    # novel_predictions = {}

    # # 全ての小説のIDをキーとして、デフォルト値を設定
    # for novel in novels:
    #     novel_predictions[novel.id] = {
    #         'predicted_author': None,
    #         'is_correct': False
    #     }

    # if request.user.is_authenticated:
    #     user_predictions = all_predictions.filter(predictor=request.user)
        
    #     print(f"\n=== Novel Predictions Debug ===")
    #     print(f"User predictions count: {user_predictions.count()}")
        
    #     # 予想情報をnovel_idをキーにして格納
    #     for pred in user_predictions:
    #         print(f"Processing prediction for novel {pred.novel.id}")
    #         novel_predictions[pred.novel.id] = {
    #             'predicted_author': pred.predicted_author,
    #             'is_correct': pred.predicted_author_id == pred.novel.original_author_id
    #         }
        
    #     print(f"Final novel_predictions keys: {list(novel_predictions.keys())}")

    #     # 正解数を計算
    #     correct_predictions = sum(1 for p in user_predictions 
    #                             if p.predicted_author_id == p.novel.original_author_id)
        
    #     # 正解率を計算（分母は全小説数）
    #     total_novels = novels.count()
    #     accuracy = (correct_predictions / total_novels * 100) if total_novels > 0 else 0

    #     print(f"\nデバッグ出力:")
    #     print(f"全小説数: {total_novels}")
    #     print(f"正解数: {correct_predictions}")
    #     print(f"正解率: {accuracy}%")

    # # 最後に了したゲームを取得（これを追加）
    # now = timezone.now()
    # last_finished_game = MaturiGame.objects.filter(
    #     maturi_end_date__lt=now
    # ).order_by('-maturi_end_date').first()
    
    # # ユーザーがゲームに参加しているかチェック（これを追加）
    # is_user_entered = False
    # if request.user.is_authenticated:
    #     is_user_entered = game.entrants.filter(id=request.user.id).exists()

    # # contextを更新する前にデバッグ出力を追加
    # print("\n=== Context Debug ===")
    # print(f"novels count: {novels.count()}")
    # print(f"novel_predictions keys: {list(novel_predictions.keys())}")
    # print(f"current_user_predictions count: {len(current_user_predictions)}")
    # print(f"all_predictions count: {all_predictions.count()}")

    # # contextを更新
    # context.update({
    #     'novel_stats': novel_stats,
    #     'correct_predictions': sum(1 for p in all_predictions if p.predicted_author_id == p.novel.original_author_id),
    #     'accuracy': (sum(1 for p in all_predictions if p.predicted_author_id == p.novel.original_author_id) / all_predictions.count() * 100) if all_predictions.count() > 0 else 0,
    #     'novels': novels,
    #     'participants': participants_stats,
    #     'all_predictions': all_predictions,
    #     'predictions': current_user_predictions,
    #     'novel_predictions': novel_predictions,
    #     'total_predictions': all_predictions.count(),
    #     'last_finished_game': last_finished_game,  # これを追加
    #     'is_user_entered': is_user_entered,  # これを追加
    # })

    return render(request, 'game_maturi/game_maturi_top.html', context)

# 進捗計算用の関数
# @freeze_time("2024-12-20")  # 12月16日に固定
def calculate_progress(game, today):
    start_date = game.maturi_start_date
    end_date = game.maturi_end_date
    total_days = (end_date - start_date).days
    days_passed = (today - start_date).days
    
    if days_passed < 0:
        return 0
    elif days_passed > total_days:
        return 100
    else:
        return min(max(int((days_passed / total_days) * 100), 0), 100)

# 予想結果追加用の関数
# @freeze_time("2024-12-20")  # 12月16日に固定
def add_prediction_results_to_context(current_game, context):
    # 最後に終了したゲームを取得
    now = timezone.localtime(timezone.now())  # 🔥 JST時間取得
    last_finished_game = MaturiGame.objects.filter(
        maturi_end_date__lt=now.date()  # 🔥 JST日付で比較
    ).order_by('-maturi_end_date').first()
    
    # ユーザーがゲームに参加しているかチェック
    is_user_entered = False
    if hasattr(context['request'], 'user') and context['request'].user.is_authenticated:
        is_user_entered = current_game.entrants.filter(id=context['request'].user.id).exists()
    
    all_predictions = GamePrediction.objects.filter(
        maturi_game=current_game
    ).select_related('predictor', 'predicted_author', 'novel__original_author')

    # ユーザーの予想情報を取得して追加（これを追加！）
    novel_predictions = {}
    if hasattr(context['request'], 'user') and context['request'].user.is_authenticated:
        user_predictions = all_predictions.filter(predictor=context['request'].user)
        for pred in user_predictions:
            novel_predictions[pred.novel.id] = {
                'predicted_author': pred.predicted_author,
                'is_correct': pred.predicted_author_id == pred.novel.original_author_id
            }

    # 予想者の統計情報を計算
    predictor_stats = {}
    for prediction in all_predictions:
        predictor = prediction.predictor
        if predictor not in predictor_stats:
            predictor_predictions = all_predictions.filter(predictor=predictor)
            total = predictor_predictions.count()
            correct = sum(1 for p in predictor_predictions 
                        if p.predicted_author_id == p.novel.original_author_id)
            
            predictor_stats[predictor] = {
                'total': total,
                'correct': correct,
                'accuracy': (correct / total * 100) if total > 0 else 0
            }

    context.update({
        'predictor_stats': predictor_stats,
        'all_predictions': all_predictions,
        'show_results': True,  # 結果表示フラグを追加
        'last_finished_game': last_finished_game,
        'is_user_entered': is_user_entered,
        'novel_predictions': novel_predictions,  # これを追加！
    })


@require_http_methods(["POST"])
def predict_author(request):
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'message': '作者予想をするには、ログインが必要です。'
        }, status=403)
        
    try:
        data = json.loads(request.body)
        novel_id = data.get('novel_id')
        author_id = data.get('author_id')

        # 祭りゲーム取得
        novel = get_object_or_404(Novel, id=novel_id)
        maturi_game = novel.maturi_games.first()
        
        if not maturi_game:
            raise ValueError("小説に関連する祭りが見つかりません")

        # エントリーチェックを削除
        
        # 予想を保存
        prediction, created = GamePrediction.objects.update_or_create(
            novel_id=novel_id,
            predictor=request.user,
            maturi_game=maturi_game,
            defaults={'predicted_author_id': author_id}
        )

        return JsonResponse({
            'success': True,
            'message': '予想を保存しました'
        })

    except Exception as e:
        logger.error(f"予想処理エラー: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)

@require_http_methods(["POST"])
def cancel_prediction(request):
    try:
        data = json.loads(request.body)
        novel_id = data.get('novel_id')
        
        # 予想を取得して削除
        prediction = GamePrediction.objects.filter(
            predictor=request.user,
            novel_id=novel_id
        ).first()
        
        if prediction:
            prediction.delete()
            return JsonResponse({
                'success': True,
                'message': '予想を取り消しました'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': '予想が見つかりません'
            }, status=404)
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)



# # ユーザーの成績用
# def get_game_detail(request, game_id):
#     game = get_object_or_404(MaturiGame, pk=game_id)
#     print(f"\n=== Game Detail Debug ===")
#     print(f"Game ID: {game_id}")
#     print(f"User ID: {request.user.id if request.user.is_authenticated else 'Not logged in'}")
    
#     novels = game.novels.filter(status='published')
#     print(f"公開済み小説数: {novels.count()}")
    
#     # 予想データを一括取得
#     predictions = GamePrediction.objects.filter(
#         maturi_game=game
#     ).select_related(
#         'novel',
#         'novel__original_author',
#         'predictor',
#         'predicted_author'
#     )
    
#     # novel_predictionsの処理を game_maturi_detail と同じように
#     novel_predictions = {}
#     if request.user.is_authenticated:
#         user_predictions = predictions.filter(predictor=request.user)
        
#         # 予想情報をnovel_idをキーにして格納
#         for pred in user_predictions:
#             novel_predictions[pred.novel.id] = {
#                 'predicted_author': pred.predicted_author,
#                 'is_correct': pred.predicted_author_id == pred.novel.original_author_id
#             }
#             print(f"Novel ID: {pred.novel.id}, Predicted Author: {pred.predicted_author.nickname}")

#     # 作品ごとの正解率を計算
#     novel_stats = {}
#     for novel in novels:
#         novel_predictions_list = [p for p in predictions if p.novel_id == novel.id]
#         total = len(novel_predictions_list)
#         correct = sum(1 for p in novel_predictions_list if p.is_correct())
        
#         novel_stats[novel.id] = {
#             'total': total,
#             'correct': correct,
#             'fraction': f"{correct}/{total}" if total > 0 else "0/0",
#             'accuracy': (correct / total * 100) if total > 0 else 0
#         }
#         print(f"小説 {novel.title} の統計: {novel_stats[novel.id]}")

#     context = {
#         'game': game,
#         'novels': novels,
#         'novel_predictions': novel_predictions,
#         'novel_stats': novel_stats,
#         'all_predictions': predictions,
#     }
    
#     print("\n=== Context Debug ===")
#     print(f"Novels count: {len(novels)}")
#     print(f"Novel predictions count: {len(novel_predictions)}")
#     print(f"Novel stats count: {len(novel_stats)}")
    
#     return render(request, 'game_maturi/game_detail.html', context)

