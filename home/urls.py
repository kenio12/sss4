from django.urls import path
from django.views.generic import TemplateView
from .views import HomePageView, novels_list_ajax
from . import views
app_name = 'home'

urlpatterns = [
    path('', HomePageView.as_view(), name='home'),
    path('ajax/novels_list/', novels_list_ajax, name='novels_list_ajax'),
    path('terms/', views.terms, name='terms'),
    path('main', views.main_view, name='main_view'),
    path('admin-home/', views.admin_home, name='admin_home'),
    path('shortcut_guide.html', TemplateView.as_view(template_name='shortcut_guide.html'), name='shortcut_guide'),
]