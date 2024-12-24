from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import get_user_model
from .forms import MaturiGameForm
from game_maturi.models import MaturiGame, Phrase
from game_same_title.models import MonthlySameTitleInfo
import datetime
from django.http import JsonResponse
import logging
import re  # 正規表現モジュールをインポート
from django.contrib import messages
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.utils import timezone

# loggerの設定
logger = logging.getLogger(__name__)

def is_admin(user):
    return user.is_superuser

@login_required
@user_passes_test(is_admin)
def maturi_game_setup(request):
    User = get_user_model()
    game = None  # 新規作成時はNone
    entrants = []  # 新規作成時は空のリスト
    
    # titlesの初期化をif-else文の外に移動
    selected_year = datetime.datetime.now().year
    titles = MonthlySameTitleInfo.objects.filter(month__startswith=str(selected_year)).values_list('title', flat=True)
    
    if request.method == 'POST':
        form = MaturiGameForm(request.POST)
        if form.is_valid():
            try:
                # フォームの基本情報を保存
                maturi_game = form.save()
                
                # 12個の語句を処理
                phrases = []
                for i in range(1, 13):
                    phrase_text = form.cleaned_data.get(f'phrase{i}')
                    if phrase_text:
                        phrase_text = re.sub(r'\s+', '', phrase_text)
                        phrase, created = Phrase.objects.get_or_create(text=phrase_text)
                        phrases.append(phrase)
                
                # 語句を追加
                if phrases:
                    maturi_game.phrases.add(*phrases)
                
                messages.success(request, '祭りの設定を完了しました！')
                return redirect('adminpanel:maturi_setting_list')
            except Exception as e:
                logger.error(f"Error in maturi_game_setup: {str(e)}")
                messages.error(request, f'エラーが発生しました: {str(e)}')
        else:
            messages.error(request, 'フォームの入力内容に問題があります。')
            logger.error(f"Form errors: {form.errors}")
    else:
        form = MaturiGameForm()

    context = {
        'form': form,
        'titles': titles,
        'errors': form.errors if hasattr(form, 'errors') else None,
        'all_users': User.objects.all(),
        'game': game,
        'entrants': entrants,
    }
    return render(request, 'adminpanel/maturi_game_setup.html', context)

@login_required
@user_passes_test(is_admin)
def get_titles_for_year(request):
    year = request.GET.get('year')
    # 'month' フィールドの先頭4文字が 'year' と一致するものをフィルタリング
    titles = MonthlySameTitleInfo.objects.filter(month__startswith=year).values_list('title', flat=True)
    return JsonResponse(list(titles), safe=False)

from game_maturi.models import MaturiGame  # game_maturi のモデルをインポート

@login_required
@user_passes_test(is_admin)
def maturi_setting_list(request):
    # 祭りの開始日で降順（新しい順）にソート
    maturi_games = MaturiGame.objects.all().order_by('-maturi_start_date')
    return render(request, 'adminpanel/maturi_setting_list.html', {'maturi_games': maturi_games})

@login_required
@user_passes_test(is_admin)
def event_selection(request):
    return render(request, 'adminpanel/event_selection.html')  # 新しいテンプレートを指定

@login_required
@user_passes_test(is_admin)
def edit_maturi_game(request, id):
    game = get_object_or_404(MaturiGame, id=id)
    User = get_user_model()
    
    if request.method == 'POST':
        form = MaturiGameForm(request.POST, instance=game)
        
        if form.is_valid():
            try:
                game = form.save()
                messages.success(request, '祭りの設定を更新しました。')
                return redirect('adminpanel:maturi_setting_list')
            except Exception as e:
                messages.error(request, f'エラーが発生しました: {str(e)}')
        else:
            for field, errors in form.errors.items():
                messages.error(request, f'{field}: {", ".join(errors)}')
    else:
        # GETリクエストの場合のフォーム初期化をここに移動
        form = MaturiGameForm(instance=game)
    
    context = {
        'form': form,
        'game': game,
        'all_users': User.objects.all(),
        'entrants': game.entrants.all(),
        'errors': form.errors if hasattr(form, 'errors') else None,
        'titles': [],  # または必要なタイトルのリスト
        'year': timezone.now().year,  # 現在の年を追加
    }
    return render(request, 'adminpanel/maturi_game_setup.html', context)

@login_required
@user_passes_test(is_admin)
def delete_maturi_game(request, id):
    if request.method == 'POST':
        maturi_game = get_object_or_404(MaturiGame, id=id)
        maturi_game.delete()
        return redirect('adminpanel:maturi_setting_list')
    else:
        # POST以外のメソッドでアクセスされた場合はリダイレクト
        return redirect('adminpanel:maturi_setting_list')

