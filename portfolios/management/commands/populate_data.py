from django.core.management.base import BaseCommand
from faker import Faker
from portfolios.models import Portfolio, Stock, Holding
from tqdm import tqdm
import random


class Command(BaseCommand):
    help = "Populate the database with fake data"

    def handle(self, *args, **kwargs):
        fake = Faker()

        total_stocks = 200
        total_portfolios = 10

        print("Creating fake data...")

        # Create fake stocks
        stocks = []
        for _ in tqdm(range(total_stocks), desc="Creating stocks", unit="stock"):
            symbol = "".join(fake.random_letters(length=6)).upper()
            date = fake.date_between(start_date="-1y", end_date="today")
            try:
                stock = Stock.objects.create(symbol=symbol)
                # Implicitly create a price by calling the `price` method
                stock.price(date)
                stocks.append(stock)
            except Exception as e:
                # Skip possible IntegrityError due to unique constraint violation
                continue

        # Create fake portfolios
        portfolios = []
        for _ in tqdm(
            range(total_portfolios), desc="Creating portfolios", unit="portfolio"
        ):
            portfolio_name = fake.sentence(nb_words=4)
            portfolio = Portfolio.objects.create(name=portfolio_name)
            portfolios.append(portfolio)

        # Create holdings for each portfolio using the existing stocks
        for portfolio in tqdm(portfolios, desc="Creating holdings", unit="holding"):
            for stock in random.sample(stocks, random.randint(1, 10)):
                quantity = random.randint(1, 100)
                try:
                    Holding.objects.create(
                        portfolio=portfolio, stock=stock, quantity=quantity
                    )
                except Exception as e:
                    # Skip possible IntegrityError due to unique constraint violation
                    continue
