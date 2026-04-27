"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.conf import settings
from django.contrib.staticfiles.views import serve as serve_static
from django.urls import include, path, re_path
from dashboard.views import interface_institucional

urlpatterns = [
    path('', interface_institucional, name='home'),
    path('admin/', admin.site.urls),
    path('contas/', include('accounts.urls')),
    path('clientes/', include('clients.urls')),
    path('empresas/', include('companies.urls')),
    path('contratos/', include('contracts.urls')),
    path('propostas/', include('proposals.urls')),
    path('painel/', include('dashboard.urls')),
]

if settings.SERVE_STATICFILES:
    urlpatterns += [
        re_path(r"^static/(?P<path>.*)$", serve_static, {"insecure": True}),
    ]
