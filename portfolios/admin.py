from django.contrib import admin
from .models import Portfolio, Stock, StockPrice, Holding

admin.site.register(Stock)
admin.site.register(StockPrice)
admin.site.register(Holding)


class HoldingInline(admin.TabularInline):
    model = Holding


@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    inlines = [HoldingInline]
