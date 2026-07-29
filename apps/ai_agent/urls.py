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
    path('knowledge/document/upload/', views.knowledge_document_upload, name='knowledge_document_upload'),
    path('knowledge/document/<int:pk>/delete/', views.knowledge_document_delete, name='knowledge_document_delete'),
    path('knowledge/url/learn/', views.knowledge_learn_url, name='knowledge_learn_url'),
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
    path('bridge/incoming/', views.bridge_incoming, name='bridge_incoming'),
    path('whatsapp/', views.whatsapp_page, name='whatsapp'),
    path('whatsapp/status/', views.whatsapp_status_api, name='whatsapp_status'),
    path('whatsapp/qr/', views.whatsapp_qr_api, name='whatsapp_qr'),
    path('rules/', views.business_rule_list, name='business_rule_list'),
    path('rules/create/', views.business_rule_create, name='business_rule_create'),
    path('rules/<int:pk>/edit/', views.business_rule_edit, name='business_rule_edit'),
    path('rules/<int:pk>/delete/', views.business_rule_delete, name='business_rule_delete'),
]
