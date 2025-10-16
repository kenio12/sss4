"""
同タイトルイベント通知機能

メール通知の送信を管理
"""
from django.core.mail import send_mail, get_connection
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core import signing
from urllib.parse import quote
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


def get_unsubscribe_url(user):
    """
    配信停止URL生成
    署名付きトークンでセキュアな配信停止リンクを生成
    """
    # 署名付きトークン生成（24時間有効）
    token = signing.dumps(user.id, salt='email_unsubscribe')
    return f"{settings.BASE_URL}/accounts/unsubscribe/{token}/"


def send_same_title_recruitment_notification():
    """
    同タイトル募集通知（月初・1日）
    全会員に同タイトルイベント募集のメールを送信
    """
    # 通知設定が有効なユーザーを取得
    users = User.objects.filter(
        notification_settings__same_title_recruitment=True,
        is_active=True,
        email_confirmed=True
    ).select_related('notification_settings')

    if not users.exists():
        logger.info('同タイトル募集通知: 送信対象ユーザーなし')
        return 0

    sent_count = 0
    current_month = timezone.now().strftime('%Y年%m月')

    # メール送信接続を再利用（効率化）
    connection = get_connection()
    connection.open()

    try:
        for user in users:
            try:
                subject = f'【超短編小説会】{current_month}の同タイトルイベントのタイトル募集！'
                unsubscribe_url = get_unsubscribe_url(user)

                message = f"""
{user.nickname} 様

こんにちは！超短編小説会です。

{current_month}の同タイトルイベントが始まりました！
タイトルの提案をお待ちしています！

◆ タイトル提案はこちら
{settings.BASE_URL}/game_same_title/proposals/create/

◆ 同タイトルイベントページ
{settings.BASE_URL}/game_same_title/same_title/

あなたが提案されたタイトルが小説のタイトルになるかも？！

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
                # 個人情報保護: メールアドレスをマスキング
                masked_email = user.email[:3] + '***'
                logger.debug(f'同タイトル募集通知送信成功: {masked_email}')

            except Exception as e:
                masked_email = user.email[:3] + '***'
                logger.error(f'同タイトル募集通知送信失敗: {masked_email} - {str(e)}')
                continue

        logger.info(f'同タイトル募集通知送信完了: {sent_count}件')
        return sent_count

    finally:
        connection.close()


def send_same_title_proposal_notification(proposal):
    """
    同タイトル提案通知
    タイトル提案時に全会員へ通知
    """
    # 通知設定が有効なユーザーを取得（提案者自身を除く）
    users = User.objects.filter(
        notification_settings__same_title_proposal=True,
        is_active=True,
        email_confirmed=True
    ).exclude(id=proposal.proposer.id).select_related('notification_settings')

    if not users.exists():
        logger.info('同タイトル提案通知: 送信対象ユーザーなし')
        return 0

    sent_count = 0
    current_month = proposal.proposal_month.strftime('%Y年%m月')

    # メール送信接続を再利用（効率化）
    connection = get_connection()
    connection.open()

    try:
        for user in users:
            try:
                subject = f'【超短編小説会】新しいタイトル提案「{proposal.title}」が追加されました'
                unsubscribe_url = get_unsubscribe_url(user)

                message = f"""
{user.nickname} 様

こんにちは！超短編小説会です。

{current_month}の同タイトルイベントに新しいタイトル提案が追加されました。

◆ 提案されたタイトル
「{proposal.title}」

提案者: {proposal.proposer.nickname}

◆ 同タイトルイベントページ
{settings.BASE_URL}/game_same_title/same_title/

あなたもこのタイトルで作品を投稿してみませんか？

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
                # 個人情報保護: メールアドレスをマスキング
                masked_email = user.email[:3] + '***'
                logger.debug(f'同タイトル提案通知送信成功: {masked_email}')

            except Exception as e:
                masked_email = user.email[:3] + '***'
                logger.error(f'同タイトル提案通知送信失敗: {masked_email} - {str(e)}')
                continue

        logger.info(f'同タイトル提案通知送信完了: {sent_count}件')
        return sent_count

    finally:
        connection.close()


