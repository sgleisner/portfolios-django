from django.db import models
from decimal import Decimal
from datetime import date
import random


class Portfolio(models.Model):
    """
    A collection of stock holdings.

    Attributes:
        name (str): The name of the portfolio.
    """

    name = models.CharField(max_length=255)

    def value(self, date: date) -> Decimal:
        """
        Returns the total value of the portfolio on a given date.
        The value is calculated as the sum of the value of each stock holding.

        Args:
            date: The date for which to get the value.
        """
        value = sum(
            holding.stock.price(date) * holding.quantity
            for holding in self.holdings.all()
        )

        return value

    def profit(self, start_date: date, end_date: date) -> tuple[Decimal, Decimal]:
        """
        Returns the total profit of the portfolio over a given date range and its
        annualized return as a raw decimal value.

        Args:
            start_date: The start date of the date range (inclusive).
            end_date: The end date of the date range (inclusive).

        Returns:
            (profit, annualized_return): A tuple containing the expected values.
        """
        if start_date >= end_date:
            raise ValueError("The start date must be before the end date.")

        today = date.today()
        if start_date > today or end_date > today:
            raise ValueError("Received dates must not be in the future.")

        initial_value = self.value(start_date)
        final_value = self.value(end_date)
        days = (end_date - start_date).days

        # Since neither prices nor holding quantities can be zero, if any
        # of the values is zero, the profit will be zero as well.
        if initial_value == 0 or final_value == 0:
            return (Decimal("0"), Decimal("0"))

        profit = final_value - initial_value

        # Calculate the annualized return using the formula:
        # annualized_return = ( 1 + (final_value - initial_value) / initial_value ) ^ (365 / days) - 1
        # Which can be derived from the formulas in the following links:
        # https://www.investopedia.com/terms/a/annualized-total-return.asp
        # https://www.investopedia.com/terms/c/cumulativereturn.asp
        # When simplified, it becomes:
        annualized_return = (final_value / initial_value) ** (Decimal("365") / days) - 1

        return (profit, annualized_return)


class Stock(models.Model):
    """
    A stock whose shares can be held in a portfolio.

    Attributes:
        symbol (str): The stock's ticker symbol. Must be unique and non-empty.
    """

    symbol = models.CharField(max_length=10, unique=True)

    def price(self, date: date) -> Decimal:
        """
        Returns the price of the stock on a given date.
        If no price is found for the given date, a fake random price is created.

        Args:
            date: The date for which to get the price. It must not be in the future.
        """
        if date > date.today():
            raise ValueError("Cannot get the price of a stock for a future date.")

        try:
            price = StockPrice.objects.get(stock=self, date=date).price
        except StockPrice.DoesNotExist:
            # Create a StockPrice with a fake random price and return its value.
            random_price = Decimal(f"{random.uniform(1, 999999):.4f}")
            price = StockPrice.objects.create(
                stock=self, date=date, price=random_price
            ).price

        return price

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
        price (Decimal): The price of the stock on the given date, must be greater than 0.
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
                name="positive_price",
            ),
        ]


class Holding(models.Model):
    """A stock holding representing the position of a portfolio in a stock.

    Attributes:
        portfolio (Portfolio): The portfolio that holds the stock.
        stock (Stock): The stock being held.
        quantity (int): The number of shares of the stock being held, must be greater than 0.
    """

    portfolio = models.ForeignKey(
        Portfolio, on_delete=models.CASCADE, related_name="holdings"
    )
    stock = models.ForeignKey(Stock, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["portfolio", "stock"],
                name="unique_portfolio_stock",
            ),
            models.CheckConstraint(
                check=models.Q(quantity__gt=0),
                name="positive_quantity",
            ),
        ]
