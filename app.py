from datetime import datetime, timedelta

import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from src import data
from src.disparity import classify, disparity, moving_average

st.set_page_config(page_title="KOSPI 이격도 대시보드", layout="wide", page_icon="📊")

st.sidebar.header("분석 설정")
window = st.sidebar.selectbox("이동평균 기간", [20, 60, 120], index=0, key="ma_window")
low_th = st.sidebar.slider("과매도 임계값", 80, 100, 95, key="low_threshold")
high_th = st.sidebar.slider("과매수 임계값", 100, 130, 105, key="high_threshold")

st.title("KOSPI 지수 이격도")
st.caption("이격도 = 종가 / N일 이동평균 × 100")

end = datetime.now()
start = end - timedelta(days=400)

with st.spinner("KOSPI 지수 데이터를 불러오는 중..."):
    try:
        idx = data.get_kospi_index_history(start.strftime("%Y%m%d"), end.strftime("%Y%m%d"))
    except Exception as e:
        st.error(f"KOSPI 지수 데이터를 불러오지 못했습니다: {e}")
        st.info("`.env` 파일의 KRX_ID / KRX_PW가 올바르게 설정되어 있는지 확인해주세요.")
        st.stop()

idx["ma"] = moving_average(idx["close"], window)
idx["disparity"] = disparity(idx["close"], window)

latest = idx.iloc[-1]
prev = idx.iloc[-2]
chg_pct = (latest["close"] - prev["close"]) / prev["close"] * 100
status = classify(latest["disparity"], low_th, high_th)

c1, c2, c3, c4 = st.columns(4)
c1.metric("KOSPI 종가", f"{latest['close']:,.2f}", f"{chg_pct:+.2f}%")
c2.metric(f"{window}일 이동평균", f"{latest['ma']:,.2f}")
c3.metric(f"{window}일 이격도", f"{latest['disparity']:.2f}")
c4.metric("상태", status)

fig = make_subplots(
    rows=2, cols=1, shared_xaxes=True, row_heights=[0.65, 0.35],
    vertical_spacing=0.05,
    subplot_titles=("KOSPI 종가 & 이동평균", f"{window}일 이격도"),
)
fig.add_trace(go.Scatter(x=idx.index, y=idx["close"], name="종가", line=dict(color="#3B82F6")), row=1, col=1)
fig.add_trace(go.Scatter(x=idx.index, y=idx["ma"], name=f"{window}일 MA", line=dict(color="#F59E0B", dash="dot")), row=1, col=1)

fig.add_trace(go.Scatter(x=idx.index, y=idx["disparity"], name="이격도", line=dict(color="#22C55E")), row=2, col=1)
fig.add_hline(y=high_th, line_dash="dash", line_color="#EF4444", row=2, col=1)
fig.add_hline(y=low_th, line_dash="dash", line_color="#EF4444", row=2, col=1)
fig.add_hline(y=100, line_color="rgba(255,255,255,0.3)", row=2, col=1)

fig.update_layout(height=700, template="plotly_dark", hovermode="x unified", legend=dict(orientation="h", y=1.08))
st.plotly_chart(fig, use_container_width=True)

nav1, nav2 = st.columns(2)
nav1.page_link("pages/1_종목_스크리닝.py", label="→ 종목 스크리닝 페이지로 이동", icon="🔎")
nav2.page_link("pages/2_종목_상세.py", label="→ 종목 상세(수급 추이) 페이지로 이동", icon="📈")
