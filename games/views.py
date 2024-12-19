from django.shortcuts import render, get_object_or_404

def game_top(request):
    # ここでは特にデータを渡さずにテンプレートをレンダリングする
    return render(request, 'games/game_top.html')