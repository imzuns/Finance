from datetime import datetime, timedelta

import pandas as pd
import streamlit as st

from src import data
from src.disparity import classify, disparity

st.set_page_config(page_title="종목 스크리닝", layout="wide", page_icon="🔎")

st.sidebar.header("분석 설정")
window = st.sidebar.selectbox("이동평균 기간", [20, 60, 120], index=0, key="ma_window")
low_th = st.sidebar.slider("과매도 임계값", 80, 100, 95, key="low_threshold")
high_th = st.sidebar.slider("과매수 임계값", 100, 130, 105, key="high_threshold")

st.title("KOSPI 구성종목 이격도 스크리닝")

end = datetime.now()
start = end - timedelta(days=250)

try:
    idx = data.get_kospi_index_history(start.strftime("%Y%m%d"), end.strftime("%Y%m%d"))
    tickers = data.get_kospi_constituents()
except Exception as e:
    st.error(f"기초 데이터를 불러오지 못했습니다: {e}")
    st.info("`.env` 파일의 KRX_ID / KRX_PW가 올바르게 설정되어 있는지 확인해주세요.")
    st.stop()

trading_dates = tuple(d.strftime("%Y%m%d") for d in idx.tail(140).index)
latest_date = trading_dates[-1]

with st.spinner("전 종목 시세 수집 중... (최초 로딩 시 1~2분 소요될 수 있습니다)"):
    close_matrix = data.get_close_matrix(trading_dates)
    names = data.get_ticker_names(tuple(tickers))
    try:
        caps = data.get_market_caps(latest_date)
    except Exception:
        caps = None

available = [t for t in tickers if t in close_matrix.columns]
sub = close_matrix[available]

rows = []
for t in available:
    close = sub[t].dropna()
    if len(close) < window:
        continue
    disp = disparity(close, window)
    val = disp.iloc[-1]
    rows.append({
        "티커": t,
        "종목명": names.get(t, t),
        "종가": close.iloc[-1],
        f"{window}일 이격도": round(val, 2),
        "상태": classify(val, low_th, high_th),
        "시가총액": caps.loc[t, "market_cap"] if caps is not None and t in caps.index else None,
    })

result = pd.DataFrame(rows)

col1, col2 = st.columns([2, 1])
with col1:
    search = st.text_input("종목명 검색")
with col2:
    status_filter = st.selectbox("상태 필터", ["전체", "과매수", "과매도", "중립"])

view = result.copy()
if search:
    view = view[view["종목명"].str.contains(search, case=False, na=False)]
if status_filter != "전체":
    view = view[view["상태"] == status_filter]

view = view.sort_values(f"{window}일 이격도", ascending=False)

st.caption(f"총 {len(view)}개 종목 (기준일: {latest_date})")


def _highlight(row):
    color = ""
    if row["상태"] == "과매수":
        color = "background-color: rgba(239,68,68,0.25)"
    elif row["상태"] == "과매도":
        color = "background-color: rgba(59,130,246,0.25)"
    return [color] * len(row)


st.dataframe(
    view.style.apply(_highlight, axis=1).format({
        "종가": "{:,.0f}",
        f"{window}일 이격도": "{:.2f}",
        "시가총액": "{:,.0f}",
    }),
    use_container_width=True,
    height=600,
    hide_index=True,
)

st.download_button(
    "CSV 다운로드",
    view.to_csv(index=False).encode("utf-8-sig"),
    file_name=f"kospi_disparity_{window}d_{latest_date}.csv",
    mime="text/csv",
)
