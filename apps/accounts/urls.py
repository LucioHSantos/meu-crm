from django.urls import path

from . import views

app_name = 'accounts'

urlpatterns = [
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('list/', views.user_list_view, name='user_list'),
    path('<int:pk>/edit/', views.user_edit_view, name='user_edit'),
    path('profile/', views.profile_view, name='profile'),
]
