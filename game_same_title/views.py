from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from .models import TitleProposal, SameTitleEntry
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

def check_entered_last_month(user):
    today = timezone.localtime(timezone.now())
    last_month_start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
    last_month_start = last_month_start.replace(day=1)
    last_month_end = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0) - timedelta(seconds=1)
    return SameTitleEntry.objects.filter(
        user=user,
        month__gte=last_month_start,
        month__lte=last_month_end
    ).exists()

def get_next_month_str():
    next_month = (timezone.now() + relativedelta(months=+1)).month
    return f"{next_month}月"

from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from datetime import timedelta
from .models import Novel, MonthlySameTitleInfo, TitleProposal, SameTitleEntry
import logging
import json

logger = logging.getLogger(__name__)

from django.core.paginator import Paginator
from django.http import JsonResponse
import json
from django.utils.dateformat import DateFormat

def same_title(request, page=1):
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

    if request.user.is_authenticated:
        proposer = request.user
        next_month_start = current_month_date + relativedelta(months=1)
        current_month_end = next_month_start - timedelta(seconds=1)

        existing_proposals = TitleProposal.objects.filter(
            proposer=proposer,
            proposed_at__gte=current_month_date,
            proposed_at__lt=current_month_end 
        )
        already_entered = SameTitleEntry.objects.filter(user=request.user, month=current_month_date).exists()
        entered_last_month = check_entered_last_month(request.user)

        last_month = current_month_date - relativedelta(months=1)
        title_candidates = [
            {'title': candidate.title, 'proposer_nickname': candidate.proposer.nickname}
            for candidate in TitleProposal.objects.filter(proposal_month__year=last_month.year, proposal_month__month=last_month.month)
        ]
        already_entered_users = SameTitleEntry.objects.filter(month=current_month_date).select_related('user__profile')
    else:
        existing_proposals = []
        already_entered = False
        entered_last_month = False
        title_candidates = []
        already_entered_users = []

    next_month = get_next_month_str()
    entry_success = request.session.pop('entry_success', None)

    return render(request, 'game_same_title/same_title.html', {
        'existing_proposals': existing_proposals,
        'already_entered': already_entered,
        'entered_last_month': entered_last_month,
        'next_month': next_month,
        'entry_success': entry_success,
        'decided_title': decided_title,
        'title_candidates': title_candidates,
        'page_obj': page_obj,
        'already_entered_users': already_entered_users,
        'same_title_novels': page_obj.object_list,
        'title_proposals': title_proposals,  # 提案者情報を追加
    })

# 過去の同タイトル一覧を表示する新しい関数
@login_required
def all_same_title_novels(request):
    # is_same_title_game=True のノベルのみを取得
    novels = Novel.objects.filter(
        is_same_title_game=True,
        status='published'
    ).order_by('-published_date').select_related('author')
    
    # 月ごとの提案者情報と一番槍情報を MonthlySameTitleInfo から取得
    monthly_info = MonthlySameTitleInfo.objects.all().select_related('proposer', 'novel')
    monthly_proposals = {}
    ichiban_yari_info = {}
    
    # 各月の情報を整理
    for info in monthly_info:
        month_key = info.month
        monthly_proposals[month_key] = {
            'proposer': info.proposer,
            'title': info.title
        }
        # 一番槍情報を設定
        ichiban_yari_info[month_key] = info.novel
    
    # ページネーション
    paginator = Paginator(novels, 20)
    page = request.GET.get('page', 1)
    page_obj = paginator.get_page(page)
    
    context = {
        'page_obj': page_obj,
        'monthly_proposals': monthly_proposals,
        'ichiban_yari_info': ichiban_yari_info,
    }
    
    return render(request, 'game_same_title/all_same_title_novels.html', context)

from django.contrib import messages
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from datetime import timedelta
from .models import TitleProposal

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
                    TitleProposal.objects.create(
                        proposer=proposer, 
                        title=title, 
                        proposed_at=timezone.now().date(),  # 時間情報を除外して日付のみを保存
                        proposal_month=current_month_start
                    )
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
from .models import SameTitleEntry

from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from .models import TitleProposal, SameTitleEntry
import datetime

from dateutil.relativedelta import relativedelta
import logging

# ロガーの設定
logger = logging.getLogger(__name__)

from dateutil.relativedelta import relativedelta
from django.contrib import messages  # 必要なインポートを追加

