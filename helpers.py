from scipy.stats import norm
from math import log, sqrt, exp, isinf


def usd(value):
    """Format value as USD."""
    return f"${value:,.3f}"

# calculates implied volatility of a stock option


def dividendIV(call: bool, S: float, K: float, T: float, R: float, q: float, value: float):
    guess = 2.5066 / sqrt(T) * value / S
    a = DividendOption(call, S, K, T, R, q, guess)
    price = a.price()
    # Tolerance bound for the difference between the calculated and actual price
    tol = 1e-10
    # Newton's method
    while abs(value-price) > tol:
        guess1 = guess - (price-value) / (a.vega() * 100)
        # Handling unstabilities
        if guess1 < 0 or isinf(guess1):
            guess1 = guess
            break
        a = DividendOption(call, S, K, T, R, q, guess1)
        price = a.price()
        guess = guess1
    return guess

# calculates implied volatility of a futures option


def futuresIV(call: bool, S: float, K: float, T: float, R: float, value: float):
    guess = 2.5066 / sqrt(T) * value / S
    a = FuturesOption(call, S, K, T, R, guess1)
    price = a.price()
    # Tolerance bound for the difference between the calculated and actual price
    tol = 1e-8
    # Newton's method
    while abs(value-price) > tol:
        guess1 = guess - (price-value) / (a.vega() * 100)
        # Handling unstabilities
        if guess1 < 0 or isinf(guess1):
            guess1 = guess
            break
        a = DividendOption(call, S, K, T, R, guess1)
        price = a.price()
        guess = guess1
    return guess

# calculates implied volatility of an FX option


def fxIV(call: bool, S: float, K: float, T: float, R: float, fr: float, value: float):
    guess = 2.5066 / sqrt(T) * value / S
    a = DividendOption(call, S, K, T, R, fr, guess)
    price = a.price()
    # Tolerance bound for the difference between the calculated and actual price
    tol = 1e-5
    # Newton's method
    while abs(value-price) > tol:
        guess1 = guess - (price-value) / (a.vega() * 100)
        # Handling unstabilities
        if guess1 < 0 or isinf(guess1):
            guess1 = guess
            break
        a = DividendOption(call, S, K, T, R, fr, guess1)
        price = a.price()
        guess = guess1
    return guess

# Parent class


class Option:
    # Initializing with inputs to Black Scholes for a Vanilla European stock option
    def __init__(self, call: bool, S: float, K: float, T: float, R: float, sigma: float):
        self.call = call
        self.S = S
        self.K = K
        self.t = T
        self.R = R
        self.sigma = sigma
        self.d1 = (log(self.S / self.K) + R * self.t + (self.sigma ** 2 * self.t / 2))\
            / (sigma * sqrt(self.t))
        self.d2 = self.d1 - self.sigma * sqrt(self.t)
        self.nd1 = norm.cdf(self.d1)
        self.nd2 = norm.cdf(self.d2)
        self.pdfd1 = norm.pdf(self.d1)
        # The delta to take derivatives
        self.diff = 1e-5

    def price(self):
        callprice = self.S * self.nd1 - self.K * exp(- self.R * self.t) * self.nd2
        if self.call:
            return callprice
        else:
            pvK = self.K / (1 + self.R) ** self.t
            return callprice + pvK - self.S

    # Calculating Greeks

    # dValue/dStrike
    def delta(self):
        return (Option(self.call, self.S + self.diff, self.K, self.t, self.R, self.sigma).price()
                - self.price()) / self.diff

    # d^2Value/dStrike^2
    def gamma(self):
        return (Option(self.call, self.S + self.diff, self.K, self.t, self.R, self.sigma).delta()
                - self.delta()) / self.diff

    # dValue/dTime (Time in calendar days)
    def theta(self):
        return (self.price() - Option(self.call, self.S, self.K, self.t + self.diff, self.R,
                self.sigma).price()) / self.diff / 365

    # dValue/dVolatility (per percentage point so we add /100)
    def vega(self):
        return (Option(self.call, self.S, self.K, self.t, self.R, self.sigma + self.diff).price()
                - self.price()) / self.diff / 100

    # dValue/dRiskfreeRate (per percentage point so we add /100)
    def rho(self):
        return (Option(self.call, self.S, self.K, self.t, self.R + self.diff, self.sigma).price()
                - self.price()) / self.diff / 100

    # Returns all greeks as a dictionary
    def greeks(self):
        return {"Delta": self.delta(), "Gamma": self.gamma(), "Theta": self.theta(),
                "Vega": self.vega(), "Rho": self.rho()}

# Incorporates a dividend yield to the calculation


