from django.shortcuts import render
from django.views.generic import ListView, DetailView
from datetime import date
from portfolios.models import Portfolio


class PortfolioListView(ListView):
    model = Portfolio
    template_name = "portfolios/portfolio_list.html"
    context_object_name = "portfolios"


class PortfolioDetailView(DetailView):
    model = Portfolio
    template_name = "portfolios/portfolio_detail.html"
    context_object_name = "portfolio"
