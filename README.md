# 📊 Samy's Django Portfolio Project
This project is a simple-yet-complete implementation of a **Portfolio** model for managing a collection of stocks, created in Django. The main feature is the ability to calculate the **profit** and **annualized return** of the portfolio between two dates.

## 🤔 The Problem
The problem statement is as follows:

> Construct a simple `Portfolio` class that has a collection of `Stocks` and a `Profit` method that receives 2 dates and returns the profit of the `Portfolio` between those dates.
> Assume each `Stock` has a `Price` method that receives a date and returns its price.
>
> **Bonus Track**: make the `Profit` method return the "annualized return" of the portfolio between the given dates.

## 💡 Solution Overview
I devised a solution consisting of four entities, which are implemented as Django models:

- `Portfolio`: A collection of stock holdings that implements the requested methods.
- `Stock`: A stock with a unique symbol and historical prices, and whose shares can be held in portfolios.
- `StockPrice`: The historical price of a stock on a given date.
- `Holding`: Links a stock to a portfolio with the quantity of shares. (Basically, an [N-to-N model](https://en.wikipedia.org/wiki/Many-to-many_(data_model))).

These models can be found in [`portfolios/models.py`](portfolios/models.py), and their tests are in [`portfolios/tests.py`](portfolios/tests.py).

### 🤦 What part of ***simple*** didn't you understand? Isn't Django overkill?
Totally! A complying solution could have been as simple as:

```python
class Stock:
    def price(self, date):
        random.seed(f"{date}")
        return random.uniform(1, 1000)

class Portfolio:
    def __init__(self):
        self.stocks = [Stock() for _ in range(100)]

    def profit(self, start_date, end_date):
        v_i = sum(stock.price(start_date) for stock in self.stocks)
        v_f = sum(stock.price(end_date) for stock in self.stocks)
        days = (end_date - start_date).days
        profit = v_f - v_i
        ann_return = (v_f / v_i) ** (365 / days) - 1
        return profit, ann_return
```
(Or maybe even shorter)

Nevertheless, I chose to use Django for the following reasons:

- It is part of Fintual's stack 👀, and it is mentioned in the job offer.
- I'm familiar with it, and it's quick to set up.
- It provides a nice ORM and a shell to interact with the models.
- It allows for easy testing and debugging.
- It's easy to extend and add more features in the future.

And last but not least, this seemed like a really fun project for the weekend! 🎉

## 🚀 Setup

Once you have cloned the repository and navigated to the project's root directory, there are 2 ways to set up the project:

### Option 1: Using Docker 🐳 (Recommended) 
```bash
docker-compose up --build
```
This will build the Docker image and start the Django server on [`http://localhost:8000`](http://localhost:8000).

It might take a few seconds, cause it will:  
✅ Install the dependencies (only the first time)  
✅ Run the migrations  
✅ Create fake data  
✅ Create a superuser with the username `admin` and password `hunter2`  
✅ Run the server  

If you want to run the tests, you can do so by running:
```bash
docker compose run portfolios-web python manage.py test
```

### Option 2: Manual Setup 🛠️ (The good ol' fashioned way)

#### 1. Set Up the Environment
```bash
python3 -m venv env
source env/bin/activate  # For Windows: env\Scripts\activate
pip install -r requirements.txt
```

#### 2. Run Migrations
```bash
python manage.py migrate
```

#### 4. Run tests (Optional)
```bash
python manage.py test
```

##### 5. Populate the database with fake data (Optional)
```bash
python manage.py populate_data
```

#### 6. Create a superuser (Optional)
```bash
python manage.py createsuperuser
```

#### 7. Start the Django app
```bash
python manage.py runserver
```

## 👨‍💻 Usage

There are several, non-exclusive ways to interact with the project:

### 1. Web app
Once the project is running, navigate to [`http://localhost:8000`](http://localhost:8000). If there is data, you should see a list of portfolios, like this:

<img src="https://github.com/user-attachments/assets/b6cda930-154b-4ee1-acb2-b3468a87cb2e" width="500">

When inside a portfolio, there is a summary of its current value, and a form for calculating its profit:

<img src="https://github.com/user-attachments/assets/d28d3eab-a174-412d-ae28-1414607fc446" width="500">

Once submitted, you get the results along with a table detailing the performance of each stock:

<img src="https://github.com/user-attachments/assets/2f4b6fd4-d3ed-4076-aeea-135810b469ae" width="500">

### 2. Django Admin
Assuming you used Docker, if you want to manually interact with the models, navigate to [`http://localhost:8000/admin`](http://localhost:8000/admin) and log in with:

- Username: `admin`
- Password: `hunter2`

If not using Docker, you should [create a super user first](#6-create-a-superuser-optional). 

There you can see the models and interact with them:

<img src="https://github.com/user-attachments/assets/51ea2b41-bd03-4c23-9af1-4f18c10af44d" width="500">

### 3. Django Shell

If you are using Docker and the service is running, run:

```bash
docker compose exec -it portfolios-web python manage.py shell
```

Or, locally, just run:

```bash
python manage.py shell
```

Once in the Django shell, you can use Django models' [queryset API](https://docs.djangoproject.com/en/4.2/ref/models/querysets/) to create and interact with model instances.

Example:

```python
from portfolios.models import Portfolio, Stock, StockPrice, Holding
from datetime import date

# Create a portfolio
portfolio = Portfolio.objects.create(name='Samy G')

# Create a stock
stock = Stock.objects.create(symbol='JUEMES')

# (Optional) Add historical prices to the stock
StockPrice.objects.create(stock=stock, date=date(2016, 9, 18), price=100)

# Add 10 shares of the stock to the portfolio
Holding.objects.create(portfolio=portfolio, stock=stock, quantity=10)

# Calculate the profit between two dates
profit, ann_return = portfolio.profit(date(2016, 9, 18), date(2016, 9, 20))
```

## 🗯️ Assumptions
Since this project is a test for a fictional scenario, I made several assumptions to simplify the development:

- The value of a portfolio is calculated based on its **current** holdings. This means there is no historical information about the portfolio or its "transactions" (when shares of a stock are acquired or sold).
- Stock prices do not change during the same day.
- Stocks will always have a price for any date that is not in the future.
- Attempting to obtain the price of a stock for a future date, as tempting as it may be, will raise an exception.
- Stock prices can be safely stored as Decimal numbers with four decimal places.
    - The minimum price is 0.0001, and the maximum price is 999,999.9999. This is arbitrary, but it is based on [the minimum increment of the US stock market ($0.0001)](https://quant.stackexchange.com/a/60543) and the order of magnitude of the most expensive stock ever ([Berkshire Hathaway, around $628,900](https://en.wikipedia.org/wiki/Share_price#List_of_historical_highest-priced_publicly_traded_shares)).
- There is no need to support multiple currencies or localization. For the sake of simplicity, we can assume all prices are in USD.

## 🤖 AI Use Disclaimer
While developing this project, I used AI tools (namely, ChatGPT, DeepSeek and GitHub Copilot) primarily for the following:

- Generating the initial version of docstrings and documents (such as this README!)
- Checking grammar and overall writing
- Generating specific chunks of code
- Styling the front end
- Providing suggestions

In any case, none of the suggestions were accepted verbatim without proper checking, so everything is hand-tailored as in the merry old times.

## 📜 License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
