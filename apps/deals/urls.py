from django.urls import path
from . import views

app_name = 'deals'

urlpatterns = [
    path('', views.deal_list, name='list'),
    path('kanban/', views.deal_kanban, name='kanban'),
    path('create/', views.deal_create, name='create'),
    path('<int:pk>/', views.deal_detail, name='detail'),
    path('<int:pk>/edit/', views.deal_edit, name='edit'),
    path('<int:pk>/delete/', views.deal_delete, name='delete'),
    path('<int:pk>/stage/', views.deal_stage_update, name='stage_update'),
    path('<int:pk>/activity/add/', views.deal_activity_add, name='activity_add'),
]
