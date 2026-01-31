import json
import logging
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseRedirect, JsonResponse, Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views.generic import ListView

from .forms import NovelForm, CommentForm
from .models import Novel, Like, Comment
from game_maturi.models import MaturiGame

# ログ設定
logger = logging.getLogger(__name__)

@login_required
def post_or_edit_novel(request, novel_id=None):
    novel = None
    edit_mode = False

    # POSTリクエストからnovelIdを優先的に取得し、なければURLパラメータから取得
    # 🔥 空文字列の場合はNoneとして扱う（重複レコード問題の修正）
    novel_id_from_post = request.POST.get('novelId')
    if novel_id_from_post:  # 空文字列でない場合のみ使用
        novel_id = novel_id_from_post

    # デバッグ：novelIdがちゃんと取得できてるか確認
    logger.info(f"post_or_edit_novel: novel_id={novel_id}, URL引数={novel_id}, POST={request.POST.get('novelId')}")

    if novel_id:
        # select_relatedを使用して、関連するauthorのみを事前に取得
        novel = get_object_or_404(Novel.objects.select_related('author'), pk=novel_id)
        if novel.author != request.user and novel.original_author_id != request.user.id:
            return HttpResponseForbidden("あなたにはこの権限がありません。")
        edit_mode = True
    else:
        novel = Novel(author=request.user)  # 新規作成にはNovelインスタンスを新しく作る
        edit_mode = False  # 新規作成モード

    if request.method == 'POST':
        form = NovelForm(request.POST, request.FILES, instance=novel)
        action = request.POST.get('action', 'draft')

        if action == 'delete':
            # 保存済みのインスタンスのみ削除可能
            if novel.pk:
                # 🔥🔥🔥 一番槍削除禁止チェック（2025-10-16制定）🔥🔥🔥
                if novel.is_first_post:
                    messages.error(request, '一番槍の栄誉に輝いているので、今から、消すことが難しいです！')
                    return redirect('novels:edit_novel', novel_id=novel.pk)

                # 削除実行
                is_same_title = novel.is_same_title_game if hasattr(novel, 'is_same_title_game') else False
                novel.delete()

                # 🔥🔥🔥 遷移先変更（2025-10-16制定）🔥🔥🔥
                if is_same_title:
                    return redirect('home:home')  # 同タイトル作品 → ホーム画面
                else:
                    return redirect('accounts:view_profile')  # 通常作品 → プロフィールページ
            return redirect('accounts:view_profile')  # プロファイルページにリダイレクト

        if action == 'rest':
            return redirect('accounts:view_profile')

        if form.is_valid():
            # 編集前のID確認（既存レコードか新規作成か）
            original_id = novel.id if novel and novel.id else None
            logger.info(f"form.save前: original_id={original_id}, edit_mode={edit_mode}")

            saved_novel = form.save(commit=False)
            saved_novel.word_count = len(form.cleaned_data['content'].split())

            # 編集後のID確認（新しいレコードが作られてへんか確認）
            logger.info(f"form.save後: saved_novel.id={saved_novel.id}, original_id={original_id}")

            # 🔥🔥🔥 同タイトル情報を設定（超重要！）🔥🔥🔥
            if not novel_id:
                # 新規作成時：タイトル提案があれば同タイトルゲーム扱い
                from game_same_title.models import TitleProposal
                current_month = timezone.now().strftime('%Y-%m')
                now = timezone.now()

                # タイトル提案が存在するかチェック
                title_proposal = TitleProposal.objects.filter(
                    title=saved_novel.title,
                    proposal_month__year=now.year,
                    proposal_month__month=now.month
                ).first()
                if title_proposal:
                    # 同タイトルゲームとして保存
                    saved_novel.is_same_title_game = True
                    saved_novel.event = '同タイトル'
                    saved_novel.same_title_event_month = current_month
                    logger.info(f"同タイトル設定: title={saved_novel.title}, month={current_month}")

            # 🔥🔥🔥 同タイトル作品のステータス変更制御（2025-10-15）🔥🔥🔥
            if novel_id and saved_novel.is_same_title_game:
                # 編集時：同タイトル作品が公開済みの場合、draft に戻すのを禁止
                if novel.status == 'published' and action == 'draft':
                    logger.warning(f"同タイトル作品のステータス変更禁止: novel_id={novel_id}, 公開→作成中への変更は不可")
                    # ステータスを元のまま維持
                    saved_novel.status = novel.status
                elif action == 'publish':
                    saved_novel.status = 'published'
                elif action == 'draft':
                    saved_novel.status = 'draft'
            else:
                # 通常作品または新規作成時
                if action == 'publish':
                    saved_novel.status = 'published'
                elif action == 'draft':
                    saved_novel.status = 'draft'

            saved_novel.save()
            form.save_m2m()

            # 🔥🔥🔥 祭り小説の maturi_novels 追加処理（2026-01-11バグ修正）🔥🔥🔥
            # 祭り小説（original_author がある）の場合、maturi_novels に追加する
            # 通常投稿ページからでも漏れないようにする
            if saved_novel.original_author:
                active_game = MaturiGame.find_active_game_for_writing()
                if active_game and not active_game.maturi_novels.filter(id=saved_novel.id).exists():
                    active_game.maturi_novels.add(saved_novel)
                    active_game.save()
                    logger.info(f"祭り小説をmaturi_novelsに追加: novel_id={saved_novel.id}, game={active_game.title}")

            # 🔥🔥🔥 同タイトル通知処理（2025-10-16追加・超重要）🔥🔥🔥
            if action == 'publish' and saved_novel.is_same_title_game:
                from game_same_title.models import MonthlySameTitleInfo
                from game_same_title.notifications import send_same_title_decision_notification, send_same_title_follower_praise_notification

                current_month = timezone.now().strftime('%Y-%m')
                monthly_info = MonthlySameTitleInfo.objects.filter(month=current_month).first()

                if not monthly_info:
                    # 一番槍の場合：MonthlySameTitleInfo作成＋一番槍フラグ設定＋通知送信
                    saved_novel.is_first_post = True
                    saved_novel.save(update_fields=['is_first_post'])

                    # MonthlySameTitleInfo作成
                    from accounts.models import User
                    from game_same_title.models import TitleProposal

                    user_instance = User.objects.get(username=saved_novel.author.username)
                    current_time = timezone.now()
                    title_proposal = TitleProposal.objects.filter(
                        title=saved_novel.title,
                        proposal_month__year=current_time.year,
                        proposal_month__month=current_time.month
                    ).first()
                    proposer_instance = title_proposal.proposer if title_proposal else request.user

                    MonthlySameTitleInfo.objects.create(
                        title=saved_novel.title,
                        author=user_instance,
                        proposer=proposer_instance,
                        published_date=timezone.now(),
                        month=current_month,
                        novel=saved_novel
                    )

                    # 一番槍決定通知送信
                    send_same_title_decision_notification(saved_novel)
                    messages.success(request, 'やったね！あんたが今月の一番槍や！')
                    logger.info(f'一番槍通知送信: {saved_novel.title}')
                else:
                    # 追随投稿の場合：順位計算＋全員通知（2番目以降全員）
                    current_year = timezone.now().year
                    current_month_num = timezone.now().month

                    same_title_novels = Novel.objects.filter(
                        title=saved_novel.title,
                        published_date__year=current_year,
                        published_date__month=current_month_num,
                        status='published'
                    ).order_by('published_date')

                    rank = list(same_title_novels.values_list('id', flat=True)).index(saved_novel.id) + 1

                    if rank >= 2:
                        send_same_title_follower_praise_notification(saved_novel, rank)
                        logger.info(f'追随通知送信: {saved_novel.title} - {rank}番目')

            if action == 'publish':
                return redirect(reverse_lazy('home:home'))
            else:
                return redirect('novels:edit_novel', novel_id=saved_novel.id)
        else:
            logger.debug(f"Form errors: {form.errors}")
            return render(request, 'novels/post_or_edit_novel.html', {'form': form, 'novel': novel, 'edit': edit_mode, 'can_edit': True})
    else:
        # 🔥 同タイトル情報を取得 🔥
        same_title_info = None
        if novel and novel.is_same_title_game and novel.same_title_event_month:
            # 編集時：既存の同タイトル情報を取得
            same_title_info = {
                'year': novel.same_title_event_month[:4],
                'month': novel.same_title_event_month[5:7],
                'title': novel.title
            }
        elif not novel_id:
            # 新規作成時：今月の一番槍タイトルを取得
            from game_same_title.models import MonthlySameTitleInfo
            current_month = timezone.now().strftime('%Y-%m')
            monthly_info = MonthlySameTitleInfo.objects.filter(month=current_month).first()
            if monthly_info:
                same_title_info = {
                    'year': current_month[:4],
                    'month': current_month[5:7],
                    'title': monthly_info.title
                }

        form = NovelForm(instance=novel)
        return render(request, 'novels/post_or_edit_novel.html', {
            'form': form,
            'novel': novel,
            'edit': edit_mode,
            'can_edit': True,
            'same_title_info': same_title_info
        })


