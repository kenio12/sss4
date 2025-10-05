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

# Create your views here.

def game_maturi_top(request, game_id=None):
    context = {}
    now = timezone.now()

    # 現在のゲームを取得
    if game_id:
        try:
            current_game = MaturiGame.objects.prefetch_related(
                'phrases',
                'maturi_novels',
                'entrants'
            ).get(id=game_id)
            
            # デバッグ情報を追加
            print("\n=== Debug Output ===")
            print(f"Game ID: {current_game.id}")
            print(f"Game Title: {current_game.title}")
            print(f"Phrases exist?: {current_game.phrases.exists()}")
            print(f"All phrases: {list(current_game.phrases.all())}")
            print("=== End Debug Output ===\n")
            
        except MaturiGame.DoesNotExist:
            raise Http404("Game does not exist")
    else:
        current_game = MaturiGame.find_current_game()

    if current_game:
        # 最後に終了したゲームを取得
        last_finished_game = MaturiGame.objects.filter(
            maturi_end_date__lt=now
        ).order_by('-maturi_end_date').first()
        
        context['last_finished_game'] = last_finished_game  # これを追加
        
        print("\n=== Debug Output ===")
        print(f"Current Game: {current_game.id}")
        print(f"User: {request.user}")
        
        # まず、ユーザーがゲームに参加しているかどうかを確認
        is_user_entered = False
        if request.user.is_authenticated:
            is_user_entered = current_game.entrants.filter(id=request.user.id).exists()

        # 関連データを一度に取得
        current_game = MaturiGame.objects.select_related(
            'dummy_author'
        ).prefetch_related(
            'maturi_novels',
            'phrases',
            'entrants'
        ).get(id=current_game.id)

        # 公開済みの小説を取得
        novels = list(current_game.maturi_novels.filter(
            status='published'
        ).select_related('original_author', 'author'))
        random.shuffle(novels)

        # 参���者リストを取得
        active_authors = list(current_game.entrants.all())
        random.shuffle(active_authors)

        # 作者ごとの統計を計算
        author_stats = {}
        for author in active_authors:
            author_novel_count = len([
                novel for novel in novels 
                if novel.original_author_id == author.id
            ])
            author_stats[author.id] = {
                'total_novels': author_novel_count,
                'predicted_count': 0  # 初期値として0を設定
            }

        # ユーザーの予想情報を取得
        user_predictions = []
        novel_predictions = {}
        
        if request.user.is_authenticated:
            predictions = GamePrediction.objects.filter(
                predictor=request.user,
                maturi_game=current_game
            ).select_related('novel', 'predicted_author')

            for prediction in predictions:
                user_predictions.append(prediction)
                novel_predictions[prediction.novel_id] = {
                    'id': prediction.id,
                    'predicted_author': {
                        'id': prediction.predicted_author.id,
                        'nickname': prediction.predicted_author.nickname
                    },
                    'novel': {
                        'id': prediction.novel.id,
                        'title': prediction.novel.title
                    }
                }

        # コンテキストを更新する前に内容を確認
        context.update({
            'game': current_game,
            'novels': novels,
            'active_authors': active_authors,
            'author_stats': author_stats,
            'novel_predictions': novel_predictions,
            'predictions': user_predictions,
            'is_user_entered': is_user_entered,
        })
        
        print("\nContext keys:", context.keys())
        print("Number of predictions:", len(user_predictions))
        print("Number of novel_predictions:", len(novel_predictions))
        print("=== End Debug Output ===\n")

        # 重複している context.update を削除し、一つにまとめる
        context.update({
            'is_writing_period': current_game.is_writing_period(),
            'is_prediction_period': current_game.is_prediction_period(),
            'is_novel_publish_period': current_game.is_novel_publish_period(),
            'is_user_entered': is_user_entered,
        })

        # 予想期間が終了している場合は結果も表示
        if current_game.is_prediction_period_finished():
            add_prediction_results_to_context(current_game, context)

        # 参加者と予想統計情報を準備
        participants_stats = []
        for author in active_authors:
            stats = {
                'correct': 0,
                'total': 0,
                'accuracy': 0.0
            }
            
            # この参加者の予想を取得
            predictions = GamePrediction.objects.filter(
                predictor=author,
                maturi_game=current_game
            )
            
            stats['total'] = predictions.count()
            stats['correct'] = predictions.filter(
                predicted_author=models.F('novel__original_author')
            ).count()
            
            if stats['total'] > 0:
                stats['accuracy'] = (stats['correct'] / stats['total']) * 100
            
            participants_stats.append((author, stats))
        
        # 正解率で降順ソート
        participants_stats.sort(key=lambda x: (-x[1]['accuracy'], -x[1]['correct']))
        
        context.update({
            'participants': participants_stats,
        })

    return render(request, 'game_maturi/game_maturi_top.html', context)

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
        action = request.POST.get('action')

        # ここで先にformを定義
        if novel and novel.status == 'published':
            form_data['status'] = 'published'
            form = MaturiNovelForm(form_data, instance=novel)
        else:
            form = MaturiNovelForm(form_data, instance=novel, is_writing_period=is_writing_period)
        
        # 頭文字のふりがなのチェック
        if not form_data.get('initial', '').strip():
            messages.error(request, 'タイトルの頭文字のふりがなを入力してください！')
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
        
        if form.is_valid():
            saved_novel = form.save(commit=False)
            
            # 祭り作家を取得または作成
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
            
            # 以降は既存のコード
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
                saved_novel.genre = '祭り'
                saved_novel.is_public = False
                saved_novel.save()
                messages.success(request, f'小説を予約公開しました。{current_game.prediction_start_date.strftime("%Y年%m月%d日")}に自動的に公開されます。')
                return redirect('accounts:view_profile')
            elif action in ['publish', 'edit_published']:
                saved_novel.status = 'published'
                saved_novel.genre = '祭り'
                saved_novel.is_public = True
            elif action in ['draft', 'rest']:
                saved_novel.status = 'draft'
                saved_novel.is_public = False
            elif action == 'cancel_schedule':  # 予約公開取り消しの理を追加
                saved_novel.status = 'draft'  # ステータスを下書きに戻す
                messages.success(request, '予約公開を取り消しました。')
            
            saved_novel.save()
            
            # 祭りゲームとの関連付け
            if current_game and not current_game.maturi_novels.filter(id=saved_novel.id).exists():
                current_game.maturi_novels.add(saved_novel)
                current_game.save()

            # リダイレクト処理
            if action == 'rest':
                messages.success(request, '小説を保存して休憩します。')
                return redirect('accounts:view_profile')
            elif action == 'draft':
                messages.success(request, '小説が保存されました！')
                return redirect('game_maturi:post_or_edit_maturi_novel', novel_id=saved_novel.id)
            else:
                messages.success(request, '小説が保存されました！')
                return redirect('novels:novel_detail', novel_id=saved_novel.id)

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
            
            # 祭り作家を取
            maturi_writer = User.objects.get(nickname='祭り作家')
            
            if novel_id:
                # 既存の小説を更新
                novel = Novel.objects.get(id=novel_id)
                novel.title = title
                novel.content = content
                novel.author = maturi_writer  # 祭り作家として保存
                novel.save()
            else:
                # 新規小説を作成
                novel = Novel.objects.create(
                    title=title,
                    content=content,
                    author=maturi_writer,  # 祭り作家として保存
                    original_author=request.user,  # 実際の作者は別フィールドに保存
                    genre='祭り'
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
@login_required
def entry_action(request, game_id):
    game = get_object_or_404(MaturiGame, pk=game_id)
    user_entered = game.is_user_entered(request.user)
    context = {
        'game': game,
        'user_entered': user_entered
    }
    if not game.is_entry_period():
        messages.error(request, 'エンリー期間ではありません。')
        logger.debug("Not in entry period")
        return redirect('game_maturi:game_maturi_top')
    elif game.is_user_entered(request.user):
        messages.error(request, 'すでにエントリーしていす。')
        logger.debug("User already entered")
    else:
        if request.method == 'POST':
            game.entrants.add(request.user)
            messages.success(request, 'エントリーが完了しました')
            logger.debug("Entry successful")
            return redirect('game_maturi:game_maturi_top')
        else:
            logger.debug("GET request on entry action")
            return redirect('game_maturi:game_maturi_top')

@login_required
@require_http_methods(["POST"])
def submit_prediction(request):
    if request.method == 'POST':
        try:
            # POSTデータをJSONとしてパース
            data = json.loads(request.body)
            predictions = data.get('predictions', {})
            game_id = data.get('game_id')  # game_idを追加

            # ここでクエリを修正
            game = get_object_or_404(MaturiGame, id=game_id)
            for novel_id, author_id in predictions.items():
                prediction, created = GamePrediction.objects.update_or_create(
                    novel_id=novel_id,
                    maturi_game=game,  # 修正: 'game'ではなく'maturi_game'を使用
                    defaults={'predicted_author_id': author_id, 'predictor': request.user}
                )
            
            return JsonResponse({'success': True, 'message': '予想が保存されました！'})

        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'エラーが発生しました: {str(e)}'
            }, status=500)

    return JsonResponse({
        'success': False,
        'message': '不正なリクエストです。'
    }, status=400)

