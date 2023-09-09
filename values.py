from pymongo import MongoClient
import random
from datetime import datetime, timedelta
# Connect to the MongoDB database
client = MongoClient('mongodb://localhost:27017/')
db = client['gourdstock']
value_collection = db['value']
trends_collection = db['trends']


today = (datetime.today() + timedelta(-1)).strftime('%Y-%m-%d')
if (datetime.today().weekday() == 4):
    tomorrow = (datetime.today() + timedelta(3)).strftime('%Y-%m-%d')
elif (datetime.today().weekday() == 5):
    tomorrow = (datetime.today() + timedelta(2)).strftime('%Y-%m-%d')
else:
    tomorrow = (datetime.today() + timedelta(1)).strftime('%Y-%m-%d')


def calculate_demand(unsold_stocks, total_stocks):
    """
    Calculate the demand factor.
    """
    demand = total_stocks / (unsold_stocks + (total_stocks / 3))
    return demand


def update_values():
    """
    Update stock values and market caps.
    """
    for value_document in value_collection.find():
        ticker = value_document['ticker']
        unsold_stocks = int(value_document['unsold stocks'])
        total_stocks = int(value_document['total stocks'])

        # Retrieve the current stock value
        current_value = float(value_document['value'])

        # Retrieve the demand factor using the calculate_demand method
        demand_factor = calculate_demand(unsold_stocks, total_stocks)

        # Generate the random factor
        random_factor = random.uniform(-9, 10)

        # Retrieve the trend factor from the trends database
        trend_document = trends_collection.find_one(
            {'ticker': ticker})
        current_trend = float(trend_document['current'])
        today_trend = float(
            trend_document[today])
        tomorrow_trend = float(
            trend_document[tomorrow])

        # Calculate new value for the trend
        new_trend = current_trend + ((tomorrow_trend - today_trend) / 391)

        # Update the trend in the database
        trends_collection.update_one(
            {'ticker': ticker},
            {'$set': {'current': new_trend}}
        )

        trend_factor = new_trend
        # Arbitrary denominator value used to adjust the overall curve
        denom = 5000

        # Next Value = (Current * (1 + (Demand / XXXX) + (Modifier / XXXX) + (Random / XXXX)))
        new_value = current_value * \
            (1 + (demand_factor / denom) +
             (trend_factor / denom) + (random_factor / denom))

        # Calculate the new market cap using the new value
        new_market_cap = new_value * total_stocks

        # Update the value and market cap in the database
        value_collection.update_one(
            {'ticker': ticker},
            {'$set': {'value': new_value, 'market cap': new_market_cap}}
        )


def update_daily_trends():
    """
    Update daily-level trends data.
    """
    for trend_document in trends_collection.find():
        today_value = trend_document[today]

        # Update the current value with today's value
        trends_collection.update_one(
            {'ticker': trend_document['ticker']},
            {'$set': {'current': today_value}}
        )


if __name__ == '__main__':
    update_values()
