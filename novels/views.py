from django.core.paginator import Paginator
from django.shortcuts import render, redirect
from .forms import NovelForm
from .models import Novel  # Novelモデルをインポート
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.http import HttpResponseRedirect
from .models import Novel, Like
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .forms import CommentForm
from .models import Comment  # Commentモデルをインポート
from django.views.decorators.csrf import csrf_exempt
from django.http import Http404
import json
from django.http import HttpResponseForbidden
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.views.generic import ListView
from game_maturi.models import MaturiGame  # この行を追加

# from .context_processors import get_unread_comments_count  # これを追加

import logging  # これを追加
from django.urls import reverse_lazy  # これを追加

from django.core.paginator import Paginator
from django.shortcuts import render, redirect
from .forms import NovelForm
from .models import Novel, Like, Comment  # Novel, Like, Commentモデルをインポート
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseRedirect, JsonResponse, Http404
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages  # これを追加！
import json
import logging
from django.db.models import Q
from django.db.models import Count  # これを追加

# ログ設定
logger = logging.getLogger(__name__)
handler = logging.FileHandler('novel_site.log')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

@login_required
def post_or_edit_novel(request, novel_id=None):
    novel = None
    edit_mode = False

    # POSTリクエストからnovelIdを優先的に取得し、なければURLパラメータから取得
    novel_id = request.POST.get('novelId', novel_id)

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
            novel.delete()
            return redirect('accounts:view_profile')  # プロファイルページにリダイレクト
        
        if action == 'rest':
            return redirect('accounts:view_profile')

        if form.is_valid():
            saved_novel = form.save(commit=False)
            saved_novel.word_count = len(form.cleaned_data['content'].split())
            
            if action == 'publish':
                saved_novel.status = 'published'
            elif action == 'draft':
                saved_novel.status = 'draft'
            
            saved_novel.save()
            form.save_m2m()

            if action == 'publish':
                return redirect(reverse_lazy('novels:novels_paginated'))
            else:
                return redirect('novels:edit_novel', novel_id=saved_novel.id)
        else:
            print("Form errors:", form.errors)
            return render(request, 'novels/post_or_edit_novel.html', {'form': form, 'novel': novel, 'edit': edit_mode})
    else:
        form = NovelForm(instance=novel)
        return render(request, 'novels/post_or_edit_novel.html', {'form': form, 'novel': novel, 'edit': edit_mode})


import logging
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from .models import Novel

# ログ設定
logger = logging.getLogger(__name__)
handler = logging.FileHandler('novel_site.log')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

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
            novel = get_object_or_404(Novel, pk=novel_id, author=request.user)
        else:
            novel = Novel(author=request.user)

        novel.title = title
        novel.content = content
        novel.initial = initial
        novel.genre = genre
        novel.word_count = len(content.split())
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


from django.http import JsonResponse
from django.core.paginator import Paginator
from .models import Novel
from django.shortcuts import render

from django.db.models import Value, CharField
from django.db.models.functions import Coalesce

from django.db.models import Value, CharField
from django.db.models.functions import Coalesce
import logging

logger = logging.getLogger(__name__)
from django.db.models import Value, CharField
from django.db.models.functions import Coalesce

from django.http import JsonResponse

from django.core.paginator import Paginator
from django.shortcuts import render
from .models import Novel
from django.db.models import Count
from django.contrib.auth.decorators import login_required
import logging
logger = logging.getLogger(__name__)

from accounts.models import User  # accounts アプリケーションから User モデルをインポート
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Novel
from django.core.paginator import Paginator
from django.db.models import Count
from django.http import JsonResponse
import datetime
from .models import Novel
# この行を追加
from accounts.models import User
# from .utils import get_user_info  # get_user_info 関数をインポート





from django.db.models import Count






@login_required
def delete_novel(request, novel_id):
    novel = get_object_or_404(Novel, pk=novel_id, author=request.user)  # 小説を取得
    novel.delete()  # 小説を削除
    return HttpResponseRedirect(reverse('accounts:view_profile'))  # プロファイルページにイレト

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

from django.urls import reverse
from django.utils import timezone