from django.core.cache import cache

@csrf_exempt
@login_required
def auto_save(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POSTメソッドが必要です。'}, status=405)

    try:
        data = json.loads(request.body)
        novel_id = data.get('novel_id')
        title = data.get('title', '')
        content = data.get('content', '')
        initial = data.get('initial', '')
        genre = data.get('genre', '')

        if not title or not content:
            return JsonResponse({'error': 'タトまは容空す'}, status=400)

        if novel_id:
            novel = get_object_or_404(
                Novel.objects.filter(
                    Q(author=request.user) | Q(original_author=request.user)
                ),
                pk=novel_id
            )
            current_status = novel.status  # 既存作品の公開状態を保持
        else:
            novel = Novel(author=request.user)
            current_status = 'draft'

        novel.title = title
        novel.content = content
        novel.initial = initial
        novel.genre = genre
        novel.word_count = len(content.split())
        # 既存公開作品のステータスを維持し、未保存の新規作品のみ下書き扱いにする
        if novel.pk:
            novel.status = current_status
        else:
            novel.status = 'draft'
        novel.save()

        return JsonResponse({'novel_id': novel.id, 'message': '自動保存が完了しました。'})

    except json.JSONDecodeError:
        return JsonResponse({'error': '無効なJSONデータです。'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def get_unread_comments_count_for_novel(user, novel_id):
    # 特定の小説に対する未読コメントの数を返すロジックを実装
    novel = get_object_or_404(Novel, pk=novel_id)
    count = Comment.objects.filter(novel=novel, is_read=False).exclude(author=user).count()
    return count


import datetime
from django.db.models import Value, CharField
from django.db.models.functions import Coalesce

from accounts.models import User






@login_required
def delete_novel(request, novel_id):
    novel = get_object_or_404(Novel, pk=novel_id, author=request.user)  # 小説を取得

    # 🔥🔥🔥 一番槍削除禁止チェック（2025-10-16制定）🔥🔥🔥
    if novel.is_first_post:
        messages.error(request, '一番槍の栄誉に輝いているので、今から、消すことが難しいです！')
        return HttpResponseRedirect(reverse('novels:edit_novel', kwargs={'novel_id': novel_id}))

    # 削除実行
    is_same_title = novel.is_same_title_game if hasattr(novel, 'is_same_title_game') else False
    novel.delete()  # 小説を削除

    # 🔥🔥🔥 遷移先変更（2025-10-16制定）🔥🔥🔥
    if is_same_title:
        return HttpResponseRedirect(reverse('home:home'))  # 同タイトル作品 → ホーム画面
    else:
        return HttpResponseRedirect(reverse('accounts:view_profile'))  # 通常作品 → プロフィールページ

@login_required
@require_POST
def like_novel(request, novel_id):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "ログインが必要です"}, status=400)
    
    novel = get_object_or_404(Novel, pk=novel_id)
    like, created = Like.objects.get_or_create(user=request.user, novel=novel)
    
    if not created:
        like.delete()  # にいいねがあれば削除
        is_liked = False
    else:
        is_liked = True
    
    return JsonResponse({"is_liked": is_liked, "likes_count": novel.likes.count()})

def novel_detail(request, novel_id):
    """
    小説詳細ページのメイン処理
    Template: novels/detail.html

    関連する処理：
    - コメント投稿: post_comment関数で処理 (/novels/<novel_id>/comment/)
      ※ 祭り小説のコメント処理や、コメントの既読/未読管理もpost_comment関数で実装
    """
    logger.debug("="*50)
    logger.debug(f"1. リクエストされたURL: {request.path}")
    logger.debug(f"2. novel_id: {novel_id}")

    # N+1問題対策：author, original_author, maturi_gamesを事前取得
    novel = get_object_or_404(
        Novel.objects.select_related('author', 'original_author').prefetch_related('maturi_games'),
        id=novel_id
    )
    logger.debug(f"3. 取得された小説: ID={novel.id}, タイトル={novel.title}")

    # 祭り作品の判定をより詳細に
    logger.debug("\n==== 祭り作品判定 ====")
    logger.debug(f"小説ID: {novel.id}")
    logger.debug(f"hasattr(novel, 'maturi_games'): {hasattr(novel, 'maturi_games')}")
    if hasattr(novel, 'maturi_games'):
        logger.debug(f"novel.maturi_games.exists(): {novel.maturi_games.exists()}")
    logger.debug(f"original_author_id: {novel.original_author_id if hasattr(novel, 'original_author_id') else 'なし'}")
    logger.debug("=====================\n")

    logger.debug("\n==== ユーザー照合 ====")
    logger.debug(f"小説ID: {novel.id}")
    logger.debug(f"小説タイトル: {novel.title}")
    logger.debug(f"作者ID: {novel.author.id}")
    logger.debug(f"作者のメール: {novel.author.email}")
    logger.debug(f"ログインユーザーID: {request.user.id if request.user.is_authenticated else 'None'}")
    logger.debug(f"ログインユーザーメール: {request.user.email if request.user.is_authenticated else 'None'}")
    logger.debug("==================\n")

    comments_list = Comment.objects.filter(novel=novel).select_related('author').order_by('-created_at')
    form = CommentForm()

    # アクセス制御（下書きと予約公開は作者のみ閲覧可能）
    if novel.status in ['scheduled', 'draft'] and (
        not request.user.is_authenticated or 
        (
            request.user != novel.author and 
            not request.user.is_staff and
            # 祭り小説の場合は original_author もチェック
            not (hasattr(novel, 'original_author_id') and novel.original_author_id == request.user.id)
        )
    ):
        logger.debug(f"リダイレクト前の状態: novel.status={novel.status}, user_authenticated={request.user.is_authenticated}, user={request.user}, novel_author={novel.author}")
        messages.error(request, f'{novel.get_status_display()}の小説は、作者本人のみ閲覧できません。')
        return redirect('novels:novels_paginated')

    # 祭り作品かどうかの判定
    is_maturi = hasattr(novel, 'maturi_games') and novel.maturi_games.exists()
    # 🔥 予想期間中かどうかの判定（コメント作者を匿名にするため）
    is_prediction_period = False
    logger.debug(f"祭り作品判定: {is_maturi}")
    if is_maturi:
        logger.debug("祭り小説の詳細情報を表示")
        # 祭り小説の詳細情報を表示するための追加デバッグ
        maturi_games = novel.maturi_games.all()
        for game in maturi_games:
            logger.debug(f"祭りゲームID: {game.id}, タイトル: {game.title}")
            logger.debug(f"is_author_revealed: {game.is_author_revealed}")
            logger.debug(f"prediction_end_date: {game.prediction_end_date}")
            now = timezone.localtime(timezone.now()).date()
            logger.debug(f"現在時刻: {now}")
            logger.debug(f"予想期間終了？: {now > game.prediction_end_date}")
            # 🔥 予想期間中 = 作者未公開 && 予想期間終了してない
            if not game.is_author_revealed and game.is_prediction_period():
                is_prediction_period = True
                logger.debug(f"予想期間中！コメント作者を匿名にする")

    # 同イトル作品かどうかの判定
    is_same_title = novel.is_same_title_game if hasattr(novel, 'is_same_title_game') else False

    # 編集権限確認（ログインユーザーのみ）
    can_edit = False
    if request.user.is_authenticated:
        logger.debug("\n==== 編集権限チェック ====")
        logger.debug(f"リクエストユーザー: {request.user.id} - {request.user.email}")
        logger.debug(f"小説の作者: {novel.author.id} - {novel.author.email}")
        logger.debug(f"オリジナル作者: {novel.original_author_id if hasattr(novel, 'original_author_id') else 'なし'}")

        if is_maturi:
            # 祭り作品の場合、作者またはオリジナルの作者
            can_edit = (request.user == novel.author or
                       novel.original_author_id == request.user.id)
        else:
            # 通常作品の場合、作者または original_author_id が一致する場合
            can_edit = (request.user == novel.author or
                       (hasattr(novel, 'original_author_id') and
                        novel.original_author_id == request.user.id))

        logger.debug(f"編集権限: {can_edit}")
        logger.debug("="*50)

    # 未読コメント情報を取得（N+1対策：select_related追加）
    latest_unread_novels = []
    if request.user.is_authenticated:
        latest_unread_novels = Novel.objects.filter(
            author=request.user,
            comments__is_read=False,
            comments__author__isnull=False
        ).select_related('author').distinct().annotate(
            unread_count=Count(
                'comments',
                filter=Q(comments__is_read=False) & ~Q(comments__author=request.user),
                distinct=True
            )
        )

        # デバッグ用：実際のSQL文を表示
        logger.debug(f"SQL Query: {latest_unread_novels.query}")

        # デバッグ用：各コメントの詳細を表示（N+1対策：select_related追加）
        for unread_novel in latest_unread_novels:
            comments = Comment.objects.filter(
                novel=unread_novel,
                is_read=False
            ).exclude(author=request.user).select_related('author')
            logger.debug(f"Novel {unread_novel.id} unread comments:")
            for comment in comments:
                logger.debug(f"- Comment {comment.id}: by {comment.author}, content: {comment.content}")

            logger.debug(f"\n5. 祭り判定結果: {is_maturi}")
    if is_maturi:
        logger.debug("   祭り小説の詳細:")
        logger.debug(f"   - maturi_games: {novel.maturi_games.all()}")

    # コンテキスト作成直前の状態確認
    logger.debug("\n6. コンテキスト作成直前の小説情報:")
    logger.debug(f"   - ID: {novel.id}")
    logger.debug(f"   - タイトル: {novel.title}")

    # コンテキスト作成直前にデバッグ情報を追加
    logger.debug("\n==== コンテキスト変数 ====")
    logger.debug(f"user: {request.user}")
    logger.debug(f"can_edit: {can_edit}")
    logger.debug(f"hide_edit_button: {False}")

    # コメント情報のデバッグ出力を追加
    logger.debug("\n==== コメント情報 ====")
    for comment in comments_list:
        if comment.author:  # 作者が存在する場合のみ
            logger.debug(f"作者: {comment.author.nickname}")
            logger.debug(f"作者の色: {comment.author.comment_color}")
        else:
            logger.debug(f"作者: 退会したユーザー")
            logger.debug(f"作者の色: #cccccc")  # デフォルトのグレー色

    context = {
        'novel': novel,
        'can_edit': can_edit,
        'hide_edit_button': False,
        'form': form,
        'comments_list': comments_list,
        'form': form,
        'can_edit': can_edit,
        'is_maturi': is_maturi,
        'is_same_title': is_same_title,
        'is_prediction_period': is_prediction_period,  # 🔥 予想期間中はコメント作者を匿名にする
        'hide_edit_button': False  # これを追加
    }
    logger.debug(f"4. レンダリング前のcontext['novel']: ID={context['novel'].id}, タイトル={context['novel'].title}")
    logger.debug("="*50)

    return render(request, 'novels/detail.html', context)


# def some_view(request):
#     # 他のコンテキスト情報を取得するコード...
#     latest_unread_novel_id = None
#     if request.user.is_authenticated:
#         latest_unread_comment = Comment.objects.filter(novel__author=request.user, is_read=False).order_by('-created_at').first()
#         if latest_unread_comment:
#             latest_unread_novel_id = latest_unread_comment.novel.id

#     context = {
#         # 他のコンテキスト変数...
#         'unread_comments_count': get_unread_comments_count(request.user) if request.user.is_authenticated else 0,
#         'latest_unread_novel_id': latest_unread_novel_id,
#     }
#     return render(request, 'base.html', context)

# @login_required
# def unread_comments_count(request, novel_id):
#     """特定の小説の未読コメント数を返す"""
#     if not request.user.is_authenticated:
#         return JsonResponse({'unread_comments_count': 0})
    
#     # キャッシュキーを生成
#     cache_key = f'unread_comments_count_{novel_id}_{request.user.id}'
    
#     # キャッシュから値を取得
#     count = cache.get(cache_key)
    
#     if count is None:
#         # シンプルなクエリに修正
#         count = Comment.objects.filter(
#             novel_id=novel_id,
#             novel__author=request.user,
#             is_read=False
#         ).count()
        
#         # キャッシュに保存（60秒間）
#         cache.set(cache_key, count, 60)
    
#     return JsonResponse({'unread_comments_count': count})
    

@login_required
@require_POST
def toggle_comment_read_status(request, comment_id):
    try:
        # N+1対策：select_related追加
        # 祭り小説の場合はoriginal_authorも確認
        comment = get_object_or_404(
            Comment.objects.select_related('novel__author', 'novel__original_author', 'author').filter(
                Q(novel__author=request.user) | Q(novel__original_author=request.user)
            ),
            id=comment_id
        )
        data = json.loads(request.body)
        comment.is_read = data.get('is_read', False)
        comment.save()

        # キャッシュをクリア
        cache_key = f'total_unread_comments_{request.user.id}'
        cache.delete(cache_key)
        
        # 未読コメントのある小説の情報を更新して返す（N+1対策：select_related追加）
        # 祭り小説の場合はoriginal_authorも確認
        novels_with_unread = Novel.objects.filter(
            Q(author=request.user) | Q(original_author=request.user)
        ).select_related('author', 'original_author').annotate(
            unread_count=Count(
                'comments',
                filter=Q(
                    comments__is_read=False,
                    comments__author__isnull=False
                ) & ~Q(comments__author=request.user)
            )
        ).filter(
            unread_count__gt=0
        ).values('id', 'unread_count')

        # デバッグ用ログ
        logger.debug("サーバー側での未読カウント:")
        for novel in novels_with_unread:
            logger.debug(f"Novel {novel['id']}: {novel['unread_count']} unread comments")

        return JsonResponse({
            'success': True,
            'is_read': comment.is_read,
            'novels_with_unread': [
                {
                    'id': novel['id'],
                    'unread_count': novel['unread_count'],
                    'color_index': novel['id'] % 10
                }
                for novel in novels_with_unread
            ]
        })
    except Comment.DoesNotExist:
        return JsonResponse({'success': False, 'error': '権限がありません'}, status=403)

@login_required
@require_POST
def mark_comments_as_read(request):
    try:
        # JSONデータをパースする
        data = json.loads(request.body)
        comment_ids = data.get('commentIds', [])
        
        # 指定されたコメントIDに対するコメントを既読に設定
        # 祭り小説の場合はoriginal_authorも確認
        updated = Comment.objects.filter(
            id__in=comment_ids
        ).filter(
            Q(novel__author=request.user) | Q(novel__original_author=request.user)
        ).update(is_read=True)
        
        # キャッシュをリアする
        cache_key = f'total_unread_comments_{request.user.id}'
        cache.delete(cache_key)
        
        return JsonResponse({
            'success': True,
            'updated_count': updated
        })
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)






