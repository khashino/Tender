from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('', RedirectView.as_view(url='/app2/', permanent=True)),
    path('admin/', admin.site.urls),
    path('app2/', include('app2.urls')),
] 