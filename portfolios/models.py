from django.db import models
from decimal import Decimal


class Portfolio(models.Model):
    """
    A collection of stock holdings.

    Attributes:
        name (str): The name of the portfolio.
    """

    name = models.CharField(max_length=255)


class Stock(models.Model):
    """
    A stock whose shares can be held in a portfolio.

    Attributes:
        symbol (str): The stock's ticker symbol. Must be unique and non-empty.
    """

    symbol = models.CharField(max_length=10, unique=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=~models.Q(symbol=""),
                name="non_empty_symbol",
            ),
        ]


class StockPrice(models.Model):
    """
    The price of a stock on a given date.
    There can only be one price per stock per day.

    Attributes:
        stock (Stock): The stock whose price is being recorded.
        date (date): The date of the price.
        price (Decimal): The price of the stock on the given date.
    """

    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    date = models.DateField()
    # Allow prices from $0.00001 up to $999,999.9999, and store them
    # as Decimal to prevent floating-point arithmetic issues.
    # See: https://floating-point-gui.de/
    price = models.DecimalField(max_digits=10, decimal_places=4)

    class Meta:
        constraints = [
            # There should only be one price per stock per day.
            # As a bonus, this constraint also speeds up queries for stock prices.
            models.UniqueConstraint(
                fields=["stock", "date"],
                name="unique_stock_date",
            ),
            models.CheckConstraint(
                check=models.Q(price__gt=Decimal("0")),
                name="non_negative_price",
            ),
        ]


class Holding(models.Model):
    """A stock holding representing the position of a portfolio in a stock.

    Attributes:
        portfolio (Portfolio): The portfolio that holds the stock.
        stock (Stock): The stock being held.
        quantity (int): The number of shares of the stock being held.
    """

    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE)
    stock = models.ForeignKey(Stock, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["portfolio", "stock"],
                name="unique_portfolio_stock",
            ),
        ]
