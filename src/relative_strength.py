import pandas as pd


def six_month_return(close: pd.Series, periods: int = 126) -> float:
    n = len(close)
    if n <= periods:
        return float("nan")
    base = close.iloc[-periods - 1]
    if not base:
        return float("nan")
    return close.iloc[-1] / base - 1


def universe_rs_ratings(close_matrix: pd.DataFrame, periods: int = 126) -> pd.Series:
    raw = {t: six_month_return(close_matrix[t].dropna(), periods) for t in close_matrix.columns}
    pct = pd.Series(raw, dtype="float64").rank(pct=True)
    return (pct * 100).round().astype("Int64")
