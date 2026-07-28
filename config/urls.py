from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.dashboard.urls', namespace='dashboard')),
    path('accounts/', include('apps.accounts.urls', namespace='accounts')),
    path('contacts/', include('apps.contacts.urls', namespace='contacts')),
    path('deals/', include('apps.deals.urls', namespace='deals')),
    path('tasks/', include('apps.tasks.urls', namespace='tasks')),
    path('api/', include('apps.dashboard.api_urls', namespace='api')),
    path('ai-agent/', include('apps.ai_agent.urls', namespace='ai_agent')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