@login_required
def check_unread_comments(request, novel_id):
    """現在の小説以外に未読コメンがある小説を探す"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'ログインが必要です'}, status=403)

    # デバッグ情報
    logger.debug(f"Checking unread comments for novel {novel_id}")
    logger.debug(f"Current user: {request.user.username}")

    # 現在の小説以外で、未読コメントがある小説を探す（N+1対策：select_related追加）
    next_novel = Novel.objects.filter(
        author=request.user  # ユーザーが書いた小説
    ).exclude(
        id=novel_id  # 現在の小説を除外
    ).select_related('author').annotate(
        unread_count=Count(
            'comments',
            filter=Q(comments__is_read=False) & ~Q(comments__author=request.user)
        )
    ).filter(
        unread_count__gt=0  # 未読コメントが1つ以上ある小説のみ
    ).order_by('-comments__created_at').first()

    if next_novel:
        logger.debug(f"Found next novel with unread comments: {next_novel.title}")
        return JsonResponse({'unread_novel_id': next_novel.id})
    else:
        logger.debug("No other novels with unread comments found")
        return JsonResponse({'unread_novel_id': None})


# 遅延のコメントコード
from django.core.paginator import EmptyPage, PageNotAnInteger

@login_required
def load_more_comments(request, novel_id):
    page = request.GET.get('page')
    # N+1対策：select_related追加
    comments_list = Comment.objects.filter(novel_id=novel_id).select_related('author').order_by('-created_at')
    paginator = Paginator(comments_list, 5)  # 1ページあたり5件のコメントを表示

    try:
        comments = paginator.page(page)
    except PageNotAnInteger:
        comments = paginator.page(1)
    except EmptyPage:
        comments = paginator.page(paginator.num_pages)

    comments_data = list(comments.object_list.values('id', 'content', 'author__nickname', 'created_at'))
    return JsonResponse({
        'comments': comments_data,
        'has_next': comments.has_next()
    })



@login_required
@require_POST
def unpublish_novel(request, novel_id):
    # N+1対策：select_related追加
    novel = get_object_or_404(Novel.objects.select_related('author'), pk=novel_id)
    
    if novel.author != request.user:
        return HttpResponseForbidden("あなにはこの小を編集する権限がありません。")
    
    novel.status = 'draft'
    novel.save()
    
    # 編集ページのURLをJSONで返す
    edit_url = reverse('novels:edit_novel', kwargs={'novel_id': novel_id})
    return JsonResponse({'redirect_url': request.build_absolute_uri(edit_url)})


# 今これを使わない方向で進める予定
# @login_required
def index(request):
    novels_list = Novel.objects.select_related(
        'author', 'original_author'  # 🔥 original_author も取得
    ).prefetch_related(
        'comments__author',  # コメントとその作者を事前に取得
        'likes',  # いいねの情報を事前に取得
        'maturi_games'  # 🔥 祭りゲーム情報も取得（get_display_author フィルターで使用）
    ).annotate(
        likes_count=Count('likes'),
        comments_count=Count('comments')
    ).filter(status='published').order_by('-published_date')  # 投稿日の降順に並替える

    # 🔥 祭り小説を「執筆期間中」かつ「予想期間前」のみ除外（ゲームの公平性のため）
    # 公開後は普通に一覧に表示される（予想期間・結果発表期間・祭り終了後も表示）
    today = timezone.localtime(timezone.now()).date()  # 🔥 JST日付取得
    # 現在進行中の祭りを取得（終了してへん祭り）
    active_games = MaturiGame.objects.filter(maturi_end_date__gte=today)
    for game in active_games:
        # 予想期間が始まっていない AND まだ執筆期間中の場合のみ除外
        if not game.is_prediction_period() and game.start_date and today <= game.end_date:
            # 執筆期間中で予想期間前の祭り小説のみ除外
            novels_list = novels_list.exclude(maturi_games=game)

    # # 作者情報を取得するためのユーIDリクエストから取得
    # author_id = request.GET.get('author_id')
    # if author_id:
    #     author_info = get_user_info(author_id)  # キャッシュからユーザー情報を取得
    #     print("Author Info:", author_info)  # コンソールに作者情報を出力

    sort_by = request.GET.get('sort_by', 'published_date')
    order = request.GET.get('order', 'desc')
    search = request.GET.get('search', '')
    post_date_from_year = request.GET.get('post_date_from_year', None)
    post_date_to_year = request.GET.get('post_date_to_year', None)
    author_search = request.GET.get('author_search', '')
    author_select = request.GET.get('author_select', '')
    title_search = request.GET.get('title_search', '')
    title_select = request.GET.get('title_select', '')
    min_word_count = request.GET.get('min_word_count', None)
    max_word_count = request.GET.get('max_word_count', None)
    genre = request.GET.get('genre', '')
    if genre:
        novels_list = novels_list.filter(genre=genre)

    if post_date_from_year:
        novels_list = novels_list.filter(published_date__year__gte=post_date_from_year)
    if post_date_to_year:
        novels_list = novels_list.filter(published_date__year__lte=post_date_to_year)

    # 作者名とタイトルの選択肢を得
    author_choices = User.objects.all().order_by('nickname').values_list('id', 'nickname')
    title_choices = Novel.objects.filter(status='published').order_by('title').values_list('id', 'title')

    # 月のリストを生成
    months = list(range(1, 13))
    # 年のリストを生成
    years = list(range(0, 5001))

    # 作者名での昧索正規現使用して「けにお」が前後や間にある場合も網羅）
    author_search = request.GET.get('author_search', '').strip()
    if author_search:
        # "けにお" が前後や間にある場合も考慮した正規表現パターン
        pattern = f'.*{author_search}.*'
        novels_list = novels_list.filter(author__nickname__iregex=pattern)

    # 作者名での選択
    author_select = request.GET.get('author_select', '').strip()
    if author_select:
        novels_list = novels_list.filter(author__id=author_select)
    logger.debug(f"Selected author ID: {author_select}")


    # イトルでの曖昧検索
    title_search = request.GET.get('title_search', '').strip()
    if title_search:
        novels_list = novels_list.filter(title__icontains=title_search)

    # タイトルの選択
    title_select = request.GET.get('title_select', '').strip()
    if title_select:
        novels_list = novels_list.filter(id=title_select)

    # 文字数の範囲
    min_word_count = request.GET.get('word_count_min', None)
    if min_word_count:
        min_word_count = int(min_word_count)  # 文字列を整数に変換
        novels_list = novels_list.filter(word_count__gte=min_word_count)

    max_word_count = request.GET.get('word_count_max', None)
    if max_word_count:
        max_word_count = int(max_word_count)  # 文字列を整数に変換
        novels_list = novels_list.filter(word_count__lte=max_word_count)

    # ジャンルでのフィルタリング
    genre = request.GET.get('genre', '').strip()
    if genre:
        novels_list = novels_list.filter(genre=genre)

    # タイトルでの索
    search = request.GET.get('search', '').strip()
    if search:
        novels_list = novels_list.filter(title__icontains=search)

    # 年の範囲でのフィルタリング
    post_date_from_year = request.GET.get('post_date_from_year', None)
    if post_date_from_year:
        novels_list = novels_list.filter(published_date__year__gte=post_date_from_year)

    post_date_to_year = request.GET.get('post_date_to_year', None)
    if post_date_to_year:
        novels_list = novels_list.filter(published_date__year__lte=post_date_to_year)

    # その他の処理...

    # 並替え
    logger.debug(f"Sort by: {sort_by}")  # sort_byの値を確認
    logger.debug(f"Order: {order}")  # orderの値を確認
    logger.debug(f"SQL Query: {str(novels_list.query)}")  # 実行されるSQLクエリを確認


    if order == 'asc':
        novels_list = novels_list.order_by(sort_by)
    else:
        novels_list = novels_list.order_by('-' + sort_by)

    # 現在の並び替え状態に基づいての状態を決定
    next_order = 'asc' if order == 'desc' else 'desc'

    # SSR用にはモデルインスタンスのまま（.values()は使わない）

# 遅延読み込みの手続き・・かっこいいが。

    # Paginatorを設定
    paginator = Paginator(novels_list, 10)  # 1ページあたり10項目を表示
    page_number = request.GET.get('page', 1)  # デフォルトは1ページ目
    page_obj = paginator.get_page(page_number)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Ajax用にデータを整形
        novels = []
        for novel in page_obj.object_list:
            from accounts.templatetags.user_display import display_name
            novels.append({
                'id': novel.id,
                'title': novel.title,
                'word_count': novel.word_count,
                'author_id': novel.author.id,
                'author_nickname': display_name(novel.author),  # display_nameフィルター使用
                'published_date': novel.published_date.strftime("%Y年%m%d日"),
                'genre': novel.genre,
                'event': novel.event,
                'same_title_event_month': novel.same_title_event_month,
                'is_first_post': novel.is_first_post,
                'likes_count': novel.likes_count,
                'comments_count': novel.comments_count,
            })
        return JsonResponse({'novels': novels, 'has_next': page_obj.has_next()})

    # 非Ajaxリクエストの場合の処理
    context = {
        'novels': page_obj.object_list,
        'page_obj': page_obj,  # Paginatorオブジェクトをコンテキストに追加
        'sort_by': sort_by,
        'order': order,
        'next_order': next_order,
        'search': search,
        'genre': genre,  # ユーザーが選択したジャンルをコンテキストに追加
        'genre_choices': Novel.GENRE_CHOICES,
        'post_date_from_year': post_date_from_year,
        'post_date_to_year': post_date_to_year,
        'months': months,  # のリストをンテキトに追加
        'years': years,
        'author_choices': author_choices,
        'title_choices': title_choices,
        'post_date_from_year': post_date_from_year,
        'post_date_to_year': post_date_to_year,
    }

    return render(request, 'novels/index.html', context)



# 真リスト
from .models import GENRE_CHOICES
from django.db.models import F

User = get_user_model()  # カスタムユーザーモデルを取得

def novels_paginated(request):
    # デフォルト値を設定
    title_initial = request.GET.get('title_initial', 'all')
    char_count_min = request.GET.get('char_count_min', 0)
    char_count_max = request.GET.get('char_count_max', 100000)  # 適切なデフォルト最大値を設定

    # クエリを最適化して必要なフィールドのみを取得
    novels_list = Novel.objects.filter(
        status='published'
    ).select_related(
        'author'
    ).annotate(
        likes_count=Count('likes', distinct=True),
        comments_count=Count('comments', distinct=True)
    )

    # 🔥 祭り小説を「執筆期間中」かつ「予想期間前」のみ除外（ゲームの公平性のため）
    # 公開後は普通に一覧に表示される（予想期間・結果発表期間・祭り終了後も表示）
    today = timezone.localtime(timezone.now()).date()  # 🔥 JST日付取得
    active_games = MaturiGame.objects.filter(maturi_end_date__gte=today)
    for game in active_games:
        # 予想期間が始まっていない AND まだ執筆期間中の場合のみ除外
        if not game.is_prediction_period() and game.start_date and today <= game.end_date:
            novels_list = novels_list.exclude(maturi_games=game)

    # タイトル検索
    title_search = request.GET.get('title_search')
    if title_search:
        novels_list = novels_list.filter(title__icontains=title_search)

    # フィルタリング処理
    author_search = request.GET.get('author_search')
    if author_search:
        novels_list = novels_list.filter(author__nickname__icontains=author_search)

    # 作者名選択
    author_select = request.GET.get('author_select')
    if author_select:
        novels_list = novels_list.filter(author_id=author_select)

    # タイトルイニシャル
    title_initial = request.GET.get('title_initial')
    if title_initial:
        if title_initial != 'all':
            novels_list = novels_list.filter(title__istartswith=title_initial)

    # ジャンル
    genre = request.GET.get('genre')
    if genre:
        novels_list = novels_list.filter(genre=genre)

    # 文字数フィルター
    char_count_min = request.GET.get('char_count_min')
    if char_count_min:
        novels_list = novels_list.filter(word_count__gte=int(char_count_min))

    char_count_max = request.GET.get('char_count_max')
    if char_count_max:
        novels_list = novels_list.filter(word_count__lte=int(char_count_max))

    # ソート処理
    sort_param = request.GET.get('sort', '-published_date')
    if sort_param.startswith('-'):
        sort_field = sort_param[1:]
        novels_list = novels_list.order_by(F(sort_field).desc())
    else:
        novels_list = novels_list.order_by(F(sort_param).asc())

    # values()はソート後に適用
    # 🔥 original_author__nickname も取得（祭り小説の予想期間終了後に正しい作者名を表示するため）
    novels_list = novels_list.values(
        'id', 'title', 'word_count',
        'author_id', 'author__nickname',
        'original_author__nickname', 'event',  # 🔥 original_author追加
        'published_date', 'genre',
        'same_title_event_month', 'is_first_post',
        'likes_count', 'comments_count'
    )

    # ページネーション（先にページネーションしてからデータ変換）
    paginator = Paginator(novels_list, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # 🔥 祭り小説で予想期間終了後は正しい作者名を表示 & イベント欄に「祭り」を設定
    novels_data = []
    for novel in page_obj.object_list:
        novel_dict = dict(novel)  # QuerySetの辞書をコピー
        # 🔥 original_author がある場合、祭りゲームとの関連をチェック（eventフィールドは使わない）
        if novel_dict.get('original_author__nickname'):
            # この小説の祭りゲームを取得して予想期間終了かチェック
            novel_obj = Novel.objects.filter(id=novel_dict['id']).first()
            if novel_obj:
                maturi_game = novel_obj.maturi_games.first()
                if maturi_game:
                    # 🔥 祭り小説のイベント欄に「祭り」を設定
                    novel_dict['event'] = '祭り'
                    # 予想期間終了後は本当の作者名を表示
                    if today > maturi_game.prediction_end_date:
                        novel_dict['author__nickname'] = novel_dict['original_author__nickname']
        novels_data.append(novel_dict)

    # タイトル一覧を取得（タイトル選択ドロップダウン用）
    title_choices = Novel.objects.filter(status='published').values_list('id', 'title').distinct().order_by('title')

    # コンテキストの設定
    context = {
        'page_obj': page_obj,
        'novels': novels_data,  # 🔥 変換後のデータを使用
        'sort': sort_param,
        'genre_choices': GENRE_CHOICES,
        'authors_list': User.objects.filter(is_active=True),
        'genre': genre,
        'char_count_min': char_count_min,
        'char_count_max': char_count_max,
        'title_search': title_search,
        'author_search': author_search,
        'author_select': author_select,
        'title_initial': title_initial,
        'years': range(1800, 2101),  # 1800年から2100年までの年リスト
        'title_choices': title_choices  # タイトル選択用リスト
    }

    return render(request, 'novels/novels_paginated.html', context)

User = get_user_model()  # この行も追加

@login_required
def post_comment(request, novel_id):
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':  # ここを変更
        # N+1対策：select_related追加
        novel = get_object_or_404(Novel.objects.select_related('author'), id=novel_id)
        form = CommentForm(request.POST)
        
        if form.is_valid():
            comment = form.save(commit=False)
            comment.novel = novel
            comment.author = request.user
            
            # 祭り関連の処理
            if 'maturi_game_id' in request.POST:
                maturi_game = get_object_or_404(MaturiGame, id=request.POST['maturi_game_id'])
                comment.maturi_game = maturi_game
                comment.is_maturi_comment = True
                
                if 'original_commenter_id' in request.POST:
                    original_commenter = get_object_or_404(User, id=request.POST['original_commenter_id'])
                    comment.original_commenter = original_commenter
            
            comment.is_read = True if novel.author == request.user else False
            comment.save()

            # 🔥 祭り小説の予想期間中はコメント作者を匿名にする
            is_prediction_period = False
            if hasattr(novel, 'maturi_games') and novel.maturi_games.exists():
                for game in novel.maturi_games.all():
                    if not game.is_author_revealed and game.is_prediction_period():
                        is_prediction_period = True
                        break

            # 🔥 予想期間中は「謎の読者」として返す
            if is_prediction_period:
                response_data = {
                    'success': True,
                    'comment': {
                        'author': '👻 謎の読者',
                        'author_id': None,
                        'author_color': '#888888',
                        'content': comment.content,
                        'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M'),
                        'is_anonymous': True
                    }
                }
            else:
                response_data = {
                    'success': True,
                    'comment': {
                        'author': comment.author.nickname,
                        'author_id': comment.author.id,
                        'author_color': comment.author.comment_color,
                        'content': comment.content,
                        'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M')
                    }
                }
            
            # 祭り関連のレスポンスデータ
            if comment.is_maturi_comment:
                response_data['comment'].update({
                    'is_maturi_comment': True,
                    'maturi_game_id': comment.maturi_game.id,
                    'original_commenter_nickname': comment.original_commenter.nickname if comment.original_commenter else None
                })
            
            return JsonResponse(response_data)
        else:
            return JsonResponse({'success': False, 'error': form.errors})
    return JsonResponse({'success': False, 'error': 'Invalid request'})



# @login_required
# def mark_all_as_read(request):
#     """すべてのコメントを既読にする関数を追加"""
#     Comment.objects.filter(
#         novel__author=request.user,
#         is_read=False
#     ).update(is_read=True)
#     return JsonResponse({'success': True})

@require_POST
def toggle_comment_read(request, comment_id):
    # N+1対策：select_related追加
    comment = get_object_or_404(Comment.objects.select_related('novel__author', 'novel__original_author', 'author'), id=comment_id)
    if request.user != comment.novel.author and request.user != comment.novel.original_author:
        return JsonResponse({'success': False, 'error': '権限がありません'})

    data = json.loads(request.body)
    comment.is_read = data.get('is_read', False)
    comment.save()

    # 未読コメントのある小説を再取得（N+1対策：select_related追加）
    novels = Novel.objects.filter(
        Q(author=request.user) | Q(original_author=request.user),
        comments__is_read=False,
        comments__author__isnull=False
    ).exclude(
        comments__author=request.user
    ).select_related('author').annotate(
        unread_count=Count('comments', filter=Q(comments__is_read=False))
    ).distinct()

    # context_processors.pyと同じ方法で色を計算
    novels_with_unread = []
    for i, novel in enumerate(novels):
        logger.debug(f"\nDEBUG: Novel ID {novel.id} assigned color {i % 10}")  # デバッグ出力
        novels_with_unread.append({
            'id': novel.id,
            'unread_count': novel.unread_count,
            'color_index': i % 10  # インデックス順に色を割り当て
        })

    return JsonResponse({
        'success': True,
        'is_read': comment.is_read,
        'novels_with_unread': novels_with_unread
    })

# def home(request):
#     # 公開済の小説を10件取得
#     latest_novels = Novel.objects.filter(
#         status='published'
#     ).select_related(
#         'author'
#     ).order_by(
#         '-published_date'
#     )[:10]

#     # デバッグ用のログ追加
#     current_maturi_game = MaturiGame.find_current_games().first()


#     context = {
#         'latest_novels': latest_novels,
#         'current_maturi_game': current_maturi_game,
#     }
#     return render(request, 'home/home.html', context)

class NovelListView(ListView):
    model = Novel
    template_name = 'novels/novels_list.html'
    context_object_name = 'novels'

    def get_queryset(self):
        # デフォルトで公開日の降順（新しい順）
        queryset = Novel.objects.filter(
            status='published',
            published_date__isnull=False
        ).select_related('author').order_by('-published_date')

        # 🔥 祭り小説を「執筆期間中」かつ「予想期間前」のみ除外（ゲームの公平性のため）
        # 公開後は普通に一覧に表示される（予想期間・結果発表期間・祭り終了後も表示）
        today = timezone.localtime(timezone.now()).date()  # 🔥 JST日付取得
        active_games = MaturiGame.objects.filter(maturi_end_date__gte=today)
        for game in active_games:
            # 予想期間が始まっていない AND まだ執筆期間中の場合のみ除外
            if not game.is_prediction_period() and game.start_date and today <= game.end_date:
                queryset = queryset.exclude(maturi_games=game)

        # GETパラメータからソート条件を取得
        sort_by = self.request.GET.get('sort_by', 'published_date')
        order = self.request.GET.get('order', 'desc')

        # ソート順の設定
        if order == 'asc':
            sort_by = sort_by
        else:
            sort_by = f'-{sort_by}'

        # ソート条件に応じてクエリを変更
        if sort_by:
            queryset = queryset.order_by(sort_by)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['sort_by'] = self.request.GET.get('sort_by', 'published_date')
        context['order'] = self.request.GET.get('order', 'desc')
        return context

class NovelPaginatedView(ListView):
    model = Novel
    template_name = 'novels/novels_paginated.html'
    context_object_name = 'novels'
    paginate_by = 10

    def get_queryset(self):
        # デフォルトで公開日の降順（新しい順）
        queryset = Novel.objects.filter(
            status='published',
            published_date__isnull=False
        ).select_related('author')

        # 🔥 祭り小説を「執筆期間中」かつ「予想期間前」のみ除外（ゲームの公平性のため）
        # 公開後は普通に一覧に表示される（予想期間・結果発表期間・祭り終了後も表示）
        today = timezone.localtime(timezone.now()).date()  # 🔥 JST日付取得
        active_games = MaturiGame.objects.filter(maturi_end_date__gte=today)
        for game in active_games:
            # 予想期間が始まっていない AND まだ執筆期間中の場合のみ除外
            if not game.is_prediction_period() and game.start_date and today <= game.end_date:
                queryset = queryset.exclude(maturi_games=game)

        # フィルタリング条件の適用
        author_search = self.request.GET.get('author_search')
        if author_search:
            queryset = queryset.filter(author__nickname__icontains=author_search)

        # その他のフィルタリング条件も同様に適用...

        # ソート条件の適用
        sort_by = self.request.GET.get('sort', '-published_date')
        queryset = queryset.order_by(sort_by)

        return queryset

def novel_choice(request):
    if not request.user.is_authenticated:
        return redirect('accounts:login')

    # 作成中の小説を取得（N+1対策：select_related追加）
    drafts = Novel.objects.filter(
        author=request.user,
        status='draft'
    ).select_related('author').order_by('-updated_at')

    # 公開予定の小説を取得（祭りの小説など）（N+1対策：select_related, prefetch_related追加）
    scheduled = Novel.objects.filter(
        author=request.user,
        status='scheduled'
    ).select_related('author').prefetch_related('maturi_games').order_by('maturi_games__prediction_start_date')

    # 公開済みの小説を取得（N+1対策：select_related追加）
    published = Novel.objects.filter(
        author=request.user,
        status='published'
    ).select_related('author').order_by('-published_date')

    # 現在開催中の祭りを取得
    current_maturi_game = MaturiGame.find_current_games().first()
    
    return render(request, 'novel_choice.html', {
        'drafts': drafts,
        'scheduled': scheduled,
        'published': published,
        'current_maturi_game': current_maturi_game
    })
