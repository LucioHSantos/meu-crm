from django.urls import path

from . import views

app_name = 'ai_agent'

urlpatterns = [
    path('config/', views.agent_config, name='config'),
    path('knowledge/', views.knowledge_list, name='knowledge_list'),
    path('knowledge/create/', views.knowledge_create, name='knowledge_create'),
    path('knowledge/<int:pk>/edit/', views.knowledge_edit, name='knowledge_edit'),
    path('knowledge/<int:pk>/delete/', views.knowledge_delete, name='knowledge_delete'),
    path('knowledge/bulk/', views.knowledge_bulk, name='knowledge_bulk'),
    path('training/', views.training_list, name='training_list'),
    path('training/create/', views.training_create, name='training_create'),
    path('training/<int:pk>/delete/', views.training_delete, name='training_delete'),
    path('training/test/', views.training_test_page, name='training_test'),
    path('training/test/send/', views.training_test_send, name='training_test_send'),
    path('conversations/', views.conversation_list, name='conversation_list'),
    path('conversations/<int:pk>/', views.conversation_detail, name='conversation_detail'),
    path('conversations/<int:pk>/handoff/', views.conversation_handoff, name='conversation_handoff'),
    path('conversations/<int:pk>/close/', views.conversation_close, name='conversation_close'),
    path('webhook/', views.webhook, name='webhook'),
]
