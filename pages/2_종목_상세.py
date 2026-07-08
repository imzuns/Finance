from datetime import datetime, timedelta

import plotly.graph_objects as go
import streamlit as st

from src import data
from src.disparity import classify, disparity, moving_average

st.set_page_config(page_title="종목 상세", layout="wide", page_icon="📈")

st.sidebar.header("분석 설정")
window = st.sidebar.selectbox("이동평균 기간", [20, 60, 120], index=0, key="ma_window")
low_th = st.sidebar.slider("과매도 임계값", 80, 100, 95, key="low_threshold")
high_th = st.sidebar.slider("과매수 임계값", 100, 130, 105, key="high_threshold")

st.title("종목 상세 — 이격도 & 수급 추이")

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
flow_start = end - timedelta(days=45)

try:
    price = data.get_stock_ohlcv(ticker, price_start.strftime("%Y%m%d"), end.strftime("%Y%m%d"))
    flow = data.get_investor_trading(ticker, flow_start.strftime("%Y%m%d"), end.strftime("%Y%m%d"))
except Exception as e:
    st.error(f"'{label_map.get(ticker, ticker)}' 데이터를 불러오지 못했습니다: {e}")
    st.stop()

price["ma"] = moving_average(price["close"], window)
price["disparity"] = disparity(price["close"], window)
latest = price.iloc[-1]
prev = price.iloc[-2]
chg_pct = (latest["close"] - prev["close"]) / prev["close"] * 100
status = classify(latest["disparity"], low_th, high_th)

st.subheader(label_map.get(ticker, ticker))
c1, c2, c3, c4 = st.columns(4)
c1.metric("종가", f"{latest['close']:,.0f}", f"{chg_pct:+.2f}%")
c2.metric(f"{window}일 이동평균", f"{latest['ma']:,.0f}")
c3.metric(f"{window}일 이격도", f"{latest['disparity']:.2f}")
c4.metric("상태", status)

fig1 = go.Figure()
fig1.add_trace(go.Scatter(x=price.index, y=price["close"], name="종가", line=dict(color="#3B82F6")))
fig1.add_trace(go.Scatter(x=price.index, y=price["ma"], name=f"{window}일 MA", line=dict(color="#F59E0B", dash="dot")))
fig1.update_layout(
    height=350, template="plotly_dark", hovermode="x unified",
    title="주가 & 이동평균", legend=dict(orientation="h", y=1.1),
)
st.plotly_chart(fig1, use_container_width=True)

st.subheader("투자자별 누적 수급 추이 (최근 1개월, 순매수대금 억원)")

flow_month = (flow.tail(20) / 1e8).round(1)
flow_cum = flow_month.cumsum()

fig2 = go.Figure()
fig2.add_trace(go.Scatter(x=flow_cum.index, y=flow_cum["individual"], name="개인", line=dict(color="#94A3B8")))
fig2.add_trace(go.Scatter(x=flow_cum.index, y=flow_cum["foreign"], name="외국인", line=dict(color="#3B82F6")))
fig2.add_trace(go.Scatter(x=flow_cum.index, y=flow_cum["institution"], name="기관", line=dict(color="#F59E0B")))
fig2.add_hline(y=0, line_color="rgba(255,255,255,0.3)")
fig2.update_layout(
    height=400, template="plotly_dark", hovermode="x unified",
    legend=dict(orientation="h", y=1.1), yaxis_title="누적 순매수대금 (억원)",
)
st.plotly_chart(fig2, use_container_width=True)

table = flow_cum.rename(columns={"individual": "개인", "foreign": "외국인", "institution": "기관"})
st.dataframe(table.sort_index(ascending=False), use_container_width=True)
