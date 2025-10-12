"""
同タイトルイベント通知機能

メール通知の送信を管理
"""
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


def get_unsubscribe_url(user):
    """
    配信停止URL生成
    ユーザーごとの配信停止リンクを生成
    """
    # 配信停止ページのURLを生成（実装は後で）
    return f"{settings.BASE_URL}/accounts/unsubscribe/{user.id}/"


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

    for user in users:
        try:
            subject = f'【SSS4】{current_month}の同タイトルイベント募集開始！'
            unsubscribe_url = get_unsubscribe_url(user)

            message = f"""
{user.nickname} 様

こんにちは！SSS4運営チームです。

{current_month}の同タイトルイベントが始まりました！
今月も面白いタイトル提案をお待ちしています。

◆ タイトル提案はこちら
{settings.BASE_URL}/game_same_title/proposals/create/

◆ 同タイトルイベントページ
{settings.BASE_URL}/game_same_title/same_title/

誰でも自由に参加できます。
あなたの創作をお待ちしています！

---
このメールの配信を停止する場合は、以下のリンクをクリックしてください。
{unsubscribe_url}

SSS4運営チーム
            """.strip()

            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            sent_count += 1
            logger.info(f'同タイトル募集通知送信成功: {user.email}')

        except Exception as e:
            logger.error(f'同タイトル募集通知送信失敗: {user.email} - {str(e)}')
            continue

    logger.info(f'同タイトル募集通知送信完了: {sent_count}件')
    return sent_count


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

    for user in users:
        try:
            subject = f'【SSS4】新しいタイトル提案「{proposal.title}」が追加されました'
            unsubscribe_url = get_unsubscribe_url(user)

            message = f"""
{user.nickname} 様

こんにちは！SSS4運営チームです。

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

SSS4運営チーム
            """.strip()

            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            sent_count += 1
            logger.info(f'同タイトル提案通知送信成功: {user.email}')

        except Exception as e:
            logger.error(f'同タイトル提案通知送信失敗: {user.email} - {str(e)}')
            continue

    logger.info(f'同タイトル提案通知送信完了: {sent_count}件')
    return sent_count


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

    for user in users:
        try:
            subject = f'【SSS4】{current_month}の同タイトル一番槍が決定！'
            unsubscribe_url = get_unsubscribe_url(user)

            message = f"""
{user.nickname} 様

こんにちは！SSS4運営チームです。

{current_month}の同タイトルイベント、一番槍が決定しました！

◆ 今月のタイトル
「{novel.title}」

一番槍: {novel.author.nickname}

◆ 作品を読む
{settings.BASE_URL}/novels/{novel.id}/

◆ 俺もこのタイトルで作る
{settings.BASE_URL}/novels/post/?title={novel.title}

あなたも同じタイトルで創作に挑戦してみませんか？

---
このメールの配信を停止する場合は、以下のリンクをクリックしてください。
{unsubscribe_url}

SSS4運営チーム
            """.strip()

            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            sent_count += 1
            logger.info(f'同タイトル決定通知送信成功: {user.email}')

        except Exception as e:
            logger.error(f'同タイトル決定通知送信失敗: {user.email} - {str(e)}')
            continue

    logger.info(f'同タイトル決定通知送信完了: {sent_count}件')
    return sent_count
