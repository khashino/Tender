from django.contrib import admin
from django.urls import path, include
from viewflow.contrib.auth import AuthViewset
from viewflow.urls import Application, Site, ModelViewset
from viewflow.workflow.flow import FlowAppViewset
from app1.flows import HelloWorldFlow


site = Site(title="ACME Corp", viewsets=[
    Application(
        title='Sample App', icon='people', app_name='sample', viewsets=[
            FlowAppViewset(HelloWorldFlow, icon="assignment"),
        ]
    ),
])

urlpatterns = [
    path('admin/', admin.site.urls),
    path('app1/', include('app1.urls')),
    path('app2/', include('app2.urls')),
    path('vf/', site.urls),
] 