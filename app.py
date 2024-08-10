import os
import datetime
import sqlalchemy

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    user_id = session["user_id"]
    transactions_db = db.execute("SELECT symbol,shares , price FROM TRANSACTIONS WHERE user_id =?",user_id)
    cash_db = db.execute("SELECT cash FROM users WHERE id =?",user_id)
    cash =cash_db[0]["cash"]

    return render_template("index.html",transactions=transactions_db,cash =cash)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    if request.method =="GET":
        return render_template("buy.html")
    else:
        stock_symbol =request.form.get("stock_symbol")
        number_of_stocks= request.form.get("number_of_stocks")

        stock = lookup(stock_symbol.upper())
        if stock == None:
            return apology("Not a valid stock symbol")
        if int(number_of_stocks) < 0:
            return apology("Shares cannot be negative")
        transaction_value = int(number_of_stocks) *stock["price"]
        cash =db.execute("SELECT cash FROM users WHERE id =?",session["user_id"])
        user_cash = cash[0]["cash"]
        if user_cash < transaction_value:
            return apology("Not enough money")
        db.execute("UPDATE users SET cash = cash - ? WHERE id = ?",transaction_value,session["user_id"])
        time = datetime.datetime.now()

        db.execute("INSERT INTO transactions(user_id,symbol,shares,price,date) VALUES(?,?,?,?,?)",session["user_id"],stock["symbol"],number_of_stocks,stock["price"],time)
        flash("bought!")


        return redirect("/")





@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    return apology("TODO")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    if request.method == "GET":
        return render_template("stockquote.html")
    else:
        stockquote = request.form.get("stockquote")
        if not stockquote:
            return apology("Must provide a stock symbol")

        stock_data = lookup(stockquote.upper())
        if stock_data == None:
            return apology("Not a valid stock symbol")

        return render_template("stock_data.html",stock_data=stock_data)



@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "GET":
        return render_template("register.html")
    else:
        username = request.form.get("username")
        password = request.form.get("password")
        re_enter_password =request.form.get("re_enter_password")
        hash = generate_password_hash(password)
        rows = db.execute("SELECT * FROM users WHERE username = ?",username)

        if not username:
            return apology("Username field cannot be left blank")
        elif not password:
            return apology("Password field cannot be left blank")
        elif not re_enter_password:
            return apology("re_enter_password field cannot be left blank")
        elif password != re_enter_password:
            return apology("passwords do not match")
        elif len(rows)>0:
            return apology("username already taken")

        db.execute("INSERT INTO users(username,hash) VALUES(?,?)",username,hash)
        new_user=db.execute("SELECT id  FROM USERS where username = ?",username)

        session["user_id"] = new_user[0]["id"]
        return redirect("/")








@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    if request.method =="GET":
        user_id = session["user_id"]
        symbols_user= db.execute("SELECT symbol FROM transactions WHERE user_id = :id GROUP BY symbol HAVING SUM(shares) > 0",id =user_id )
        return render_template("sell.html",symbols = [row["symbol"] for row in symbols_user])

    else:
        stock_symbol =request.form.get("symbol")
        number_of_stocks= request.form.get("number_of_stocks")
        user_id = session["user_id"]

        stock = lookup(stock_symbol.upper())
        if stock == None:
            return apology("Not a valid stock symbol")
        if int(number_of_stocks) < 0:
            return apology("Shares cannot be negative")
        transaction_value = int(number_of_stocks) *stock["price"]
        cash =db.execute("SELECT cash FROM users WHERE id =?",session["user_id"])
        user_cash = cash[0]["cash"]

        user_shares = db.execute("SELECT shares FROM transactions WHERE user_id =? AND symbol =? GROUP BY symbol",user_id,stock_symbol)
        user_shares_real = user_shares[0]["shares"]
        if int(number_of_stocks) > user_shares_real:
            return apology("You donot have enough shares")

        db.execute("UPDATE users SET cash = cash + ? WHERE id = ?",transaction_value,session["user_id"])
        time = datetime.datetime.now()
        transactions_db = db.execute("SELECT shares FROM TRANSACTIONS WHERE user_id =? AND symbol =",user_id,stock_symbol)
        new_shares = transactions_db[0]["shares"] -int(number_of_stocks)
        db.execute("UPDATE transactions SET shares =  ? WHERE id = ? AND symbol = ?",new_shares,user_id,stock_symbol)
        flash("Sold")


        return redirect("/")


if __name__ == '__main__':
    app.debug = True
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)