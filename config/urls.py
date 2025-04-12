from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from viewflow.contrib.auth import AuthViewset
from viewflow.urls import Application, Site, ModelViewset
from viewflow.workflow.flow import FlowAppViewset
from app1.flows import TenderApplicationFlow


site = Site(title="ACME Corp", viewsets=[
    Application(
        title='Tender Applications', icon='business_center', app_name='tender_application', viewsets=[
            FlowAppViewset(TenderApplicationFlow, icon="description"),
        ]
    ),
])

urlpatterns = [
    path('', RedirectView.as_view(url='/app2/', permanent=True)),
    path('admin/', admin.site.urls),
    path('app1/', include('app1.urls')),
    path('app2/', include('app2.urls')),
    path('vf/', site.urls),
] 