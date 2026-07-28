from django.urls import path

from . import api_views

app_name = 'api'

urlpatterns = [
    path('dashboard/metrics/', api_views.dashboard_metrics, name='dashboard_metrics'),
    path('deals/', api_views.DealListAPI.as_view(), name='deal_list'),
    path('deals/<int:pk>/', api_views.DealDetailAPI.as_view(), name='deal_detail'),
    path('contacts/', api_views.ContactListAPI.as_view(), name='contact_list'),
    path('contacts/<int:pk>/', api_views.ContactDetailAPI.as_view(), name='contact_detail'),
    path('tasks/', api_views.TaskListAPI.as_view(), name='task_list'),
    path('tasks/<int:pk>/', api_views.TaskDetailAPI.as_view(), name='task_detail'),
]
