from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from viewflow.contrib.auth import AuthViewset
from viewflow.urls import Application, Site, ModelViewset
from viewflow.workflow.flow import FlowAppViewset

site = Site(title="ACME Corp", viewsets=[
    # App1 references removed - keeping only app2 functionality
])

urlpatterns = [
    path('', RedirectView.as_view(url='/app2/', permanent=True)),
    path('admin/', admin.site.urls),
    path('app2/', include('app2.urls')),
    path('vf/', site.urls),
] 