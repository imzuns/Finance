import pandas as pd


def moving_average(close: pd.Series, window: int) -> pd.Series:
    return close.rolling(window).mean()


def disparity(close: pd.Series, window: int) -> pd.Series:
    return close / moving_average(close, window) * 100


def classify(value: float, low: float, high: float) -> str:
    if pd.isna(value):
        return "데이터 없음"
    if value > high:
        return "과매수"
    if value < low:
        return "과매도"
    return "중립"
