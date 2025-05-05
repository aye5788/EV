import requests
import streamlit as st

ALPHAVANTAGE_KEY = st.secrets["alphavantage"]["key"]
ORATS_TOKEN       = st.secrets["orats"]["token"]
FRED_API_KEY      = st.secrets.get("fred", {}).get("key", None)

def get_spot(symbol):
    url = (
      f"https://www.alphavantage.co/query?"
      f"function=GLOBAL_QUOTE&symbol={symbol}&apikey={ALPHAVANTAGE_KEY}"
    )
    resp = requests.get(url).json()
    return float(resp["Global Quote"]["05. price"])

def get_iv_surface(symbol, expiry):
    url = (
      "https://api.orats.io/datav2/monies/implied"
      f"?token={ORATS_TOKEN}"
      f"&ticker={symbol}"
      f"&fields=tradeDate,expirDate,stockPrice,vol95,vol75,vol50,vol25,vol10"
    )
    rec = requests.get(url).json()["data"][0]
    return {
      "expiry":       rec["expirDate"],
      "spotAtSample": rec["stockPrice"],
      "vol95":        rec["vol95"],
      "vol75":        rec["vol75"],
      "vol50":        rec["vol50"],  # ATM IV
      "vol25":        rec["vol25"],
      "vol10":        rec["vol10"],
    }

def get_rate():
    if not FRED_API_KEY:
        return 0.0
    url = (
      f"https://api.stlouisfed.org/fred/series/observations"
      f"?series_id=DTB3&api_key={FRED_API_KEY}&file_type=json&limit=1"
    )
    j = requests.get(url).json()
    return float(j["observations"][-1]["value"]) / 100.0