class DividendOption(Option):
    def __init__(self, call: bool, S: float, K: float, T: float, R: float, q: float, sigma: float):
        super().__init__(call, S, K, T, R, sigma)
        # The dividend yield
        self.q = q
        # Adjusts Black Scholes solution accordingly
        self.d1 = (log(S / K) + (R - q) * self.t + (sigma ** 2 * self.t / 2)) / (sigma * sqrt(self.t))

    def price(self):
        if self.call:
            return self.S * exp(- self.q * self.t) * self.nd1 - self.K * exp(- self.R * self.t) * self.nd2
        else:
            return self.K * exp(- self.R * self.t) * norm.cdf(- self.d2) - self.S * exp(-self.q * self.t) * norm.cdf(- self.d1)

    def delta(self):
        return (DividendOption(self.call, self.S + self.diff, self.K, self.t, self.R, self.q, self.sigma).price() -
                self.price()) / self.diff

    def gamma(self):
        return (DividendOption(self.call, self.S + self.diff, self.K, self.t, self.R, self.q, self.sigma).delta() -
                self.delta()) / self.diff

    def theta(self):
        return (self.price() - DividendOption(self.call, self.S, self.K, self.t + self.diff, self.R, self.q,
                self.sigma).price()) / self.diff / 365

    def vega(self):
        return (DividendOption(self.call, self.S, self.K, self.t, self.R, self.q, self.sigma + self.diff).price()
                - self.price()) / self.diff / 100

    def rho(self):
        return (DividendOption(self.call, self.S, self.K, self.t, self.R + self.diff, self.q, self.sigma).price() -
                self.price()) / self.diff / 100

# The underlying is now a futures contract


class FuturesOption(Option):
    def __init__(self, call: bool, S: float, K: float, T: float, R: float, sigma: float):
        super().__init__(call, S, K, T, R, sigma)
        self.d1 = (log(self.S / self.K) + self.sigma ** 2 * self.t / 2) / (self.sigma * sqrt(self.t))
        self.d2 = self.d1 - self.sigma * sqrt(self.t)
        self.nd1 = norm.cdf(self.d1)
        self.nd2 = norm.cdf(self.d2)
        self.nnd1 = norm.cdf(- self.d1)
        self.nnd2 = norm.cdf(- self.d2)

    def price(self):
        if self.call:
            return exp(- self.R * self.t) * ((self.S * self.nd1) - self.K * self.nd2)
        else:
            return exp(- self.R * self.t) * ((self.K * self.nnd2) - self.S * self.nnd1)

    def delta(self):
        return (FuturesOption(self.call, self.S + self.diff, self.K, self.t, self.R, self.sigma).price() - self.price()) \
            / self.diff

    def gamma(self):
        return (FuturesOption(self.call, self.S + self.diff, self.K, self.t, self.R, self.sigma).delta() - self.delta()) \
            / self.diff

    def theta(self):
        return (self.price() - FuturesOption(self.call, self.S, self.K, self.t + self.diff, self.R, self.sigma).price()) \
            / self.diff / 365

    def vega(self):
        return (FuturesOption(self.call, self.S, self.K, self.t, self.R, self.sigma + self.diff).price() - self.price()) \
            / self.diff / 100

    def rho(self):
        return (FuturesOption(self.call, self.S, self.K, self.t, self.R + self.diff, self.sigma).price() - self.price()) \
            / self.diff / 100

# The underlying is now an excahange rate of two currencies


class ForexOption(Option):
    def __init__(self, call: bool, S: float, K: float, T: float, R: float, FR: float, sigma: float):
        super().__init__(call, S, K, T, R, sigma)
        self.FR = FR
        self.d1 = (log(self.S / self.K) + (self.R - self.FR) * self.t + self.sigma ** 2 * self.t / 2) / \
                  (self.sigma * sqrt(self.t))

    def price(self):
        if self.call:
            return self.S * exp(- self.FR * self.t) * self.nd1 - self.K * exp(- self.R * self.t) * self.nd2
        else:
            return self.K * exp(- self.R * self.t) * norm.cdf(- self.d2) - self.S * exp(- self.FR * self.t) * \
                norm.cdf(- self.d1)

    def delta(self):
        return (ForexOption(self.call, self.S + self.diff, self.K, self.t, self.R, self.FR, self.sigma).price() -
                self.price()) / self.diff

    def gamma(self):
        return (ForexOption(self.call, self.S + self.diff, self.K, self.t, self.R, self.FR, self.sigma).delta() -
                self.delta()) / self.diff

    def theta(self):
        return (self.price() - ForexOption(self.call, self.S, self.K, self.t + self.diff, self.R, self.FR,
                self.sigma).price()) / self.diff

    def vega(self):
        return (ForexOption(self.call, self.S, self.K, self.t, self.R, self.FR, self.sigma + self.diff).price() -
                self.price()) / self.diff / 100

    def rho(self):
        return (ForexOption(self.call, self.S, self.K, self.t, self.R + self.diff, self.FR, self.sigma).price() -
                self.price()) / self.diff / 100