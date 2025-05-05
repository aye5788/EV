import numpy as np
from scipy.integrate import quad
from datetime import date
import QuantLib as ql

def build_density(spot, rate, iv, eval_date):
    today = ql.Date().todaysDate()
    ql_eval = ql.Date(eval_date.day, eval_date.month, eval_date.year)
    T = (ql_eval - today) / 365.0
    mu = np.log(spot) + (rate - 0.5 * iv**2) * T
    sigmaT = iv * np.sqrt(T)
    def pdf(ST):
        return (1 / (ST * sigmaT * np.sqrt(2 * np.pi))
                * np.exp(- (np.log(ST) - mu)**2 / (2 * sigmaT**2)))
    return pdf

def price_leg(leg, ST, rate, eval_date):
    K, qty, kind, expiry, iv = (
        leg["strike"], leg["qty"], leg["type"], leg["expiry"], leg["iv"]
    )
    if expiry <= eval_date:
        payoff = max(ST - K, 0) if kind == "call" else max(K - ST, 0)
        return qty * payoff
    T = ql.Actual365Fixed().yearFraction(
        ql.Date(eval_date.day, eval_date.month, eval_date.year),
        ql.Date(expiry.day, expiry.month, expiry.year)
    )
    d1 = (np.log(ST/K) + (rate + 0.5 * iv**2) * T) / (iv * np.sqrt(T))
    d2 = d1 - iv * np.sqrt(T)
    nd1 = 0.5 * (1 + np.math.erf(d1/np.sqrt(2)))
    nd2 = 0.5 * (1 + np.math.erf(d2/np.sqrt(2)))
    df = np.exp(-rate * T)
    if kind == "call":
        price = ST * nd1 - K * df * nd2
    else:
        price = K * df * (1 - nd2) - ST * (1 - nd1)
    return qty * price

def portfolio_value(legs, ST, rate, eval_date):
    return sum(price_leg(leg, ST, rate, eval_date) for leg in legs)

def expected_value(legs, spot, rate, iv_atm, eval_date):
    pdf = build_density(spot, rate, iv_atm, eval_date)
    cost0 = sum(l["qty"] * l["price"] for l in legs)
    integrand = lambda ST: (portfolio_value(legs, ST, rate, eval_date) - cost0) * pdf(ST)
    EV, _ = quad(integrand, 0, spot * 3)
    return EV

def expected_return(EV, legs):
    cost0 = sum(l["qty"] * l["price"] for l in legs)
    return EV / abs(cost0)

