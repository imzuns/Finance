import os
import time

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

try:
    for key in ("KRX_ID", "KRX_PW"):
        if key in st.secrets:
            os.environ[key] = st.secrets[key]
except Exception:
    pass

from pykrx import stock

KOSPI_INDEX_TICKER = "1001"
MARKET = "KOSPI"


def _retry(fn, *args, attempts: int = 3, delay: float = 1.0, **kwargs):
    last_err = None
    for i in range(attempts):
        try:
            result = fn(*args, **kwargs)
            if result is None or (hasattr(result, "empty") and result.empty):
                raise ValueError("empty response")
            return result
        except Exception as e:
            last_err = e
            time.sleep(delay)
    raise last_err


@st.cache_data(ttl=60 * 60 * 6, show_spinner=False)
def get_kospi_index_history(start: str, end: str) -> pd.DataFrame:
    df = _retry(stock.get_index_ohlcv, start, end, KOSPI_INDEX_TICKER)
    df = df.rename(columns={
        "시가": "open", "고가": "high", "저가": "low",
        "종가": "close", "거래량": "volume",
    })
    return df


@st.cache_data(ttl=60 * 60 * 24, show_spinner=False)
def get_kospi_constituents() -> list[str]:
    tickers = _retry(stock.get_index_portfolio_deposit_file, KOSPI_INDEX_TICKER)
    return list(tickers)


@st.cache_data(ttl=60 * 60 * 24, show_spinner=False)
def get_ticker_names(tickers: tuple[str, ...]) -> dict[str, str]:
    names = {}
    for t in tickers:
        try:
            names[t] = _retry(stock.get_market_ticker_name, t, attempts=2, delay=0.5)
        except Exception:
            names[t] = t
    return names


@st.cache_data(ttl=60 * 60 * 6, show_spinner=False)
def get_close_matrix(trading_dates: tuple[str, ...]) -> pd.DataFrame:
    rows = {}
    for d in trading_dates:
        snap = _retry(stock.get_market_ohlcv, d, market=MARKET)
        rows[d] = snap["종가"]
    matrix = pd.DataFrame(rows).T
    matrix.index = pd.to_datetime(matrix.index)
    matrix = matrix.sort_index()
    return matrix


@st.cache_data(ttl=60 * 60 * 24, show_spinner=False)
def get_market_caps(date: str) -> pd.DataFrame:
    df = _retry(stock.get_market_cap, date)
    return df.rename(columns={"시가총액": "market_cap"})


@st.cache_data(ttl=60 * 60 * 6, show_spinner=False)
def get_stock_ohlcv(ticker: str, start: str, end: str) -> pd.DataFrame:
    df = _retry(stock.get_market_ohlcv, start, end, ticker)
    df = df.rename(columns={
        "시가": "open", "고가": "high", "저가": "low",
        "종가": "close", "거래량": "volume",
    })
    return df


@st.cache_data(ttl=60 * 60 * 6, show_spinner=False)
def get_investor_trading(ticker: str, start: str, end: str) -> pd.DataFrame:
    df = _retry(stock.get_market_trading_value_by_date, start, end, ticker)
    df = df.rename(columns={
        "개인": "individual", "외국인합계": "foreign", "기관합계": "institution",
    })
    return df[["individual", "foreign", "institution"]]
