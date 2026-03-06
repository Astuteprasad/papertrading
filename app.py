from flask import Flask, render_template, redirect, url_for, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
import random
import json

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'supersecretkey'

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


# ==========================
# MODELS
# ==========================

class User(UserMixin, db.Model):

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(150), unique=True, nullable=False)

    password = db.Column(db.String(150), nullable=False)

    risk_level = db.Column(db.String(50))

    income = db.Column(db.String(50))

    purpose = db.Column(db.String(100))

    experience = db.Column(db.String(50))


class Strategy(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100))

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    legs_data = db.Column(db.Text)


with app.app_context():
    db.create_all()


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ==========================
# SIMULATED MARKET DATA
# ==========================

prices = {
    "AAPL": 150.0,
    "TSLA": 700.0,
    "NIFTY50": 18000.0,
    "RELIANCE": 2400.0,
    "GOOGLE": 2800.0
}


def simulate_prices():

    for stock in prices:

        drift = random.uniform(-1, 1)

        noise = random.uniform(-0.5, 0.5)

        prices[stock] += drift + noise

        prices[stock] = round(prices[stock], 2)


# ==========================
# ROUTES
# ==========================

@app.route('/')
def index():
    return redirect(url_for('login'))


# REGISTER
@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        username = request.form['username']

        password = request.form['password']

        if User.query.filter_by(username=username).first():
            return "User already exists!"

        user = User(
            username=username,
            password=password
        )

        db.session.add(user)

        db.session.commit()

        return redirect(url_for('login'))

    return render_template('register.html')


# LOGIN
@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        username = request.form['username']

        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and user.password == password:

            login_user(user)

            return redirect(url_for('questionnaire'))

        return "Invalid credentials"

    return render_template('login.html')


# QUESTIONNAIRE
@app.route('/questionnaire', methods=['GET', 'POST'])
@login_required
def questionnaire():

    if request.method == 'POST':

        current_user.income = request.form.get('income')

        current_user.purpose = request.form.get('purpose')

        current_user.experience = request.form.get('experience')

        current_user.risk_level = request.form.get('risk')

        db.session.commit()

        return redirect(url_for('dashboard'))

    return render_template('questionnaire.html')


# DASHBOARD
@app.route('/dashboard')
@login_required
def dashboard():

    simulate_prices()

    return render_template(
        'dashboard.html',
        prices=prices,
        user=current_user
    )


# LIVE PRICE API
@app.route('/api/prices')
@login_required
def api_prices():

    simulate_prices()

    return jsonify(prices)


# STOCK PAGE
@app.route('/stock/<symbol>')
@login_required
def stock_page(symbol):

    simulate_prices()

    price = prices.get(symbol)

    if price is None:
        return "Stock not found"

    return render_template(
        'stock.html',
        symbol=symbol,
        price=price
    )


# OPTIONS PAGE
@app.route('/options')
@login_required
def options():
    return render_template('options.html')


# STRATEGY PAGE
@app.route('/strategy')
@login_required
def strategy():
    return render_template('strategy.html')


# STRATEGY DETAIL
@app.route('/strategy/<name>')
@login_required
def strategy_detail(name):
    return render_template('strategy_detail.html', name=name)


# STRATEGY BUILDER
@app.route('/strategy/builder')
@login_required
def strategy_builder():
    return render_template('strategy_builder.html')


# CALCULATE STRATEGY API
@app.route('/api/calculate_strategy', methods=['POST'])
@login_required
def calculate_strategy():

    data = request.get_json()

    legs = data.get("legs", [])

    base_price = prices.get("NIFTY50", 18000)

    spot_range = range(int(base_price - 2000), int(base_price + 2000), 50)

    pnl_values = []

    for spot in spot_range:

        total_pnl = 0

        for leg in legs:

            strike = float(leg["strike"])

            premium = float(leg["premium"])

            quantity = int(leg["quantity"])

            option_type = leg["type"]

            position = leg["position"]

            if option_type == "CALL":
                intrinsic = max(0, spot - strike)
            else:
                intrinsic = max(0, strike - spot)

            pnl = intrinsic - premium

            if position == "SELL":
                pnl *= -1

            total_pnl += pnl * quantity

        pnl_values.append(total_pnl)

    return jsonify({
        "spot": list(spot_range),
        "pnl": pnl_values
    })


# SAVE STRATEGY
@app.route('/api/save_strategy', methods=['POST'])
@login_required
def save_strategy():

    data = request.get_json()

    name = data.get("name")

    legs = data.get("legs")

    if not name or not legs:
        return jsonify({"error": "Invalid data"}), 400

    strategy = Strategy(
        name=name,
        user_id=current_user.id,
        legs_data=json.dumps(legs)
    )

    db.session.add(strategy)

    db.session.commit()

    return jsonify({"message": "Strategy saved successfully"})


# PORTFOLIO
@app.route('/portfolio')
@login_required
def portfolio():

    strategies = Strategy.query.filter_by(
        user_id=current_user.id
    ).all()

    return render_template(
        'portfolio.html',
        strategies=strategies
    )


# TRADE OPTIONS
@app.route("/trade-options/<symbol>")
@login_required
def trade_options(symbol):

    return render_template(
        "trade_options.html",
        symbol=symbol
    )


# LOGOUT
@app.route('/logout')
@login_required
def logout():

    logout_user()

    return redirect(url_for('login'))


if __name__ == "__main__":
    app.run(debug=True)