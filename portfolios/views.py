from django.shortcuts import render
from django.views.generic import ListView, DetailView
from portfolios.forms import DateRangeForm
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
        form = DateRangeForm(self.request.GET or None)
        results = None
        if form.is_valid():
            start_date = form.cleaned_data["start_date"]
            end_date = form.cleaned_data["end_date"]
            profit, annualized_return = self.object.profit(start_date, end_date)
            results = {
                "profit": profit,
                "annualized_return": annualized_return * 100,  # as a percentage
                "start_date": start_date,
                "end_date": end_date,
                "initial_value": self.object.value(start_date),
                "final_value": self.object.value(end_date),
                "days_held": (end_date - start_date).days,
            }

        context["form"] = form
        context["results"] = results
        return context
