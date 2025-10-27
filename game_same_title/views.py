from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from .models import TitleProposal
import logging
from novels.models import Novel
from .forms import NovelForm, CommentForm
from django.utils import timezone
from game_same_title.models import MonthlySameTitleInfo
from django.core import serializers

# ロガーの設定
logger = logging.getLogger(__name__)

from django.utils import timezone
from datetime import timedelta

# エントリー制廃止により check_entered_last_month 関数を削除

def get_next_month_str():
    next_month = (timezone.now() + relativedelta(months=+1)).month
    return f"{next_month}月"

from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from datetime import timedelta
from .models import Novel, MonthlySameTitleInfo, TitleProposal
import logging
import json

logger = logging.getLogger(__name__)

from django.core.paginator import Paginator
from django.http import JsonResponse
import json
from django.utils.dateformat import DateFormat

def same_title(request, page=1):
    # 🚧 工事中メッセージ表示（2025-10-14：改修完了により解除）
    # return render(request, 'game_same_title/under_construction.html', {
    #     'message': '現在、同タイトルは改修工事中です。お待ち願います。'
    # })

    current_month_date = timezone.now().date().replace(day=1)
    current_year = current_month_date.year
    current_month = current_month_date.month
    current_month_str = current_month_date.strftime('%Y-%m')

    # 現在月の同タイトル小説のみを取得し、published_dateの昇順で並び替え
    same_title_novels = Novel.objects.filter(
        is_same_title_game=True,
        published_date__year=current_year,
        published_date__month=current_month,
        status='published'
    ).order_by('published_date').select_related('author')  # 降順から昇順に変更

    # 提案者情報を取得
    title_proposals = {
        proposal.title: proposal.proposer.nickname 
        for proposal in TitleProposal.objects.filter(
            proposal_month__year=current_year,
            proposal_month__month=current_month
        ).select_related('proposer')
    }

    paginator = Paginator(same_title_novels, 10)
    page_obj = paginator.get_page(page)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        novels_list = [
            {
                'id': novel['id'],
                'title': novel['title'],
                'author_nickname': novel['author__nickname'],
                'published_date': DateFormat(novel['published_date']).format('Y-m-d H:i:s'),  # 日付を文字列に変換
                'word_count': novel['word_count'],
                'genre': novel['genre'],
                'author_id': novel['author_id']
            }
            for novel in page_obj.object_list.values(
                'id', 'title', 'author__nickname', 'published_date', 'word_count', 'genre', 'author_id'
            )
        ]
        response_data = {
            'novels': novels_list,
            'has_next': page_obj.has_next()
        }
        logger.debug(f"ひいいいいいいいいいいいいいいいいいいいいいいいいいいいいいいいいSending JSON response: {json.dumps(response_data)}")  # ログ出力
        return JsonResponse(response_data)

    decided_title_info = MonthlySameTitleInfo.objects.filter(month=current_month_str).first()
    if decided_title_info:
        decided_title = {
            'title': decided_title_info.title,
            'novel': decided_title_info.novel,
            'proposer_nickname': decided_title_info.proposer.nickname
        }
    else:
        decided_title = None

    # 🔥 前月のタイトル候補は全員に表示（ログイン不要）
    last_month = current_month_date - relativedelta(months=1)
    title_candidates = [
        {'title': candidate.title, 'proposer_nickname': candidate.proposer.nickname}
        for candidate in TitleProposal.objects.filter(proposal_month__year=last_month.year, proposal_month__month=last_month.month)
    ]

    if request.user.is_authenticated:
        proposer = request.user
        next_month_start = current_month_date + relativedelta(months=1)
        current_month_end = next_month_start - timedelta(seconds=1)

        existing_proposals = TitleProposal.objects.filter(
            proposer=proposer,
            proposed_at__gte=current_month_date,
            proposed_at__lt=current_month_end
        )
        # エントリー制廃止により削除: already_entered, entered_last_month, already_entered_users
    else:
        existing_proposals = []

    next_month = get_next_month_str()
    # エントリー制廃止により entry_success を削除

    return render(request, 'game_same_title/same_title.html', {
        'existing_proposals': existing_proposals,
        # エントリー制廃止により削除: already_entered, entered_last_month, entry_success, already_entered_users
        'next_month': next_month,
        'decided_title': decided_title,
        'title_candidates': title_candidates,
        'page_obj': page_obj,
        'same_title_novels': page_obj.object_list,
        'title_proposals': title_proposals,
    })