def prediction_period_finished_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # 現在のゲームを探す
        current_game = MaturiGame.objects.filter(
            maturi_end_date__gte=timezone.now()
        ).order_by('maturi_start_date').first()
        
        if not current_game:
            # 終了した最新の祭りを取得
            current_game = MaturiGame.objects.filter(
                maturi_end_date__lt=timezone.now()
            ).order_by('-maturi_end_date').first()
        
        if not current_game:
            messages.warning(request, '祭りが見つかりません。')
            return redirect('game_maturi:game_maturi_top')
            
        if not current_game.is_prediction_period_finished():
            messages.warning(request, '予想期間が終了するまで結果は表示できません。')
            return redirect('game_maturi:game_maturi_top')
            
        return view_func(request, *args, **kwargs)
    return _wrapped_view

@login_required
@prediction_period_finished_required
def prediction_result(request, user_id):
    predictor = get_object_or_404(User, id=user_id)
    
    # 現在のゲームを探す（デコレータと同じロジック）
    current_game = MaturiGame.objects.filter(
        maturi_end_date__gte=timezone.now()
    ).order_by('maturi_start_date').first()
    
    if not current_game:
        current_game = MaturiGame.objects.filter(
            maturi_end_date__lt=timezone.now()
        ).order_by('-maturi_end_date').first()

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
    }
    
    return render(request, 'game_maturi/includes/prediction_result.html', context)

