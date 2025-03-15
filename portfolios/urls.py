from django.shortcuts import redirect
from django.urls import path
from . import views

urlpatterns = [
    path("", lambda _: redirect("portfolios/", permanent=True)),
    path("portfolios/", views.PortfolioListView.as_view(), name="portfolio_list"),
]
