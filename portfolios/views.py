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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add the result of calling the price for today to the context
        context["current_value"] = self.object.value(date.today())
        return context