@login_required
@prediction_period_finished_required
def game_results(request, game_id):
    current_game = get_object_or_404(MaturiGame, id=game_id)
    
    if not current_game.is_prediction_period_finished:
        messages.warning(request, '予想期間終了するまで結果は表示できません。')
        return redirect('game_maturi:game_maturi_top')
    
    # 予想結果の計算は、予想期間了後のみ行う
    predictor_stats = {}
    active_authors = set()
    
    # 現在のゲームでの予想を全て取得
    all_predictions = GamePrediction.objects.filter(
        maturi_game=current_game
    ).select_related('predictor', 'predicted_author', 'novel__original_author')

    # 予想した人全員を取得（既存の処理）
    for prediction in all_predictions:
        participant = prediction.predictor
        if participant not in predictor_stats:
            participant_predictions = all_predictions.filter(predictor=participant)
            total = participant_predictions.count()
            correct = sum(1 for p in participant_predictions 
                        if p.predicted_author_id == p.novel.original_author_id)
            
            predictor_stats[participant] = {
                'total': total,
                'correct': correct,
                'accuracy': (correct / total * 100) if total > 0 else 0,
                'fraction': f"{correct}/{total}"
            }

    # 予想者を50音順にソート
    participants = sorted(
        predictor_stats.items(),
        key=lambda x: x[0].nickname
    )

    # 作品を50音順にソート
    novels = current_game.published_novels.order_by('title')

    # 作品ごとの正解率を計算
    novel_stats = {}
    for novel in novels:
        novel_predictions = all_predictions.filter(novel=novel)
        total = novel_predictions.count()
        correct = sum(1 for p in novel_predictions 
                     if p.predicted_author_id == p.novel.original_author_id)
        novel_stats[novel.id] = {
            'total': total,
            'correct': correct,
            'fraction': f"{correct}/{total}" if total > 0 else "0/0"
        }

    context = {
        'current_game': current_game,
        'predictor_stats': predictor_stats,
        'participants': participants,
        'active_authors': active_authors,
        'novels': novels,
        'novel_stats': novel_stats,
        'all_predictions': all_predictions,
    }
    
    return render(request, 'game_maturi/includes/game_results.html', context)

