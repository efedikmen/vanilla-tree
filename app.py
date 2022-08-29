import os
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp

from helpers import Option, DividendOption, FuturesOption, usd, dividendIV, futuresIV, fxIV

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Custom filter
app.jinja_env.filters["usd"] = usd

Session(app)


@app.route("/", methods=["GET", "POST"])
def index():
    # Redirecting user to the right screen according to underlying and the quantity to be calculated
    if request.method == "POST":
        underlying = request.form.get("underlying")
        if request.form["submit_btn"] == "price":
            if underlying == "Stock":
                return render_template("stockoptionprice.html")
            if underlying == "Futures":
                return render_template("futuresoptionprice.html")
            if underlying == "FX":
                return render_template("fxoptionprice.html")
        if request.form["submit_btn"] == "ivol":
            if underlying == "Stock":
                return render_template("stockiv.html")
            if underlying == "Futures":
                return render_template("futuresiv.html")
            if underlying == "FX":
                return render_template("fxiv.html")
        return render_template("index.html")
    return render_template("index.html")

# pricing stock options


@app.route("/stockoptionprice", methods=["GET", "POST"])
def stockoptionprice():
    if request.method == "POST":
        option_type = request.form.get("option type")
        if option_type not in ["Call", "Put"]:
            return render_template("error.html", error="403, option type {a} invalid".format(a=type(option_type)))
        # Retrieving user input and excepting value errors
        try:
            strike = float(request.form.get("strike"))
            spot = float(request.form.get("current"))
            rate = float(request.form.get("rate"))
            time = float(request.form.get("days"))
            vol = float(request.form.get("vol"))
            dividend = float(request.form.get("dividend"))
        except ValueError:
            return render_template("error.html", error="403, Value Error")
        # Divide user input for rates or days to match Black Scholes conveniencies
        if option_type == "Call":
            option = DividendOption(True, spot, strike, time/365, rate/100, dividend/100, vol/100)
        elif option_type == "Put":
            option = DividendOption(False, spot, strike, time/365, rate/100, dividend/100, vol/100)
        price = usd(option.price())
        greeks = option.greeks()
        greeks = {greek: round(value, 4) for (greek, value) in greeks.items()}
        return render_template("results.html", price=price, greeks=greeks)
    render_template("stockoptionprice.html")

# finding implied volatility of stock options


@app.route("/stockiv", methods=["GET", "POST"])
def stockiv():
    if request.method == "POST":
        option_type = request.form.get("option type")
        if option_type not in ["Call", "Put"]:
            return render_template("error.html", error="403, option type {a} invalid".format(a=type(option_type)))
        # Retrieving user input and excepting value errors
        try:
            strike = float(request.form.get("strike"))
            spot = float(request.form.get("current"))
            rate = float(request.form.get("rate"))
            time = float(request.form.get("days"))
            val = float(request.form.get("value"))
            dividend = float(request.form.get("dividend"))
        except ValueError:
            return render_template("error.html", error="403, Value Error")
        optype = (option_type == "Call")
        # Running Newton's method to find the IV
        iv = dividendIV(optype, spot, strike, time/365, rate/100, dividend/100, val)
        return render_template("resultsiv.html", iv=f"{iv*100:,.2f}%")
    render_template("stockiv.html")

# pricing futures options


@app.route("/futuresoptionprice", methods=["GET", "POST"])
def futuresoptionprice():
    if request.method == "POST":
        option_type = request.form.get("option type")
        if option_type not in ["Call", "Put"]:
            return render_template("error.html", error="403, option type {a} invalid".format(a=type(option_type)))
        # Retrieving user input and excepting value errors
        try:
            strike = float(request.form.get("strike"))
            spot = float(request.form.get("current"))
            rate = float(request.form.get("rate"))
            time = float(request.form.get("days"))
            vol = float(request.form.get("vol"))
        except ValueError:
            return render_template("error.html", error="403, Value Error")
        # Divide user input for rates or days to match Black Scholes conveniencies
        if option_type == "Call":
            option = FuturesOption(True, spot, strike, time/365, rate/100, vol/100)
        elif option_type == "Put":
            option = FuturesOption(False, spot, strike, time/365, rate/100, vol/100)
        price = usd(option.price())
        greeks = option.greeks()
        greeks = {greek: round(value, 4) for (greek, value) in greeks.items()}
        return render_template("results.html", price=price, greeks=greeks)
    render_template("futuresoptionprice.html")

# finding implied volatility of futures options


@app.route("/futuresiv", methods=["GET", "POST"])
def futuresiv():
    if request.method == "POST":
        option_type = request.form.get("option type")
        if option_type not in ["Call", "Put"]:
            return render_template("error.html", error="403, option type {a} invalid".format(a=type(option_type)))
        # Retrieving user input and excepting value errors
        try:
            strike = float(request.form.get("strike"))
            spot = float(request.form.get("current"))
            rate = float(request.form.get("rate"))
            time = float(request.form.get("days"))
            val = float(request.form.get("value"))
        except ValueError:
            return render_template("error.html", error="403, Value Error")
        optype = (option_type == "Call")
        # Running Newton's method to find the IV
        iv = dividendIV(optype, spot, strike, time/365, rate/100, val)
        return render_template("resultsiv.html", iv=f"{iv*100:,.2f}%")
    render_template("futuresiv.html")

# pricing fx options


@app.route("/fxoptionprice", methods=["GET", "POST"])
def fxoptionprice():
    if request.method == "POST":
        option_type = request.form.get("option type")
        if option_type not in ["Call", "Put"]:
            return render_template("error.html", error="403, option type {a} invalid".format(a=type(option_type)))
        # Retrieving user input and excepting value errors
        try:
            strike = float(request.form.get("strike"))
            spot = float(request.form.get("current"))
            rate = float(request.form.get("rate"))
            frate = float(request.form.get("frate"))
            time = float(request.form.get("days"))
            vol = float(request.form.get("vol"))
        except ValueError:
            return render_template("error.html", error="403, Value Error")
        # Divide user input for rates or days to match Black Scholes conveniencies
        if option_type == "Call":
            option = DividendOption(True, spot, strike, time/365, rate/100, frate/100, vol/100)
        elif option_type == "Put":
            option = DividendOption(False, spot, strike, time/365, rate/100, frate/100, vol/100)
        price = usd(option.price())
        greeks = option.greeks()
        greeks = {greek: round(value, 4) for (greek, value) in greeks.items()}
        return render_template("results.html", price=price, greeks=greeks)
    render_template("fxoptionprice.html")

# finding implied volatility of stock options


@app.route("/fxiv", methods=["GET", "POST"])
def fxiv():
    if request.method == "POST":
        option_type = request.form.get("option type")
        if option_type not in ["Call", "Put"]:
            return render_template("error.html", error="403, option type {a} invalid".format(a=type(option_type)))
        # Retrieving user input and excepting value errors
        try:
            strike = float(request.form.get("strike"))
            spot = float(request.form.get("current"))
            rate = float(request.form.get("rate"))
            time = float(request.form.get("days"))
            val = float(request.form.get("value"))
            frate = float(request.form.get("frate"))
        except ValueError:
            return render_template("error.html", error="403, Value Error")
        optype = (option_type == "Call")
        # Running Newton's method to find the IV
        iv = dividendIV(optype, spot, strike, time/365, rate/100, frate/100, val)
        return render_template("resultsiv.html", iv=f"{iv*100:,.2f}%")
    render_template("fxiv.html")