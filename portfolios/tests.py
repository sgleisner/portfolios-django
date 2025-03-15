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

    def test_str(self):
        """The string representation of a Portfolio should be its name."""
        self.assertEqual(str(self.test_portfolio), self.test_portfolio.name)

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

    def test_value_empty_portfolio(self):
        """The `value` method should return zero for an empty portfolio."""
        empty_portfolio = Portfolio.objects.create(name="The Voidfolio")
        self.assertEqual(empty_portfolio.value(self.test_date), Decimal("0"))

    def test_profit_for_valid_date_range(self):
        """The `profit` method's return should contain the total profit of a portfolio for a given, valid date range."""
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

        # The profit's method return first element should be the total profit
        profit, _ = self.test_portfolio.profit(start_date, end_date)
        self.assertEqual(profit, expected_profit)

    def test_profit_for_invalid_date_range(self):
        """The `profit` method's should raise an exception if the received date range is invalid."""
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

    def test_profit_annualized_return_zero(self):
        """The `profit` method should calculate the annualized return as zero if the portfolio's value doesn't change."""
        start_date = self.test_date
        end_date = start_date + timedelta(days=100)

        for holding in self.test_portfolio.holdings.all():
            stock = holding.stock

            # This will implicitly create a `StockPrice` for the start date
            price = stock.price(start_date)

            # Create a stock price for the end date with the same price
            StockPrice.objects.create(stock=stock, date=end_date, price=price)

        # The profit's method return second element should be the annualized return
        _, annualized_return = self.test_portfolio.profit(start_date, end_date)
        self.assertEqual(annualized_return, Decimal("0"))

    def test_profit_annualized_return_positive_over_a_year(self):
        """The `profit` method should correctly calculate a positive annualized return over a year."""
        # For a period of exactly one year, the annualized return is equal to the total return,
        # which is the difference between the end and start prices divided by the start price.
        start_date = self.test_date
        end_date = start_date + timedelta(days=365)

        for holding in self.test_portfolio.holdings.all():
            stock = holding.stock

            # This will implicitly create a random `StockPrice` for the start date
            price_start = stock.price(start_date)

            # Create a stock price for the end date with a higher price, keeping it
            # within the maximum allowed price
            price_end = min(price_start * 2, Decimal("999999.9999"))
            StockPrice.objects.create(stock=stock, date=end_date, price=price_end)

        # The profit's method return second element should be the annualized return
        _, annualized_return = self.test_portfolio.profit(start_date, end_date)

        # The annualized return should be positive and equal to the total return
        initial_value = self.test_portfolio.value(start_date)
        final_value = self.test_portfolio.value(end_date)
        total_return = (final_value - initial_value) / initial_value

        self.assertGreater(annualized_return, Decimal("0"))

        # Despite Decimal's floating point precision, the result might be slightly off
        # so we use assertAlmostEqual to compare the two values up to 7 decimal places (the default).
        self.assertAlmostEqual(annualized_return, total_return)

    def test_profit_annualized_return_negative_over_a_year(self):
        """The `profit` method should correctly calculate a negative annualized return over a year."""
        # For a period of exactly one year, the annualized return is equal to the total return,
        # which is the difference between the end and start prices divided by the start price.
        start_date = self.test_date
        end_date = start_date + timedelta(days=365)

        for holding in self.test_portfolio.holdings.all():
            stock = holding.stock

            # This will implicitly create a random `StockPrice` for the start date
            price_start = stock.price(start_date)

            # Create a stock price for the end date with a lower price, keeping it
            # within the minimum allowed price
            price_end = max(price_start / 2, Decimal("0.0001"))
            StockPrice.objects.create(stock=stock, date=end_date, price=price_end)

        # The profit's method return second element should be the annualized return
        _, annualized_return = self.test_portfolio.profit(start_date, end_date)

        # The annualized return should be negative and equal to the total return
        initial_value = self.test_portfolio.value(start_date)
        final_value = self.test_portfolio.value(end_date)
        total_return = (final_value - initial_value) / initial_value

        self.assertLess(annualized_return, Decimal("0"))

        # Despite Decimal's floating point precision, the result might be slightly off
        # so we use assertAlmostEqual to compare the two values up to 7 decimal places (the default).
        self.assertAlmostEqual(annualized_return, total_return)

    def test_profit_annualized_return_example(self):
        """The `profit` method should correctly calculate the annualized return for a given example."""
        # For a cummulative return of 23.74% over 575 days, the annualized return is 0.145
        # Example taken from Investopedia:
        # https://www.investopedia.com/terms/a/annualized-total-return.asp#toc-annualized-return-formula-and-calculation
        start_date = self.test_date
        end_date = start_date + timedelta(days=575)

        # Create a porfolio with a single stock share and a return of 23.74% over 575 days
        portfolio = Portfolio.objects.create(name="Investopedia's Portfolio")
        stock = Stock.objects.create(symbol="SAMYG")
        initial_price = Decimal("100")
        final_price = Decimal("123.74")  # +23.74%
        StockPrice.objects.create(stock=stock, date=start_date, price=initial_price)
        StockPrice.objects.create(stock=stock, date=end_date, price=final_price)
        Holding.objects.create(portfolio=portfolio, stock=stock, quantity=1)

        # The profit's method return second element should be the annualized return
        _, annualized_return = portfolio.profit(start_date, end_date)

        # Upon further inspection, the result reported by Investopedia is actually
        # rounded to 3 decimal places, so we use that same rounding to compare.
        self.assertEqual(round(annualized_return, 3), Decimal("0.145"))

    def test_profit_empty_portfolio(self):
        """The `profit` method should return zero profit and annualized return for an empty portfolio."""
        # Since the price of stocks cannot be zero, a portfolio with nil value holds no stocks.
        # For those cases, we assume both the profit and annualized return are zero.
        empty_portfolio = Portfolio.objects.create(name="The Voidfolio")

        start_date = self.test_date
        end_date = start_date + timedelta(days=5)
        profit, annualized_return = empty_portfolio.profit(start_date, end_date)

        self.assertEqual(profit, Decimal("0"))
        self.assertEqual(annualized_return, Decimal("0"))


