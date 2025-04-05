from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from viewflow.contrib.auth import AuthViewset
from viewflow.urls import Application, Site, ModelViewset
from viewflow.workflow.flow import FlowAppViewset

from app1.flows import TenderApplicationFlow



urlpatterns = [
    path('admin/', admin.site.urls),
    path('app1/', include('app1.urls')),
    path('app2/', include('app2.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) 