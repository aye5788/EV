import streamlit as st
import pandas as pd
from datetime import date
from data import get_spot, get_iv_surface, get_rate
from ev_engine import expected_value, expected_return

st.title("🧮 EV/ER Calculator for Option Spreads")

# — Underlying & spot
symbol = st.text_input("Underlying symbol", value="SPY")
if symbol:
    spot = get_spot(symbol)
    st.write(f"Current spot: **${spot:.2f}**")

# — Risk‑free rate
rate = st.number_input("Risk‑free rate (annual)", value=float(get_rate()), format="%.4f")

# — Define legs
st.markdown("### Define your legs")
default_leg = {"type":"call","strike":spot*1.01,"expiry":date.today(),"qty":1,"price":0.0,"iv":0.2}
legs_df = st.experimental_data_editor(
    pd.DataFrame([default_leg]),
    num_rows="dynamic",
    column_config={
      "type": st.ColumnConfig(type="select", options=["call","put"]),
      "expiry": st.ColumnConfig(type="date")
    }
)

# — Evaluation dates
st.markdown("### Evaluation dates")
today = date.today()
dates = pd.date_range(today, today.replace(day=min(today.day+30,28))).date
eval_dates = st.multiselect("Choose dates", options=dates, default=[today, dates[len(dates)//2]])

# — Calculate
if st.button("Calculate EV/ER"):
    if not eval_dates:
        st.error("Select at least one evaluation date")
    else:
        iv_surf = get_iv_surface(symbol, eval_dates[-1].isoformat())
        iv_atm = iv_surf["vol50"]
        legs = legs_df.to_dict("records")
        results = []
        for d in eval_dates:
            EV = expected_value(legs, spot, rate, iv_atm, d)
            ER = expected_return(EV, legs)
            results.append({"Date":d, "EV ($)":round(EV,2), "ER (%)":f"{ER:.1%}"})
        st.table(pd.DataFrame(results))

# — P/L curve for first eval date
if eval_dates:
    d0 = eval_dates[0]
    iv_atm = get_iv_surface(symbol, d0.isoformat())["vol50"]
    from ev_engine import build_density, portfolio_value
    pdf = build_density(spot, rate, iv_atm, d0)
    STs = list(spot * (x/100) for x in range(50, 151, 5))
    cost0 = sum(l["qty"]*l["price"] for l in legs_df.to_dict("records"))
    PnL = [portfolio_value(legs_df.to_dict("records"), stp, rate, d0) - cost0 for stp in STs]
    import plotly.express as px
    df = pd.DataFrame({"Underlying Price":STs, "P/L":PnL})
    fig = px.line(df, x="Underlying Price", y="P/L", title=f"P/L at {d0}")
    st.plotly_chart(fig)
