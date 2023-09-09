from flask import Flask, render_template, request, jsonify
import json
import values
from pymongo import MongoClient

app = Flask(__name__)

# MongoDB connection
client = MongoClient('mongodb://localhost:27017/')
db = client['gourdstock']
value_collection = db['value']
users_collection = db['users']


@app.route('/')
def dashboard():
    # Retrieve all documents from the 'value' collection
    value_documents = list(value_collection.find())
    return render_template('dashboard.html', value_documents=value_documents)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check if the username already exists
        if users_collection.find_one({'username': username}):
            return render_template('message.html', message="Username already exists. Please choose another username.")

        # Create a new user document with default values
        new_user = {
            'username': username,
            'password': password,
            'balance': 10000,
            'owned stocks': {}
        }

        # Insert the new user into the 'users' collection
        users_collection.insert_one(new_user)

        return render_template('message.html', message="Registration successful!")

    return render_template('registration.html')


@app.route('/purchase', methods=['GET', 'POST'])
def purchase():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        ticker = request.form['ticker']
        amount = int(request.form['amount'])

        # Check if the user exists and the password is correct
        user = users_collection.find_one(
            {'username': username, 'password': password})

        if user:
            # Check if the stock ticker exists in the 'value' collection
            stock = value_collection.find_one({'ticker': ticker})

            if stock and amount > 0 and stock['unsold stocks'] >= amount:
                stock_value = stock['value']
                stock_cost = float(stock_value) * int(amount)
                # Check if the user has enough balance to purchase the stocks
                if int(user['balance']) >= float(stock_cost):
                    # Update the user's balance and owned stocks
                    if ticker not in user['owned stocks']:
                        users_collection.update_one(
                            {'_id': user['_id']},
                            {
                                '$set': {f'owned stocks.{ticker}': 0}
                            }
                        )

                    users_collection.update_one(
                        {'_id': user['_id']},
                        {
                            '$inc': {'balance': -stock_cost, 'owned stocks.' + ticker:  amount}
                        }
                    )
                    value_collection.update_one(
                        {'ticker': ticker}, {'$inc': {'unsold stocks': -amount}})

                    return render_template('message.html', message=f"Purchase successful! Bought {amount} shares of {ticker} for ${stock_cost:.2f} ")
                else:
                    render_template(
                        'message.html', message="Insufficient balance to purchase the stocks.")
            else:
                return render_template('message.html', message="Invalid stock ticker or amount.")
        else:
            return render_template('message.html', message="Invalid username or password.")

    return render_template('purchase.html')


@app.route('/sell', methods=['GET', 'POST'])
def sell():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        ticker = request.form['ticker']
        amount = int(request.form['amount'])

        # Check if the user exists and the password is correct
        user = users_collection.find_one(
            {'username': username, 'password': password})
        if user:
            if value_collection.find_one({'ticker': ticker}):
                # Check if the user has the specified stock
                if ticker in user['owned stocks']:
                    current_stock_amount = user['owned stocks'][ticker]

                    # Check if the user has enough of the specified stock to sell

                    if current_stock_amount >= amount:
                        # Retrieve the current stock value from the 'value' collection
                        stock_info = value_collection.find_one(
                            {'ticker': ticker})
                        stock_value = float(stock_info['value'])

                        # Calculate the total earnings from selling the stock
                        earnings = stock_value * amount
                        new_stock = current_stock_amount - amount
                        # Update the user's balance and reduce the number of owned stocks
                        if new_stock == 0:
                            users_collection.update_one(
                                {'_id': user['_id']},
                                {
                                    '$inc': {'balance': earnings},
                                    '$unset': {'owned stocks.' + ticker: current_stock_amount - amount}
                                }
                            )
                        else:
                            users_collection.update_one(
                                {'_id': user['_id']},
                                {
                                    '$inc': {'balance': earnings},
                                    '$set': {'owned stocks.' + ticker: current_stock_amount - amount}
                                }
                            )
                        value_collection.update_one(
                            {'ticker': ticker},
                            {
                                '$inc': {'unsold stocks': amount}
                            }
                        )
                        return render_template('message.html', message=f"Sale successful! Earned ${earnings:.2f} USD.")
                    else:
                        return render_template('message.html', message='Not enough stocks to sell.')
                else:
                    return render_template('message.html', message=f"You don't own {ticker} stocks.")
            else:
                return render_template('message.html', message=f"Stock {ticker} does not exist.")
        else:
            return render_template('message.html', message="Invalid username or password.")

    # Render the sell page
    return render_template('sell.html')


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check if the user exists and the password is correct
        user = users_collection.find_one(
            {'username': username, 'password': password})

        if user:
            return render_template('profile.html', user_data=user)

        return render_template(
            'message.html', message="Invalid username or password.")

    return render_template('profile.html', user_data=None)


@app.route('/about', methods=['GET', 'POST'])
def about():
    return render_template('about.html', user_data=None)


@app.route('/leaderboard')
def leaderboard():
    # Query the users collection to retrieve user data
    users_data = users_collection.find()

    # Create a dictionary to store user total wealth
    user_wealth = []

    # Calculate the total wealth for each user
    for user in users_data:
        username = user['username']
        balance = float(user['balance'])
        owned_stocks = user['owned stocks']

        total_stock_value = 0.0

        # Calculate the total value of owned stocks
        for ticker, amount in owned_stocks.items():
            stock_info = value_collection.find_one({'ticker': ticker})
            if stock_info:
                stock_value = float(stock_info['value'])
                total_stock_value += stock_value * amount

        if ('title' in user):
            title = user['title']
        else:
            title = -1

        total_wealth = balance + total_stock_value
        user_wealth.append({'username': username, 'net worth': total_wealth,
                           'liquid': balance, 'invested': total_stock_value, 'title': title})

    # Sort users by total wealth in descending order
    top_users = sorted(
        user_wealth,  key=lambda x: x['net worth'], reverse=True)[:10]

    # Render the leaderboard template with the top_users data

    return render_template('leaderboard.html', top_users=top_users)


@app.route('/update_data')
def update_data():
    value_documents = list(value_collection.find())

    # Convert ObjectId to string for each document
    for document in value_documents:
        document['_id'] = str(document['_id'])

    return jsonify({'value_documents': value_documents})


if __name__ == '__main__':
    app.run(debug=True)
