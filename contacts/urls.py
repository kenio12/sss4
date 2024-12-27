from django.urls import path
from . import views

app_name = 'contacts'

urlpatterns = [
    path('create/', views.ContactCreateView.as_view(), name='contact_create'),
    path('detail/<int:pk>/', views.ContactDetailView.as_view(), name='contact_detail'),
    path('update-status/<int:pk>/', views.update_status, name='update_status'),
    path('list/', views.ContactListView.as_view(), name='contact_list'),
] 