def maturi_list(request):
    """祭り一覧を表示するビュー"""
    now = timezone.now().date()
    print(f"Current date: {now}")  # 現在の日付を確認
    
    # 過去の祭り
    past_games = MaturiGame.objects.filter(
        maturi_end_date__lt=now,
        maturi_end_date__isnull=False
    ).order_by('-maturi_end_date')
    
    # 現在開催中の祭り
    current_games = MaturiGame.objects.filter(
        maturi_start_date__lte=now,  # 開始日が今日以前
        maturi_end_date__gte=now     # 終了日が今日以降
    ).order_by('maturi_start_date')

    # 開催予定の祭り（未来）
    upcoming_games = MaturiGame.objects.filter(
        maturi_start_date__gt=now,   # ここが問題！今日を含んでしう
        maturi_start_date__isnull=False
    ).order_by('maturi_start_date')
    
    # デバッグ用のログ
    print(f"Current games: {current_games.count()}")
    print(f"Upcoming games: {upcoming_games.count()}")
    print(f"Past games: {past_games.count()}")
    
    context = {
        'current_games': current_games,
        'upcoming_games': upcoming_games,
        'past_games': past_games,
    }
    
    return render(request, 'game_maturi/maturi_list.html', context)

def game_maturi_detail(request, game_id):
    game = get_object_or_404(MaturiGame, pk=game_id)
    
    print(f"\n=== Game Detail Debug ===")
    print(f"Game ID: {game_id}")
    print(f"User: {request.user}")

    # 予想情報を取得
    novel_predictions = {}
    user_predictions = []
    if request.user.is_authenticated:
        predictions = GamePrediction.objects.filter(
            predictor=request.user,
            maturi_game=game
        ).select_related(
            'predicted_author',
            'novel'
        )
        
        print(f"\n=== Predictions Debug ===")
        print(f"Found {predictions.count()} predictions")
        
        user_predictions = list(predictions)
        for pred in predictions:
            novel_predictions[str(pred.novel.id)] = {  # ここをstr()で文字列変換
                'id': pred.id,
                'predicted_author': {
                    'id': pred.predicted_author.id,
                    'nickname': pred.predicted_author.nickname
                },
                'novel': {
                    'id': pred.novel.id,
                    'title': pred.novel.title
                }
            }
            print(f"Added prediction: Novel {pred.novel.id} -> Author {pred.predicted_author.nickname}")

    # 公開済みの小説を取得
    novels = Novel.objects.filter(
        maturi_games=game,
        status='published'
    ).select_related(
        'author',
        'original_author'
    )
    print(f"\nPublished Novels: {novels.count()}")

    # エントリー済みの作者を取得（リレーション名を修正）
    active_authors = User.objects.filter(
        entered_games=game  # ここを修正
    )
    print(f"Active Authors: {active_authors.count()}")

    # 作者ごとの統計情報を作成
    author_stats = {}
    for author in active_authors:
        published_count = novels.filter(original_author=author).count()
        predicted_count = GamePrediction.objects.filter(
            predictor=request.user,
            maturi_game=game,
            predicted_author=author
        ).count() if request.user.is_authenticated else 0
        
        author_stats[author.id] = {
            'total_novels': published_count,
            'predicted_count': predicted_count
        }
        print(f"Author {author.nickname}: {published_count} novels, {predicted_count} predictions")

    # 予想結果の処理を追加
    if game.is_prediction_period_finished():
        all_predictions = GamePrediction.objects.filter(
            maturi_game=game
        ).select_related('predictor', 'predicted_author', 'novel__original_author')

        # 参加者ごとの統計情報を計算
        participants_stats = []
        for author in active_authors:
            author_predictions = all_predictions.filter(predictor=author)
            total = author_predictions.count()
            correct = sum(1 for p in author_predictions 
                        if p.predicted_author_id == p.novel.original_author_id)
            
            stats = {
                'total': total,
                'correct': correct,
                'accuracy': (correct / total * 100) if total > 0 else 0,
                'predictions': {  # この部分を追加
                    p.novel_id: p for p in author_predictions
                }
            }
            participants_stats.append((author, stats))

        # 正解率で降順ソート
        participants_stats.sort(key=lambda x: (-x[1]['accuracy'], -x[1]['correct']))

    context = {
        'game': game,
        'novels': novels,
        'active_authors': active_authors,
        'author_stats': author_stats,
        'novel_predictions': novel_predictions,
        'predictions': user_predictions,
        'is_user_entered': game.is_user_entered(request.user) if request.user.is_authenticated else False,
        'is_writing_period': game.is_writing_period(),
        'is_prediction_period': game.is_prediction_period(),
        'is_novel_publish_period': game.is_novel_publish_period(),
        'participants': participants_stats if game.is_prediction_period_finished() else [],
        'all_predictions': all_predictions if game.is_prediction_period_finished() else [],  # この行を追加
    }

    print("\nContext Debug:")
    print(f"Participants: {participants_stats if game.is_prediction_period_finished() else []}")
    print(f"novel_predictions: {novel_predictions}")
    print(f"Number of predictions: {len(user_predictions)}")
    print("=== End Debug Output ===\n")

    return render(request, 'game_maturi/game_maturi_top.html', context)

