from django.urls import path

from . import views

app_name = 'contacts'

urlpatterns = [
    path('', views.contact_list, name='list'),
    path('create/', views.contact_create, name='create'),
    path('<int:pk>/', views.contact_detail, name='detail'),
    path('<int:pk>/edit/', views.contact_edit, name='edit'),
    path('<int:pk>/delete/', views.contact_delete, name='delete'),
    path('<int:pk>/note/add/', views.contact_note_add, name='note_add'),
]
