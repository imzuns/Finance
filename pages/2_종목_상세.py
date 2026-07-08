from datetime import datetime, timedelta

import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from src import data
from src import relative_strength as rs
from src.disparity import classify, disparity, moving_average

st.set_page_config(page_title="종목 상세", layout="wide", page_icon="📈")

st.sidebar.title("추추 도우미")
st.sidebar.divider()
st.sidebar.header("분석 설정")
window = st.sidebar.selectbox("이동평균 기간", [50, 60, 120], index=0, key="ma_window")
low_th = st.sidebar.slider("과매도 임계값", 80, 100, 95, key="low_threshold")
high_th = st.sidebar.slider("과매수 임계값", 100, 130, 105, key="high_threshold")

st.title("종목 상세 — 이격도 & 상대강도")

try:
    tickers = data.get_kospi_constituents()
    names = data.get_ticker_names(tuple(tickers))
except Exception as e:
    st.error(f"구성종목 목록을 불러오지 못했습니다: {e}")
    st.info("`.env` 파일의 KRX_ID / KRX_PW가 올바르게 설정되어 있는지 확인해주세요.")
    st.stop()

options = sorted(tickers, key=lambda t: names.get(t, t))
label_map = {t: f"{names.get(t, t)} ({t})" for t in options}

ticker = st.selectbox(
    "종목 선택 (이름 또는 코드로 검색 가능)",
    options,
    format_func=lambda t: label_map.get(t, t),
    key="selected_ticker",
)

end = datetime.now()
price_start = end - timedelta(days=250)

try:
    price = data.get_stock_ohlcv(ticker, price_start.strftime("%Y%m%d"), end.strftime("%Y%m%d"))
    idx = data.get_kospi_index_history(price_start.strftime("%Y%m%d"), end.strftime("%Y%m%d"))
except Exception as e:
    st.error(f"'{label_map.get(ticker, ticker)}' 데이터를 불러오지 못했습니다: {e}")
    st.stop()

price["ma"] = moving_average(price["close"], window)
price["disparity"] = disparity(price["close"], window)

with st.spinner("전 종목 대비 상대강도 계산 중... (최초 로딩 시 1~2분 소요될 수 있습니다)"):
    trading_dates = tuple(d.strftime("%Y%m%d") for d in idx.tail(145).index)
    close_matrix = data.get_close_matrix(trading_dates)
    universe = [t for t in tickers if t in close_matrix.columns]
    rs_rating = rs.universe_rs_ratings(close_matrix[universe]).get(ticker)

latest = price.iloc[-1]
prev = price.iloc[-2]
chg_pct = (latest["close"] - prev["close"]) / prev["close"] * 100
status = classify(latest["disparity"], low_th, high_th)

st.subheader(label_map.get(ticker, ticker))
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("종가", f"{latest['close']:,.0f}", f"{chg_pct:+.2f}%")
c2.metric(f"{window}일 이동평균", f"{latest['ma']:,.0f}")
c3.metric(f"{window}일 이격도", f"{latest['disparity']:.2f}")
c4.metric("상태", status)
c5.metric("RS (6개월, 0~100)", rs_rating if rs_rating is not None else "N/A")

fig = make_subplots(
    rows=2, cols=1, shared_xaxes=True, row_heights=[0.65, 0.35],
    vertical_spacing=0.05,
    subplot_titles=("주가 & 이동평균", f"{window}일 이격도"),
)
fig.add_trace(go.Scatter(x=price.index, y=price["close"], name="종가", line=dict(color="#3B82F6")), row=1, col=1)
fig.add_trace(go.Scatter(x=price.index, y=price["ma"], name=f"{window}일 MA", line=dict(color="#F59E0B", dash="dot")), row=1, col=1)

fig.add_trace(go.Bar(x=price.index, y=price["disparity"], name="이격도", marker_color="#22C55E"), row=2, col=1)
fig.add_hline(y=high_th, line_dash="dash", line_color="#EF4444", row=2, col=1)
fig.add_hline(y=low_th, line_dash="dash", line_color="#EF4444", row=2, col=1)
fig.add_hline(y=100, line_color="rgba(255,255,255,0.3)", row=2, col=1)
fig.update_yaxes(range=[50, 150], row=2, col=1)

fig.update_layout(height=700, template="plotly_dark", hovermode="x unified", legend=dict(orientation="h", y=1.08))
st.plotly_chart(fig, use_container_width=True)