# 進捗計算用の関数
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
def add_prediction_results_to_context(game, context):
    all_predictions = GamePrediction.objects.filter(
        maturi_game=game
    ).select_related('predictor', 'predicted_author', 'novel__original_author')

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
    })

@require_http_methods(["POST"])
def predict_author(request):
    try:
        data = json.loads(request.body)
        novel_id = data.get('novel_id')
        author_id = data.get('author_id')

        # 既存の予想を確認
        existing_prediction = GamePrediction.objects.filter(
            novel_id=novel_id,
            predictor=request.user
        ).first()

        # 祭りゲームを取得
        maturi_game = MaturiGame.objects.filter(
            maturi_novels__id=novel_id
        ).first()

        if existing_prediction:
            # 既存の予想を更新
            existing_prediction.predicted_author_id = author_id
            existing_prediction.updated_at = timezone.now()
            existing_prediction.save()
            prediction = existing_prediction
        else:
            # 新しい予想を作成
            prediction = GamePrediction.objects.create(
                maturi_game=maturi_game,
                novel_id=novel_id,
                predictor=request.user,
                predicted_author_id=author_id,
                status='pending'
            )

        print(f"予想処理完了: {prediction}")
        
        return JsonResponse({
            'success': True,
            'prediction_id': prediction.id,
            'message': '予想を保存しました'
        })

    except Exception as e:
        print(f"予想処理エラー: {str(e)}")
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