from django.http import HttpResponse
import logging
logger = logging.getLogger(__name__)

def novel_detail(request, novel_id):
    """
    小説詳細ページのメイン処理
    Template: novels/detail.html
    
    関連する処理：
    - コメント投稿: post_comment関数で処理 (/novels/<novel_id>/comment/)
      ※ 祭り小説のコメント処理や、コメントの既読/未読管理もpost_comment関数で実装
    """
    print("="*50)
    print(f"1. リクエストされたURL: {request.path}")
    print(f"2. novel_id: {novel_id}")
    
    novel = get_object_or_404(Novel.objects.select_related('author'), id=novel_id)
    print(f"3. 取得された小説: ID={novel.id}, タイトル={novel.title}")

    # 祭り作品の判定をより詳細に
    print("\n==== 祭り作品判定 ====")
    print(f"小説ID: {novel.id}")
    print(f"hasattr(novel, 'maturi_games'): {hasattr(novel, 'maturi_games')}")
    if hasattr(novel, 'maturi_games'):
        print(f"novel.maturi_games.exists(): {novel.maturi_games.exists()}")
    print(f"original_author_id: {novel.original_author_id if hasattr(novel, 'original_author_id') else 'なし'}")
    print("=====================\n")
   

    print("\n==== ユーザー照合 ====")
    print(f"小説ID: {novel.id}")
    print(f"小説タイトル: {novel.title}")
    print(f"作者ID: {novel.author.id}")
    print(f"作者のメール: {novel.author.email}")
    print(f"ログインユーザーID: {request.user.id if request.user.is_authenticated else 'None'}")
    print(f"ログインユーザーメール: {request.user.email if request.user.is_authenticated else 'None'}")
    print("==================\n")

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
        print(f"リダイレクト前の状態: novel.status={novel.status}, user_authenticated={request.user.is_authenticated}, user={request.user}, novel_author={novel.author}")
        messages.error(request, f'{novel.get_status_display()}の小説は、作者本人のみ閲覧できません。')
        return redirect('novels:novels_paginated')

    # 祭り作品かどうかの判定
    is_maturi = hasattr(novel, 'maturi_games') and novel.maturi_games.exists()
    print(f"祭り作品判定: {is_maturi}")
    if is_maturi:
        print("祭り小説の詳細情報を表示")
        # 祭り小説の詳細情報を表示するための追加デバッグ
        maturi_games = novel.maturi_games.all()
        for game in maturi_games:
            print(f"祭りゲームID: {game.id}, タイトル: {game.title}")
            print(f"is_author_revealed: {game.is_author_revealed}")
            print(f"prediction_end_date: {game.prediction_end_date}")
            now = timezone.now().date()
            print(f"現在時刻: {now}")
            print(f"予想期間終了？: {now > game.prediction_end_date}")

    # 同イトル作品かどうかの判定
    is_same_title = novel.is_same_title_game if hasattr(novel, 'is_same_title_game') else False

    # 編集権限確認（ログインユーザーのみ）
    can_edit = False
    if request.user.is_authenticated:
        print("\n==== 編集権限チェック ====")
        print(f"リクエストユーザー: {request.user.id} - {request.user.email}")
        print(f"小説の作者: {novel.author.id} - {novel.author.email}")
        print(f"オリジナル作者: {novel.original_author_id if hasattr(novel, 'original_author_id') else 'なし'}")
        
        if is_maturi:
            # 祭り作品の場合、作者またはオリジナルの作者
            can_edit = (request.user == novel.author or 
                       novel.original_author_id == request.user.id)
        else:
            # 通常作品の場合、作者または original_author_id が一致する場合
            can_edit = (request.user == novel.author or 
                       (hasattr(novel, 'original_author_id') and 
                        novel.original_author_id == request.user.id))
        
        print(f"編集権限: {can_edit}")
        print("="*50)

    # 未読コメント情報を取得
    latest_unread_novels = []
    if request.user.is_authenticated:
        latest_unread_novels = Novel.objects.filter(
            author=request.user,
            comments__is_read=False,
            comments__author__isnull=False
        ).distinct().annotate(
            unread_count=Count(
                'comments',
                filter=Q(comments__is_read=False) & ~Q(comments__author=request.user),
                distinct=True
            )
        )
        
        # デバッグ用：実際のSQL文を表示
        print("SQL Query:", latest_unread_novels.query)
        
        # デバッグ用：各コメントの詳細を表示
        for unread_novel in latest_unread_novels:
            comments = Comment.objects.filter(
                novel=unread_novel,
                is_read=False
            ).exclude(author=request.user)
            print(f"Novel {unread_novel.id} unread comments:")
            for comment in comments:
                print(f"- Comment {comment.id}: by {comment.author}, content: {comment.content}")
        
            print(f"\n5. 祭り判定結果: {is_maturi}")
    if is_maturi:
        print("   祭り小説の詳細:")
        print(f"   - maturi_games: {novel.maturi_games.all()}")
    
    # コンテキスト作成直前の状態確認
    print("\n6. コンテキスト作成直前の小説情報:")
    print(f"   - ID: {novel.id}")
    print(f"   - タイトル: {novel.title}")
    
    # コンテキスト作成直前にデバッグ情報を追加
    print("\n==== コンテキスト変数 ====")
    print(f"user: {request.user}")
    print(f"can_edit: {can_edit}")
    print(f"hide_edit_button: {False}")
    
    # コメント情報のデバッグ出力を追加
    print("\n==== コメント情報 ====")
    for comment in comments_list:
        if comment.author:  # 作者が存在する場合のみ
            print(f"作者: {comment.author.nickname}")
            print(f"作者の色: {comment.author.comment_color}")
        else:
            print(f"作者: 退会したユーザー")
            print(f"作者の色: #cccccc")  # デフォルトのグレー色

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
        'hide_edit_button': False  # これを追加
    }
    print(f"4. レンダリング前のcontext['novel']: ID={context['novel'].id}, タイトル={context['novel'].title}")
    print("="*50)
    
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
        comment = get_object_or_404(Comment, id=comment_id, novel__author=request.user)
        data = json.loads(request.body)
        comment.is_read = data.get('is_read', False)
        comment.save()

        # キャッシュをクリア
        cache_key = f'total_unread_comments_{request.user.id}'
        cache.delete(cache_key)
        
        # 未読コメントのある小説の情報を更新して返す
        novels_with_unread = Novel.objects.filter(
            author=request.user
        ).annotate(
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
        print("サーバー側での未読カウント:")
        for novel in novels_with_unread:
            print(f"Novel {novel['id']}: {novel['unread_count']} unread comments")

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
        updated = Comment.objects.filter(
            id__in=comment_ids,
            novel__author=request.user  # 自分の小説のコメントのみ
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





from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Novel, Comment

import logging
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from .models import Novel, Comment

# ロガーを設定する
logger = logging.getLogger(__name__)

@login_required
def check_unread_comments(request, novel_id):
    """現在の小説以外に未読コメンがある小説を探す"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'ログインが必要です'}, status=403)

    # デバッグ情報
    logger.debug(f"Checking unread comments for novel {novel_id}")
    logger.debug(f"Current user: {request.user.username}")

    # 現在の小説以外で、未読コメントがある小説を探す
    next_novel = Novel.objects.filter(
        author=request.user  # ユーザーが書いた小説
    ).exclude(
        id=novel_id  # 現在の小説を除外
    ).annotate(
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
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

@login_required
def load_more_comments(request, novel_id):
    page = request.GET.get('page')
    comments_list = Comment.objects.filter(novel_id=novel_id).order_by('-created_at')
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


from django.http import JsonResponse
from django.urls import reverse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .models import Novel

@login_required
@require_POST
def unpublish_novel(request, novel_id):
    novel = get_object_or_404(Novel, pk=novel_id)
    
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
    novels_list = Novel.objects.select_related('author').prefetch_related(
        'comments__author',  # コメントとその作者を事前に取得
        'likes'  # いいねの情報を事前に取得
    ).annotate(
        likes_count=Count('likes'),
        comments_count=Count('comments')
    ).filter(status='published').order_by('-published_date')  # 投稿日の降順に並替える

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
    print("Selected author ID:", author_select)


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
    print("Sort by:", sort_by)  # sort_byの値を確認
    print("Order:", order)  # orderの値を確認
    print("SQL Query:", str(novels_list.query))  # 実行されるSQLクエリを確認


    if order == 'asc':
        novels_list = novels_list.order_by(sort_by)
    else:
        novels_list = novels_list.order_by('-' + sort_by)

    # 現在の並び替え状態に基づいての状態を決定
    next_order = 'asc' if order == 'desc' else 'desc'



# 遅延読み込みの手続き・・かっこいいが。

    # Paginatorを設定
    paginator = Paginator(novels_list, 10)  # 1ページあたり10項目を表示
    page_number = request.GET.get('page', 1)  # デフォルトは1ページ目
    page_obj = paginator.get_page(page_number)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        novels = list(page_obj.object_list.values(
            'id', 'title', 'word_count', 'author__id', 'author__nickname', 'published_date', 'genre', 'likes_count', 'comments_count'
        ))
        
        for novel in novels:
            novel['published_date'] = novel['published_date'].strftime("%Y年%m%d日")
            novel['author_nickname'] = novel.pop('author__nickname')
            novel['author_id'] = novel.pop('author__id')
            novel['title'] = novel['title']
            novel['genre'] = novel['genre']
            novel['likes_count'] = novel['likes_count']
            novel['comments_count'] = novel['comments_count']
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
from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Count  # ここを正！
from django.contrib.auth import get_user_model
from .models import Novel, GENRE_CHOICES
from django.db.models import Count, F, Q 

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
    novels_list = novels_list.values(
        'id', 'title', 'word_count', 
        'author_id', 'author__nickname',
        'published_date', 'genre',
        'likes_count', 'comments_count'
    )

    # ページネーション
    paginator = Paginator(novels_list, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # コンテキストの設定
    context = {
        'page_obj': page_obj,
        'novels': page_obj.object_list,
        'sort': sort_param,
        'genre_choices': GENRE_CHOICES,
        'authors_list': User.objects.filter(is_active=True).values('id', 'nickname'),
        'genre': genre,
        'char_count_min': char_count_min,
        'char_count_max': char_count_max,
        'title_search': title_search,
        'author_search': author_search,
        'author_select': author_select,
        'title_initial': title_initial
    }

    return render(request, 'novels/novels_paginated.html', context)

User = get_user_model()  # この行も追加

@login_required
def post_comment(request, novel_id):
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':  # ここを変更
        novel = get_object_or_404(Novel, id=novel_id)
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
    comment = get_object_or_404(Comment, id=comment_id)
    if request.user != comment.novel.author:
        return JsonResponse({'success': False, 'error': '権限がありません'})

    data = json.loads(request.body)
    comment.is_read = data.get('is_read', False)
    comment.save()

    # 未読コメントのある小説を再取得
    novels = Novel.objects.filter(
        author=request.user,
        comments__is_read=False,
        comments__author__isnull=False
    ).exclude(
        comments__author=request.user
    ).annotate(
        unread_count=Count('comments', filter=Q(comments__is_read=False))
    ).distinct()

    # context_processors.pyと同じ方法で色を計算
    novels_with_unread = []
    for i, novel in enumerate(novels):
        print(f"\nDEBUG: Novel ID {novel.id} assigned color {i % 10}")  # デバッグ出力
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
    
    # 作成中の小説を取得
    drafts = Novel.objects.filter(
        author=request.user,
        status='draft'
    ).order_by('-updated_at')
    
    # 公開予定の小説を取得（祭りの小説など）
    scheduled = Novel.objects.filter(
        author=request.user,
        status='scheduled'
    ).order_by('maturi_games__prediction_start_date')
    
    # 公開済みの小説を取得
    published = Novel.objects.filter(
        author=request.user,
        status='published'
    ).order_by('-published_date')

    # 現在開催中の祭りを取得
    current_maturi_game = MaturiGame.find_current_games().first()
    
    return render(request, 'novel_choice.html', {
        'drafts': drafts,
        'scheduled': scheduled,
        'published': published,
        'current_maturi_game': current_maturi_game
    })