# 過去の同タイトル一覧を表示する新しい関数
@login_required
def all_same_title_novels(request):
    # is_same_title_game=True のノベルのみを取得（「募集します」を含むタイトルを除外）
    novels = Novel.objects.filter(
        is_same_title_game=True,
        status='published'
    ).exclude(
        title__contains='募集します'
    ).order_by('-published_date').select_related('author')

    # 🔥 一番槍判定：各タイトル・各イベント月で最古の投稿を特定 🔥
    from collections import defaultdict
    ichiban_yari_ids = set()

    # タイトル・イベント月ごとにグループ化
    novels_by_title_event_month = defaultdict(list)
    for novel in novels:
        # same_title_event_month（提案月の翌月）でグループ化
        event_month = novel.same_title_event_month
        if event_month:
            title_month_key = (novel.title, event_month)
            novels_by_title_event_month[title_month_key].append(novel)

    # 各グループで最古のpublished_dateの投稿を特定
    for (title, event_month), group_novels in novels_by_title_event_month.items():
        earliest_novel = min(group_novels, key=lambda n: n.published_date)
        ichiban_yari_ids.add(earliest_novel.id)

    # 月ごとの提案者情報を取得
    monthly_info = MonthlySameTitleInfo.objects.all().select_related('proposer', 'novel')
    monthly_proposals = {}

    for info in monthly_info:
        month_key = info.month
        monthly_proposals[month_key] = {
            'proposer': info.proposer,
            'title': info.title
        }

    # ページネーション
    paginator = Paginator(novels, 20)
    page = request.GET.get('page', 1)
    page_obj = paginator.get_page(page)

    context = {
        'page_obj': page_obj,
        'monthly_proposals': monthly_proposals,
        'ichiban_yari_ids': ichiban_yari_ids,  # 一番槍のIDリストを渡す
    }

    return render(request, 'game_same_title/all_same_title_novels.html', context)

from django.contrib import messages
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from datetime import timedelta
from .models import TitleProposal
# 🔥 通知関数のimportを削除（PendingNotificationに変更したため）

from django.utils import timezone

@login_required
def create_title_proposal(request):
    proposer = request.user
    current_month_start = timezone.now().date().replace(day=1)  # 今月の初めを取得
    next_month_start = current_month_start + relativedelta(months=1)
    current_month_end = next_month_start - timedelta(days=1)  # 今月の終わりを取得

    # 現在の月の提案を取得
    existing_proposals = TitleProposal.objects.filter(
        proposer=proposer,
        proposed_at__gte=current_month_start,
        proposed_at__lte=current_month_end
    )
    proposals_count = existing_proposals.count()  # ここで提案の数をカウント

    # 提案可能なタイトルのインデックスリストを生成
    remaining_proposals_indexes = [i for i in range(1, 4)]  # 常に1から3までのインデックス

    if request.method == "POST":
        if proposals_count < 3:
            titles = [request.POST.get(f'title{i}') for i in range(1, 4)]
            for title in titles:
                if title:
                    created_proposal = TitleProposal.objects.create(
                        proposer=proposer,
                        title=title,
                        proposed_at=timezone.now().date(),  # 時間情報を除外して日付のみを保存
                        proposal_month=current_month_start
                    )

                    # 🔥 タイトル提案通知を翌日12時に送信するため予約
                    from .models import PendingNotification
                    notification, created = PendingNotification.objects.get_or_create(
                        notification_type='提案',
                        proposal=created_proposal
                    )
                    if created:
                        logger.info(f'タイトル提案通知予約: {title} (提案者: {proposer.username})')
                    else:
                        logger.info(f'タイトル提案通知既存: {title} (重複作成を防止)')

            messages.success(request, '提案が成功しました。')
            return redirect('game_same_title:same_title')
        else:
            messages.error(request, '提案の上限に達しています。')

    return render(request, 'game_same_title/same_title.html', {
        'existing_proposals': existing_proposals,
        'remaining_proposals_indexes': remaining_proposals_indexes[:3-proposals_count],
    })

from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from .models import TitleProposal
import datetime

from dateutil.relativedelta import relativedelta
import logging

# ロガーの設定
logger = logging.getLogger(__name__)