def send_same_title_decision_notification(novel):
    """
    同タイトル決定通知（月の最初の投稿時）
    今月の一番槍（最初の投稿）を全会員に通知
    """
    # 通知設定が有効なユーザーを取得（投稿者自身を除く）
    users = User.objects.filter(
        notification_settings__same_title_decision=True,
        is_active=True,
        email_confirmed=True
    ).exclude(id=novel.author.id).select_related('notification_settings')

    if not users.exists():
        logger.info('同タイトル決定通知: 送信対象ユーザーなし')
        return 0

    sent_count = 0
    current_month = timezone.now().strftime('%Y年%m月')

    # メール送信接続を再利用（効率化）
    connection = get_connection()
    connection.open()

    try:
        for user in users:
            try:
                subject = f'【超短編小説会】{current_month}の同タイトル一番槍が決定！'
                unsubscribe_url = get_unsubscribe_url(user)
                # タイトルをURLエンコード（日本語・スペース対応）
                encoded_title = quote(novel.title, safe='')

                message = f"""
{user.nickname} 様

こんにちは！超短編小説会です。

{current_month}の同タイトルイベント、一番槍が決定しました！

◆ 今月のタイトル
「{novel.title}」

一番槍: {novel.author.nickname}

◆ 作品を読む
{settings.BASE_URL}/novels/{novel.id}/

◆ 俺もこのタイトルで作る
{settings.BASE_URL}/novels/post/?title={encoded_title}

あなたも同じタイトルで創作に挑戦してみませんか？

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
                # 個人情報保護: メールアドレスをマスキング
                masked_email = user.email[:3] + '***'
                logger.debug(f'同タイトル決定通知送信成功: {masked_email}')

            except Exception as e:
                masked_email = user.email[:3] + '***'
                logger.error(f'同タイトル決定通知送信失敗: {masked_email} - {str(e)}')
                continue

        logger.info(f'同タイトル決定通知送信完了: {sent_count}件')
        return sent_count

    finally:
        connection.close()


def send_same_title_follower_praise_notification(novel, rank):
    """
    同タイトル追随投稿讃え通知（3・5・7番目専用）
    同タイトルで3番目・5番目・7番目に投稿した人を讃える
    """
    # 投稿者本人にのみ送信
    user = novel.author

    # email_confirmedチェック
    if not user.email_confirmed or not user.is_active:
        logger.info(f'同タイトル追随讃え通知: ユーザー{user.nickname}はemail_confirmed=Falseまたはis_active=False')
        return 0

    current_month = timezone.now().strftime('%Y年%m月')

    try:
        subject = f'【超短編小説会】あなたは{rank}番目に「{novel.title}」に挑戦されました！'
        unsubscribe_url = get_unsubscribe_url(user)

        # 一番槍の作品を取得
        first_novel = novel.__class__.objects.filter(
            title=novel.title,
            created_at__month=novel.created_at.month,
            created_at__year=novel.created_at.year,
            is_public=True
        ).order_by('created_at').first()

        message = f"""
{user.nickname} 様

こんにちは！超短編小説会です。

あなたは{rank}番目に「{novel.title}」での小説に挑戦し、そして投稿されました！
素晴らしい挑戦、ありがとうございます！

◆ あなたの作品を読む
{settings.BASE_URL}/novels/{novel.id}/

◆ 一番槍の作品を読む
{settings.BASE_URL}/novels/{first_novel.id}/

◆ 同タイトル作品一覧
{settings.BASE_URL}/game_same_title/same_title/

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
        )

        masked_email = user.email[:3] + '***'
        logger.info(f'同タイトル追随讃え通知送信成功: {masked_email} ({rank}番目)')
        return 1

    except Exception as e:
        masked_email = user.email[:3] + '***'
        logger.error(f'同タイトル追随讃え通知送信失敗: {masked_email} - {str(e)}')
        return 0
