from django.urls import path
from .views import maturi_game_setup, get_titles_for_year, maturi_setting_list, event_selection, edit_maturi_game, delete_maturi_game

app_name = 'adminpanel'

urlpatterns = [
    path('maturi-setup/', maturi_game_setup, name='maturi_game_setup'),
    path('api/get-titles/', get_titles_for_year, name='get-titles'),
    path('settings/', maturi_setting_list, name='maturi_setting_list'),
    path('event-selection/', event_selection, name='event_selection'),
    path('edit-maturi/<int:id>/', edit_maturi_game, name='edit_maturi_game'),
    path('delete-maturi/<int:id>/', delete_maturi_game, name='delete_maturi_game'),
]