from dateutil.relativedelta import relativedelta
from django.contrib import messages  # 必要なインポートを追加

# エントリー制廃止により entry_for_same_title view を削除

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from .models import TitleProposal
from .forms import NovelForm  # 必要なフォームをインポート
from django.shortcuts import render, redirect
from django.http import HttpResponseForbidden
import datetime
from django.db.models.functions import TruncDate

# 今の同タイトル情報を取得する関数を追加するで！
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from .models import MonthlySameTitleInfo  # この行を追加
from django.http import Http404  # この行を追加

def get_current_month_same_title_info():
    current_month = timezone.now().strftime('%Y-%m')
    try:
        current_month_info = MonthlySameTitleInfo.objects.get(month=current_month)
        return {
            'title': current_month_info.title,
            'author': current_month_info.author,
            'published_date': current_month_info.published_date
        }
    except MonthlySameTitleInfo.DoesNotExist:
        return None

from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
import logging
from django.conf import settings
from django.contrib.auth import get_user_model

# ロガーの設定
logger = logging.getLogger(__name__)

@login_required
def post_or_edit_same_title(request, novel_id=None):
    User = get_user_model()  # カスタムユーザーモデル取得
    current_month_same_title_info = get_current_month_same_title_info()

    # エントリー制廃止により check_entered_last_month のアクセス制限を削除

    # 🔥 前月の提案のみ取得（正しい仕様）🔥
    current_month = timezone.now().date().replace(day=1)
    last_month = current_month - relativedelta(months=1)

    # 前月に提案されたタイトルのみ取得
    last_month_proposals = TitleProposal.objects.filter(
        proposal_month__year=last_month.year,
        proposal_month__month=last_month.month
    ).exclude(proposer=request.user).select_related('proposer')

    # JSONシリアライズ
    last_month_proposals_json = serializers.serialize('json', last_month_proposals)
    logger.info(f"JSONデータ: {last_month_proposals_json}")

    # 現在の月の一番槍情報
    current_month = timezone.now().strftime('%Y-%m')
    current_month_same_title_info = MonthlySameTitleInfo.objects.filter(month=current_month).first()
    
    logger.info(f"現在の月: {current_month}")
    if current_month_same_title_info:
        logger.info(f"一番槍情報: ID={current_month_same_title_info.id}, "
                   f"タイトル={current_month_same_title_info.title}, "
                   f"作者={current_month_same_title_info.author}")
    else:
        logger.info("一番槍情報: なし")
    
    logger.info("=== デバッグ情報 終了 ===")

    novel = None
    edit = False
    is_published = False
    is_locked = False

    # novel_idが提供されている場合は編集、そうでなければ新規作成
    if novel_id:
        try:
            novel_id = int(novel_id)  # 確実に整数に変換
            novel = get_object_or_404(Novel, id=novel_id, author=request.user)
            form = NovelForm(request.POST or None, instance=novel, initial={'is_same_title_game': novel.is_same_title_game})
            is_published = novel.status == 'published'
            is_locked = MonthlySameTitleInfo.objects.filter(novel=novel).exists()
            edit = True
        except ValueError:
            messages.error(request, '不正なIDが指定されました。')
            return redirect('error_url')
    else:
        # 新規作成の場合
        novel = Novel()
        form = NovelForm(request.POST or None, initial={'is_same_title_game': True})
        is_published = False
        is_locked = False
        edit = False

    if request.method == 'POST':
        if novel_id:
            novel = get_object_or_404(Novel, id=novel_id, author=request.user)
            form = NovelForm(request.POST, instance=novel)
        else:
            form = NovelForm(request.POST)
            if form.is_valid():
                new_novel = form.save(commit=False)
                new_novel.author = request.user
                # 🔥 ジャンルはユーザー選択のまま（変更しない）
                new_novel.save()
                # 正しいURL名を使用してリダイレクト
                return redirect(reverse('game_same_title:post_or_edit_same_title_with_id', kwargs={'novel_id': new_novel.id}))
            else:
                print("えらああああああああああああああああああForm errors:", form.errors)

        if form.is_valid():
            novel = form.save(commit=False)
            if not novel_id:
                novel.author = request.user  # 新規作成時にのみ作者を設定
            novel.author = request.user
            novel.title = form.cleaned_data['title']
            action = request.POST.get('action', '')

            current_month = timezone.now().strftime('%Y-%m')
            if not novel.same_title_event_month and novel.is_same_title_game:
                novel.same_title_event_month = current_month
            # 🔥 ジャンルはユーザー選択のまま（変更しない）
            existing_entry = MonthlySameTitleInfo.objects.filter(month=current_month).first()

            if is_locked:
                if action == 'draft' or action == 'rest':
                    if form.is_valid():
                        novel.content = form.cleaned_data['content']
                        # content, title, initialを更新対象に指定
                        novel.save(update_fields=['content'])
                        messages.success(request, '変更が保存されました。')
                    if action == 'draft':
                        return redirect('game_same_title:post_or_edit_same_title_with_id', novel_id=novel.id)
                    elif action == 'rest':
                        return redirect('game_same_title:same_title')
                elif action == 'publish':
                    if form.is_valid():
                        novel.content = form.cleaned_data['content']
                        novel.status = 'published'  # ステータスをpublishedに設定
                        novel.published_date = timezone.now()  # 🆕 公開日時を設定
                        novel.save(update_fields=['content', 'status', 'published_date'])  # 🆕 published_dateを追加
                        messages.success(request, '小説が更新され、公開されました。')
                        return redirect('game_same_title:same_title')
                elif action == 'delete':
                    messages.error(request, '一番槍は消せません。')
                    return redirect('game_same_title:post_or_edit_same_title_with_id', novel_id=novel.id)
                
            else:
                if action == 'publish':
                    if form.is_valid():
                        novel.content = form.cleaned_data['content']
                        novel.status = 'published'  # ステータスをpublishedに設定
                        novel.published_date = timezone.now()  # 🆕 公開日時を設定
                        # 🔥 ジャンルはユーザー選択のまま（変更しない）
                        novel.save(update_fields=['content', 'status', 'published_date', 'is_same_title_game'])  # 🆕 published_dateを追加
                        # 🔥 メッセージは一番槍・追随投稿で別々に出す（重複削除）
                        if not existing_entry and novel.is_same_title_game:
                            user_instance = User.objects.get(username=novel.author.username)
                            title_proposal = TitleProposal.objects.filter(title=novel.title).first()
                            proposer_instance = title_proposal.proposer if title_proposal else request.user

                            MonthlySameTitleInfo.objects.create(
                                title=novel.title,
                                author=user_instance,
                                proposer=proposer_instance,
                                published_date=timezone.now(),
                                month=current_month,
                                novel=novel
                            )
                            # 🔥 一番槍決定通知を18時に送信するため予約
                            from .models import PendingNotification
                            notification, created = PendingNotification.objects.get_or_create(
                                notification_type='決定',
                                novel=novel
                            )
                            if created:
                                logger.info(f'一番槍通知予約: {novel.title} (ユーザー: {novel.author.username})')
                            else:
                                logger.info(f'一番槍通知既存: {novel.title} (重複作成を防止)')
                            messages.success(request, 'やったね！あんたが今月の一番槍や！')
                        elif existing_entry and novel.is_same_title_game:
                            # 🔥 追随投稿の場合：順位を計算して全員に通知（2番目以降全員） 🔥
                            current_year = timezone.now().year
                            current_month_num = timezone.now().month

                            # 今月の同タイトル投稿を published_date 昇順で取得
                            same_title_novels = Novel.objects.filter(
                                title=novel.title,
                                published_date__year=current_year,
                                published_date__month=current_month_num,
                                status='published'
                            ).order_by('published_date')

                            # 現在の投稿の順位を特定（1-indexed）
                            rank = list(same_title_novels.values_list('id', flat=True)).index(novel.id) + 1

                            # 🔥 2番目以降全員に通知予約（18時送信）
                            if rank >= 2:
                                from .models import PendingNotification
                                notification, created = PendingNotification.objects.get_or_create(
                                    notification_type='追随',
                                    novel=novel,
                                    rank=rank
                                )
                                if created:
                                    logger.info(f'追随通知予約: {novel.title} - {rank}番目 (ユーザー: {novel.author.username})')
                                else:
                                    logger.info(f'追随通知既存: {novel.title} - {rank}番目 (重複作成を防止)')
                                messages.success(request, '小説が公開されました。')
                        return redirect('game_same_title:same_title')

                elif action == 'draft' or action == 'rest':
                    novel.status = 'draft'
                    novel.save()
                    form.save_m2m()
                    if action == 'draft':
                        return redirect(reverse('game_same_title:post_or_edit_same_title_with_id', kwargs={'novel_id': novel.id}))
                    elif action == 'rest':
                        return redirect('accounts:view_profile')

                elif action == 'delete':
                    if novel:
                        novel.delete()
                        messages.success(request, '小説が削除されました。')
                        return redirect('game_same_title:same_title')
        else:
            print(form.errors)



    is_same_title_game = form['is_same_title_game'].value() if 'is_same_title_game' in form.fields else False

    # GETリクエスト時にフォムの初期を設
    if request.method == 'GET':
        initial_data = {
            'is_same_title_game': True  # 新規作成時にデフォルトでTrueに設定
        }
        if novel_id:
            # 既存のノベルデータがある場合は、そのデータでフォームを初期化
            initial_data.update({
                'title': novel.title,
                'content': novel.content,
                'initial': novel.initial,
                'genre': novel.genre,  # 🔥 ジャンルフィールド追加（消失バグ修正）
                'is_same_title_game': novel.is_same_title_game  # 既存の値を使用
            })
        form = NovelForm(initial=initial_data)

    # 🆕 can_edit 判定を追加（自分の小説かつログイン中）
    can_edit = request.user.is_authenticated and novel and novel.author == request.user

    context = {
        'form': form,
        'novel': novel,
        'edit': edit,
        'last_month_proposals': last_month_proposals,
        'is_published': is_published,
        'current_month_same_title_info': current_month_same_title_info,
        'is_same_title_game': is_same_title_game,
        'is_locked': is_locked,
        'last_month_proposals_json': last_month_proposals_json,
        'can_edit': can_edit,  # 🆕 can_editを追加
    }

    # デバッグ用のログ出力を追加
    logger.debug(f"前月の提案数: {len(last_month_proposals)}")
    logger.debug(f"JSONデータ: {last_month_proposals_json}")

    # フォームのタイトルフィールドの値をログに出力
    logger.debug(f"くぅうううううううううううううううううううううんForm title value: {form['title'].value()}")

    return render(request, 'game_same_title/same_title_post_or_edit.html', context)
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db import transaction
from .models import Novel
import logging
from django.conf import settings
from django.http import HttpResponse

