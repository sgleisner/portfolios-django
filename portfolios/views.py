from django.shortcuts import render
from django.views.generic import ListView

from portfolios.models import Portfolio


class PortfolioListView(ListView):
    model = Portfolio
    template_name = "portfolios/portfolio_list.html"
    context_object_name = "portfolios"
