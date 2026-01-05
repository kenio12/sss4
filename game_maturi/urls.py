from django.urls import path
from .views import game_maturi_top, post_or_edit_maturi_novel, prediction_result
from . import views

app_name = 'game_maturi'

urlpatterns = [
    path('game_top/<int:game_id>/', game_maturi_top, name='game_maturi_top'),
    path('post_or_edit/', post_or_edit_maturi_novel, name='post_or_edit_maturi_novel'),
    path('post_or_edit/<int:novel_id>/', post_or_edit_maturi_novel, name='post_or_edit_maturi_novel'),
    path('entry-action/<int:game_id>/', views.entry_action, name='entry_action'),
    path('submit-prediction/', views.submit_prediction, name='submit_prediction'),
    path('prediction_result/<int:user_id>/', views.prediction_result, name='prediction_result'),
    path('maturi_list/', views.maturi_list, name='maturi_list'),
    path('predict/', views.predict_author, name='predict_author'),
    path('cancel_prediction/', views.cancel_prediction, name='cancel_prediction'),
    path('auto-save/', views.auto_save_maturi_novel, name='auto_save_maturi_novel'),

]
