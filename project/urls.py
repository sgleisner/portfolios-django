from django.contrib import admin
from django.shortcuts import redirect
from django.urls import include, path

urlpatterns = [
    path("", include("portfolios.urls")),
    path("admin/", admin.site.urls),
]