class StockTest(TestCase):
    def setUp(self):
        self.test_stock = Stock.objects.create(symbol="FNTL")
        self.test_date = date(2016, 9, 18)

    def test_str(self):
        """The string representation of a Stock should be its symbol."""
        self.assertEqual(str(self.test_stock), self.test_stock.symbol)

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

    def test_str(self):
        """The string representation of a StockPrice should be its stock's symbol, date and price."""
        test_price = Decimal("100")
        stock_price = StockPrice.objects.create(
            stock=self.test_stock,
            date=self.test_date,
            price=test_price,
        )

        self.assertEqual(
            str(stock_price),
            f"{stock_price.stock.symbol} - {stock_price.date} - ${stock_price.price:,.4f}",
        )

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
        self.test_portfolio = Portfolio.objects.create(name="Samy's Portfolio")
        self.test_stock = Stock.objects.create(symbol="FNTL")

    def test_str(self):
        """The string representation of a Holding should be its stock's symbol, quantity and portfolio's name."""
        holding = Holding.objects.create(
            portfolio=self.test_portfolio,
            stock=self.test_stock,
            quantity=100,
        )

        self.assertEqual(
            str(holding),
            f"{holding.stock.symbol} - {holding.quantity} - {holding.portfolio.name}",
        )

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

    def test_quantity_non_zero(self):
        """A Holding's quantity must not be equal to zero."""
        with self.assertRaises(IntegrityError):
            Holding.objects.create(
                portfolio=self.test_portfolio,
                stock=self.test_stock,
                quantity=0,
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


class PortfolioListViewTest(TestCase):
    def setUp(self):
        self.portfolio_names = [
            "Pedro's Piggy Bank",
            "Agustín's Ferocious Fund",
            "Omar's Last-minute Investments",
            "Andrés' Magic Money Making Machine",
        ]

        for name in self.portfolio_names:
            Portfolio.objects.create(name=name)

    def test_portfolio_list_view(self):
        portfolios = Portfolio.objects.all()

        response = self.client.get("/portfolios/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "portfolios/portfolio_list.html")
        self.assertContains(response, "Portfolios")

        for portfolio in portfolios:
            self.assertContains(response, portfolio.name)

        self.assertQuerysetEqual(response.context["portfolios"], portfolios)
