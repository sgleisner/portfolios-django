from django.db import IntegrityError
from django.test import TestCase
from datetime import date, timedelta
from decimal import Decimal
from portfolios.models import Portfolio, Stock, StockPrice, Holding


class PortfolioTest(TestCase):
    def setUp(self):
        self.test_portfolio = Portfolio.objects.create(name="Samy's Portfolio")
        self.test_date = date(2016, 9, 18)
        self.test_holding_data = {
            "JUEMS": 10,
            "FNTLST": 20,
            "MERYL": 30,
            "GEORG": 40,
            "BRAD": 50,
            "CHUCK": 60,
        }

        for symbol, quantity in self.test_holding_data.items():
            stock = Stock.objects.create(symbol=symbol)
            Holding.objects.create(
                portfolio=self.test_portfolio,
                stock=stock,
                quantity=quantity,
            )

    def test_create_portfolio(self):
        """A Portfolio can be created and retrieved with the correct data."""
        self.assertEqual(Portfolio.objects.count(), 1)
        self.assertEqual(Portfolio.objects.first().name, self.test_portfolio.name)

    def test_value_for_date(self):
        """The `value` method should return the total value of a portfolio for a given date."""
        expected_value = Decimal("0")

        for symbol, quantity in self.test_holding_data.items():
            price = Stock.objects.get(symbol=symbol).price(self.test_date)
            expected_value += price * quantity

        self.assertEqual(self.test_portfolio.value(self.test_date), expected_value)

    def test_profit_for_valid_date_range(self):
        """The `profit` method should return the total profit of a portfolio for a given, valid date range."""
        start_date = self.test_date - timedelta(days=5)
        end_date = self.test_date + timedelta(days=5)

        # The portfolio's profit should be the sum of the profits its holdings over the date range.
        expected_profit = Decimal("0")

        for symbol, quantity in self.test_holding_data.items():
            stock = Stock.objects.get(symbol=symbol)
            price_start = stock.price(start_date)
            price_end = stock.price(end_date)

            # Each holding's profit is its end price times its quantity minus its start price
            # times its quantity. Factorizing the quantity, we get the formula below.
            expected_profit += (price_end - price_start) * quantity

        self.assertEqual(
            self.test_portfolio.profit(start_date, end_date), expected_profit
        )

    def test_profit_for_invalid_date_range(self):
        """The `profit` method should raise an exception if the received date range is invalid."""
        start_date = self.test_date + timedelta(days=5)
        end_date = self.test_date - timedelta(days=5)

        # Case 1: start date is after end date
        with self.assertRaisesMessage(
            ValueError, "The start date must be before the end date."
        ):
            self.test_portfolio.profit(start_date, end_date)

        # Case 2: start date is equal to end date
        with self.assertRaisesMessage(
            ValueError, "The start date must be before the end date."
        ):
            self.test_portfolio.profit(self.test_date, self.test_date)

        # Case 3: end date is in the future
        future_date = date.today() + timedelta(days=1)
        with self.assertRaisesMessage(
            ValueError, "Received dates must not be in the future."
        ):
            self.test_portfolio.profit(date.today(), future_date)

        # Case 4: both dates are in the future
        with self.assertRaisesMessage(
            ValueError, "Received dates must not be in the future."
        ):
            self.test_portfolio.profit(future_date, future_date + timedelta(days=1))


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

    def test_price_with_future(self):
        """The date passed to the `price` method must not be in the future."""
        future_date = date.today() + timedelta(days=1)

        with self.assertRaisesMessage(
            ValueError,
            "Cannot get the price of a stock for a future date.",
        ):
            self.test_stock.price(future_date)


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