# ロガーの設定
logger = logging.getLogger(__name__)

@login_required
@transaction.atomic
def auto_save(request):

    if request.method != 'POST':
        logger.warning(f'無効なリクエストメソッド: {request.method}が使用されました')
        return JsonResponse({'status': 'error', 'message': '無効なリクエスト'}, status=405)

    novel_id = request.POST.get('novel_id')
    title = request.POST.get('title')
    content = request.POST.get('content')
    is_same_title_game = request.POST.get('is_same_title_game') == 'true' if request.POST.get('is_same_title_game') else True
    initial = request.POST.get('initial')

    logger.debug(f'受け取ったデータ: novel_id={novel_id}, title={title}, content={content}, is_same_title_game={is_same_title_game}, initial={initial}')

    if novel_id:
        try:
            novel_id = int(novel_id)
            novel = Novel.objects.get(id=novel_id)
            logger.debug(f'既存の小説を更新中: id={novel_id}')
        except ValueError:
            logger.error(f'小説IDの形式が不正です: {novel_id}')
            return JsonResponse({'status': 'error', 'message': '小説IDの形式が不正です'}, status=400)
        except Novel.DoesNotExist:
            logger.error(f'指定された小説が見つかりません: ID {novel_id}')
            return JsonResponse({'status': 'error', 'message': '指定された小説が見つかりません'}, status=404)

        novel.title = title
        novel.content = content
        novel.is_same_title_game = is_same_title_game
        novel.initial = initial
        novel.save()
        logger.info(f'小説ID {novel_id} のデータが更新されました')
        return JsonResponse({'message': '自動保存されました。', 'novel_id': novel_id})
    else:
        novel = Novel.objects.create(
            title=title,
            content=content,
            is_same_title_game=is_same_title_game,
            initial=initial,
            author=request.user  # authorフィールドを追加
        )
        logger.info(f'新しい小説が作成されました: ノベルID {novel.id}')
        return JsonResponse({'message': '自動保存されました。', 'novel_id': novel.id})
    

