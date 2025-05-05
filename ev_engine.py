import numpy as np
from scipy.integrate import quad
import QuantLib as ql
from datetime import date

# Build log-normal risk-neutral PDF
def build_density(spot, rate, iv, eval_date):
    today = ql.Date().todaysDate()
    ed = ql.Date(eval_date.day, eval_date.month, eval_date.year)
    T = (ed - today) / 365.0
    mu = np.log(spot) + (rate - 0.5 * iv**2) * T
    sigmaT = iv * np.sqrt(T)
    def pdf(ST):
        return (1/(ST*sigmaT*np.sqrt(2*np.pi))
                * np.exp(- (np.log(ST)-mu)**2/(2*sigmaT**2)))
    return pdf

# Price a leg (intrinsic if expired, else BS theoretical)
def price_leg(leg, ST, rate, eval_date):
    K, qty, kind = leg["strike"], leg["qty"], leg["type"]
    expiry = leg["expiry"]
    iv = leg.get("iv", None) or leg.get("iv_seed", None)
    # intrinsic if expired
    if expiry <= eval_date:
        payoff = max(ST-K, 0) if kind == "call" else max(K-ST, 0)
        return qty * payoff
    # else Black-Scholes
    ed = ql.Date(eval_date.day, eval_date.month, eval_date.year)
    ex = ql.Date(expiry.day, expiry.month, expiry.year)
    T = ql.Actual365Fixed().yearFraction(ed, ex)
    # use iv provided
    sigma = iv
    d1 = (np.log(ST/K) + (rate + 0.5*sigma**2)*T) / (sigma*np.sqrt(T))
    d2 = d1 - sigma*np.sqrt(T)
    nd1 = 0.5*(1 + np.math.erf(d1/np.sqrt(2)))
    nd2 = 0.5*(1 + np.math.erf(d2/np.sqrt(2)))
    df = np.exp(-rate*T)
    if kind == "call":
        price = ST*nd1 - K*df*nd2
    else:
        price = K*df*(1-nd2) - ST*(1-nd1)
    return qty * price

# Portfolio value at ST for eval_date
def portfolio_value(legs, ST, rate, eval_date):
    return sum(price_leg(leg, ST, rate, eval_date) for leg in legs)

# Expected value integration
def expected_value(legs, spot, rate, iv_atm, eval_date):
    pdf = build_density(spot, rate, iv_atm, eval_date)
    cost0 = sum(l["qty"] * l["price"] for l in legs)
    integrand = lambda ST: (portfolio_value(legs, ST, rate, eval_date) - cost0) * pdf(ST)
    EV, _ = quad(integrand, 0, spot * 3)
    return EV

# Expected return normalizes by absolute cost
def expected_return(EV, legs):
    cost0 = sum(l["qty"] * l["price"] for l in legs)
    return EV / abs(cost0)