@login_required
def entry_for_same_title(request):
    current_month = timezone.now().date().replace(day=1)
    already_entered = SameTitleEntry.objects.filter(user=request.user, month=current_month).exists()
    
    next_month_str = get_next_month_str()

    # 先月の初日と最終日を計算
    last_month_start = current_month - relativedelta(months=1)
    last_month_end = last_month_start + relativedelta(months=1, days=-1)

    # 先月のイトル提案を取得
    existing_proposals = TitleProposal.objects.filter(
        proposer=request.user,
        proposed_at__gte=last_month_start,
        proposed_at__lte=last_month_end
    )

    # ログに先月の初日と最終日を出力
    logger.debug(f"先月の初日: {last_month_start}, 最終日: {last_month_end}")

    if request.method == 'POST':
        if not already_entered:
            SameTitleEntry.objects.create(user=request.user, month=current_month)
            messages.success(request, 'エントリーが完了しました。')  # 成功メッセージを追加
            request.session['entry_success'] = True
            return redirect(reverse('game_same_title:same_title'))
        else:
            messages.error(request, 'すでにエントリー済みです。')  # エラーメッセージを追加
            return render(request, 'game_same_title/same_title.html', {
                'already_entered': True,
                'next_month': next_month_str,
                'existing_proposals': existing_proposals,
            })
    else:
        context = {
            'already_entered': already_entered,
            'next_month': next_month_str,
            'existing_proposals': existing_proposals,
        }
        if 'entry_success' in request.session:
            context['entry_success'] = request.session.pop('entry_success', None)

        return render(request, 'game_same_title/same_title.html', context)

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from .models import TitleProposal, SameTitleEntry
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


    if not check_entered_last_month(request.user):
        return HttpResponseForbidden("先月エントリーしていないため、このページにはクセスできせん。")

    # 前月の初日と最終日を計算
    current_month = timezone.now().date().replace(day=1)
    last_month_start = current_month - relativedelta(months=1)
    last_month_end = current_month - timedelta(days=1)

    # 前月のタイトル提案を取得
    last_month_proposals = TitleProposal.objects.filter(
        proposal_month__gte=last_month_start,
        proposal_month__lte=last_month_end
    ).exclude(proposer=request.user)  # 自分の提案は除外

    # デバッグ情報を詳しく出力
    logger.info("=== デバッグ情報 開始 ===")
    logger.info(f"前月の期間: {last_month_start} から {last_month_end}")
    logger.info(f"前月の提案数: {last_month_proposals.count()}")
    
    # 実際のSQLクエリを確認
    logger.info("実行されるSQL:")
    logger.info(str(last_month_proposals.query))
    
    # 各提案の詳細を確認
    for proposal in last_month_proposals:
        logger.info(f"提案詳細: ID={proposal.id}, タイトル={proposal.title}, "
                   f"提案者={proposal.proposer}, 提案日={proposal.proposed_at}, "
                   f"提案月={proposal.proposal_month}")

    # JSONシリアライズの確認
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
                if new_novel.is_same_title_game:
                    new_novel.genre = '同タイトル'
                    print("Genre set to 同タイトル")
                new_novel.save()  # ここで先にnovelを保存

                # 一番槍の処理（必要な場合）
                current_month = timezone.now().strftime('%Y-%m')
                existing_entry = MonthlySameTitleInfo.objects.filter(month=current_month).first()
                
                if not existing_entry and new_novel.is_same_title_game:
                    title_proposal = TitleProposal.objects.filter(title=new_novel.title).first()
                    proposer_instance = title_proposal.proposer if title_proposal else request.user
                    
                    MonthlySameTitleInfo.objects.create(
                        title=new_novel.title,
                        author=request.user,
                        proposer=proposer_instance,
                        published_date=timezone.now(),
                        month=current_month,
                        novel=new_novel  # 保存済みのnovelを使用
                    )
                    messages.success(request, 'やったね！あんたが今月の一番槍や！')

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
            if not novel.genre and novel.is_same_title_game:
                novel.genre = '同タイトル'

            # アクションに応じた処理
            if action == 'publish':
                novel.status = 'published'
                novel.save()
                
                # 一番槍の処理（公開時のみ）
                existing_entry = MonthlySameTitleInfo.objects.filter(month=current_month).exists()
                if not existing_entry and novel.is_same_title_game:
                    title_proposal = TitleProposal.objects.filter(title=novel.title).first()
                    proposer_instance = title_proposal.proposer if title_proposal else request.user
                    
                    MonthlySameTitleInfo.objects.create(
                        title=novel.title,
                        author=request.user,
                        proposer=proposer_instance,
                        published_date=timezone.now(),
                        month=current_month,
                        novel=novel
                    )
                    messages.success(request, 'やったね！あんたが今月の一番槍や！')
                return redirect('game_same_title:same_title')

            elif action == 'rest':
                novel.status = 'draft'  # 休息時は必ずdraft
                novel.save()
                messages.success(request, '変更を保存して休憩します。')
                return redirect('accounts:view_profile')

            elif action == 'draft':
                novel.status = 'draft'
                novel.save()
                messages.success(request, '下書きを保存しました。')
                return redirect('game_same_title:post_or_edit_same_title_with_id', novel_id=novel.id)

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
                'is_same_title_game': novel.is_same_title_game  # 既存の値を使用
            })
        form = NovelForm(initial=initial_data)

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
    }

    # デバッグ用のログ出力を追加
    logger.debug(f"前月の提案数: {last_month_proposals.count()}")
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
    

