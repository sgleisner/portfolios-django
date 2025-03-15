from django.db import IntegrityError
from django.test import TestCase
from datetime import date, timedelta
from decimal import Decimal
from portfolios.models import Portfolio, Stock, StockPrice, Holding


class PortfolioTest(TestCase):
    def test_create_portfolio(self):
        """A Portfolio can be created and retrieved with the correct data."""
        Portfolio.objects.create(name="Samy's Portfolio")

        self.assertEqual(Portfolio.objects.count(), 1)
        self.assertEqual(Portfolio.objects.first().name, "Samy's Portfolio")


class StockTest(TestCase):
    def setUp(self):
        self.test_stock = Stock.objects.create(symbol="FNTL")
        self.test_date = date(2016, 9, 18)

    def test_create_stock(self):
        """A Stock can be created and retrieved with the correct data."""
        self.assertEqual(Stock.objects.count(), 1)
        self.assertEqual(Stock.objects.first().symbol, self.test_stock.symbol)

    def test_stock_symbol_unique(self):
        """A Stock's symbol must be unique."""
        with self.assertRaises(IntegrityError):
            Stock.objects.create(symbol=self.test_stock.symbol)

    def test_symbol_not_empty(self):
        """A Stock's symbol cannot be empty."""
        with self.assertRaises(IntegrityError):
            Stock.objects.create(symbol="")

    def test_price_get_existing_value(self):
        """If there's a price for a given date, the `price` method should return it."""
        test_price = Decimal("100")
        StockPrice.objects.create(
            stock=self.test_stock,
            date=self.test_date,
            price=test_price,
        )

        self.assertEqual(self.test_stock.price(self.test_date), test_price)

    def test_price_create_new_value(self):
        """If there's no price for a given date, the `price` method should create it."""
        self.assertEqual(StockPrice.objects.count(), 0)

        created_price = self.test_stock.price(self.test_date)

        stock_price = StockPrice.objects.first()
        self.assertEqual(stock_price.stock, self.test_stock)
        self.assertEqual(stock_price.date, self.test_date)
        self.assertEqual(stock_price.price, created_price)


class StockPriceTest(TestCase):
    def setUp(self):
        self.test_stock = Stock.objects.create(symbol="FNTL")
        self.test_date = date(2016, 9, 18)

    def test_create_stock_price(self):
        """A StockPrice can be created and retrieved with the correct data."""
        test_price = Decimal("100")
        StockPrice.objects.create(
            stock=self.test_stock,
            date=self.test_date,
            price=test_price,
        )

        self.assertEqual(StockPrice.objects.count(), 1)
        stock_price = StockPrice.objects.first()
        self.assertEqual(stock_price.stock, self.test_stock)
        self.assertEqual(stock_price.date, self.test_date)
        self.assertEqual(stock_price.price, test_price)

    def test_price_non_negative(self):
        """A StockPrice's price must not be negative."""
        with self.assertRaises(IntegrityError):
            StockPrice.objects.create(
                stock=self.test_stock,
                date=self.test_date,
                price=Decimal("-100"),
            )

    def test_price_non_zero(self):
        """A StockPrice's price must not be equal to zero."""
        with self.assertRaises(IntegrityError):
            StockPrice.objects.create(
                stock=self.test_stock,
                date=self.test_date,
                price=Decimal("0"),
            )

    def test_price_minimum(self):
        """A StockPrice's price must be at least $0.0001."""
        # Allow the minimum price
        StockPrice.objects.create(
            stock=self.test_stock,
            date=self.test_date,
            price=Decimal("0.0001"),
        )

        # Less than that should raise an exception
        with self.assertRaises(Exception):
            StockPrice.objects.create(
                stock=self.test_stock,
                # Use another date to prevent unique constraint error
                date=self.test_date + timedelta(days=1),
                price=Decimal("0.00001"),
            )

    def test_price_maximum(self):
        """A StockPrice's price must be at most $999,999.9999."""
        # Allow the maximum price
        StockPrice.objects.create(
            stock=self.test_stock,
            date=self.test_date,
            price=Decimal("999999.9999"),
        )

        # More than that should raise an exception
        with self.assertRaises(Exception):
            StockPrice.objects.create(
                stock=self.test_stock,
                # Use another date to prevent unique constraint error
                date=self.test_date + timedelta(days=1),
                price=Decimal("999999.99999"),
            )

    def test_stock_and_date_unique_together(self):
        """A StockPrice's stock and date must be unique together."""
        StockPrice.objects.create(
            stock=self.test_stock,
            date=self.test_date,
            price=Decimal("100"),
        )

        with self.assertRaises(IntegrityError):
            StockPrice.objects.create(
                stock=self.test_stock,
                date=self.test_date,
                price=Decimal("200"),
            )


class HoldingTest(TestCase):
    def setUp(self):
        self.test_portfolio = Portfolio.objects.create()
        self.test_stock = Stock.objects.create(symbol="FNTL")

    def test_create_holding(self):
        """A Holding can be created and retrieved with the correct data."""
        Holding.objects.create(
            portfolio=self.test_portfolio,
            stock=self.test_stock,
            quantity=100,
        )

        self.assertEqual(Holding.objects.count(), 1)
        holding = Holding.objects.first()
        self.assertEqual(holding.portfolio, self.test_portfolio)
        self.assertEqual(holding.stock, self.test_stock)
        self.assertEqual(holding.quantity, 100)

    def test_quantity_non_negative(self):
        """A Holding's quantity must not be negative."""
        with self.assertRaises(IntegrityError):
            Holding.objects.create(
                portfolio=self.test_portfolio,
                stock=self.test_stock,
                quantity=-100,
            )

    def test_portfolio_and_stock_unique_together(self):
        """A Holding's portfolio and stock must be unique together."""
        Holding.objects.create(
            portfolio=self.test_portfolio,
            stock=self.test_stock,
            quantity=100,
        )

        with self.assertRaises(IntegrityError):
            Holding.objects.create(
                portfolio=self.test_portfolio,
                stock=self.test_stock,
                quantity=200,
            )
