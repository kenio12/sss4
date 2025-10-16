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
    # 🔥🔥🔥 通知設定が有効なユーザーを取得（投稿者本人を含む！）🔥🔥🔥
    users = User.objects.filter(
        notification_settings__same_title_decision=True,
        is_active=True,
        email_confirmed=True
    ).select_related('notification_settings')

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
    同タイトル追随投稿通知（2番目以降全員）
    投稿者本人への通知 + 全会員への通知の2つを送信
    """
    current_month = timezone.now().strftime('%Y年%m月')
    total_sent = 0

    # 一番槍の作品を取得
    first_novel = novel.__class__.objects.filter(
        title=novel.title,
        created_at__month=novel.created_at.month,
        created_at__year=novel.created_at.year,
        status='published'
    ).order_by('created_at').first()

    # タイトルをURLエンコード（日本語・スペース対応）
    encoded_title = quote(novel.title, safe='')

    # メール送信接続を再利用（効率化）
    connection = get_connection()
    connection.open()

    try:
        # 🔥🔥🔥 1. 投稿者本人への通知（何番目か伝える） 🔥🔥🔥
        user = novel.author
        if user.email_confirmed and user.is_active:
            try:
                subject = f'【超短編小説会】{current_month}の同タイトルの{rank}番煎じとして投稿されました！'
                unsubscribe_url = get_unsubscribe_url(user)

                message = f"""
{user.nickname} 様

こんにちは！超短編小説会です。

すでに{current_month}の同タイトルの一番槍は投稿されましたが、
その{rank}番煎じとして{user.nickname}さんが同タイトルとして投稿されました！

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
                    connection=connection,
                )

                masked_email = user.email[:3] + '***'
                logger.info(f'同タイトル追随通知（投稿者本人）送信成功: {masked_email} ({rank}番目)')
                total_sent += 1

            except Exception as e:
                masked_email = user.email[:3] + '***'
                logger.error(f'同タイトル追随通知（投稿者本人）送信失敗: {masked_email} - {str(e)}')

        # 🔥🔥🔥 2. 全会員への通知（投稿者本人を含む） 🔥🔥🔥
        users = User.objects.filter(
            notification_settings__same_title_follower=True,
            is_active=True,
            email_confirmed=True
        ).select_related('notification_settings')

        if users.exists():
            for recipient in users:
                try:
                    subject = f'【超短編小説会】{current_month}の同タイトルに{rank}番目の作品が投稿されました！'
                    unsubscribe_url = get_unsubscribe_url(recipient)

                    message = f"""
{recipient.nickname} 様

こんにちは！超短編小説会です。

{current_month}の同タイトルイベントに{rank}番目の作品が投稿されました！

◆ 今月のタイトル
「{novel.title}」

◆ {rank}番目の投稿者
{novel.author.nickname}

◆ {rank}番目の作品を読む
{settings.BASE_URL}/novels/{novel.id}/

◆ 一番槍の作品を読む
{settings.BASE_URL}/novels/{first_novel.id}/

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
                        [recipient.email],
                        fail_silently=False,
                        connection=connection,
                    )

                    masked_email = recipient.email[:3] + '***'
                    logger.debug(f'同タイトル追随通知（全会員）送信成功: {masked_email}')
                    total_sent += 1

                except Exception as e:
                    masked_email = recipient.email[:3] + '***'
                    logger.error(f'同タイトル追随通知（全会員）送信失敗: {masked_email} - {str(e)}')
                    continue

        logger.info(f'同タイトル追随通知送信完了: {total_sent}件（{rank}番目）')
        return total_sent

    finally:
        connection.close()
