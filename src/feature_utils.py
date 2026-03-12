import numpy as np
import pandas as pd
import datetime
import yfinance as yf
import pandas_datareader.data as web
import requests
#from datetime import datetime, timedelta
import os
import sys

import os
import sys


# ... continue with your script ...

def extract_features():

    return_period = 5
    
    START_DATE = (datetime.date.today() - datetime.timedelta(days=365)).strftime("%Y-%m-%d")
    END_DATE = datetime.date.today().strftime("%Y-%m-%d")
    stk_tickers = ['MSFT', 'IBM', 'GOOGL']
    ccy_tickers = ['DEXJPUS', 'DEXUSUK']
    idx_tickers = ['SP500', 'DJIA', 'VIXCLS']
    
    stk_data = yf.download(stk_tickers, start=START_DATE, end=END_DATE, auto_adjust=False)
    #stk_data = web.DataReader(stk_tickers, 'yahoo')
    ccy_data = web.DataReader(ccy_tickers, 'fred', start=START_DATE, end=END_DATE)
    idx_data = web.DataReader(idx_tickers, 'fred', start=START_DATE, end=END_DATE)

    Y = np.log(stk_data.loc[:, ('Adj Close', 'MSFT')]).diff(return_period).shift(-return_period)
    Y.name = Y.name[-1]+'_Future'
    
    X1 = np.log(stk_data.loc[:, ('Adj Close', ('GOOGL', 'IBM'))]).diff(return_period)
    X1.columns = X1.columns.droplevel()
    X2 = np.log(ccy_data).diff(return_period)
    X3 = np.log(idx_data).diff(return_period)

    X = pd.concat([X1, X2, X3], axis=1)
    
    dataset = pd.concat([Y, X], axis=1).dropna().iloc[::return_period, :]
    Y = dataset.loc[:, Y.name]
    X = dataset.loc[:, X.columns]
    dataset.index.name = 'Date'
    #dataset.to_csv(r"./test_data.csv")
    features = dataset.sort_index()
    features = features.reset_index(drop=True)
    features = features.iloc[:,1:]
    return features

def extract_features_pair():
    START_DATE = (datetime.date.today() - datetime.timedelta(days=365)).strftime("%Y-%m-%d")
    END_DATE = datetime.date.today().strftime("%Y-%m-%d")

    target_ticker = 'NVDA'
    partner_ticker = 'ANET'
    stk_tickers = [partner_ticker, target_ticker]

    try:
        stk_data = yf.download(
            stk_tickers,
            start=START_DATE,
            end=END_DATE,
            auto_adjust=False,
            progress=False,
            threads=False
        )

        if stk_data.empty:
            raise ValueError("yfinance returned empty data")

        # Pull adjusted close if available, otherwise close
        if isinstance(stk_data.columns, pd.MultiIndex):
            if ('Adj Close', target_ticker) in stk_data.columns and ('Adj Close', partner_ticker) in stk_data.columns:
                y = stk_data[('Adj Close', target_ticker)]
                x = stk_data[('Adj Close', partner_ticker)]
            elif ('Close', target_ticker) in stk_data.columns and ('Close', partner_ticker) in stk_data.columns:
                y = stk_data[('Close', target_ticker)]
                x = stk_data[('Close', partner_ticker)]
            else:
                raise ValueError(f"Unexpected columns: {stk_data.columns}")
        else:
            raise ValueError(f"Expected MultiIndex columns, got: {stk_data.columns}")

        y.name = target_ticker
        x.name = partner_ticker

        dataset = pd.concat([x, y], axis=1).dropna()
        if dataset.empty:
            raise ValueError("No overlapping price data after dropna")

        dataset.index.name = 'Date'
        features = dataset.sort_index().reset_index(drop=True)
        return features

    except Exception as e:
        print("extract_features_pair error:", e)

        # Fallback so Streamlit still runs
        idx = pd.RangeIndex(start=0, stop=252, step=1)
        fallback = pd.DataFrame({
            partner_ticker: np.linspace(200, 260, len(idx)),
            target_ticker: np.linspace(800, 1000, len(idx))
        }, index=idx)

        return fallback

def get_bitcoin_historical_prices(days=60):

    BASE_URL = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"

    params = {
        "vs_currency": "usd",
        "days": days,
        "interval": "daily"
    }

    try:
        response = requests.get(BASE_URL, params=params, timeout=15)
        data = response.json()

        prices = data.get("prices") if isinstance(data, dict) else None
        if not prices:
            raise ValueError("Missing 'prices' key in API response")

        df = pd.DataFrame(prices, columns=["Timestamp", "Close Price (USD)"])
        df["Date"] = pd.to_datetime(df["Timestamp"], unit="ms").dt.normalize()
        df = df[["Date", "Close Price (USD)"]].set_index("Date")

        return df

    except Exception:
        # Fallback if CoinGecko fails (prevents Streamlit crash)
        idx = pd.date_range(end=pd.Timestamp.today().normalize(), periods=days, freq="D")
        close = np.linspace(60000, 80000, len(idx))
        return pd.DataFrame({"Close Price (USD)": close}, index=idx)




