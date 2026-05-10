import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import time

API = "http://api:8000"
st.set_page_config(page_title="Plant Health Dashboard", layout="wide")
st.title("Plant Health Dashboard")

try:
    rows = requests.get(f"{API}/moisture/latest", timeout=5).json()
    if not rows:
        st.warning("No moisture data in the last 24 hours.")
        st.stop()
    df = pd.DataFrame(rows)
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    latest = df.iloc[-1]
    last_watered = df[df['watered'] == True]['timestamp'].max()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Moisture", f"{latest['moisture_pct']}%")
    col2.metric("Status", "Dry" if latest['is_dry'] else "OK")
    col3.metric("Last Watered", last_watered.strftime("%b %d %H:%M") if pd.notna(last_watered) else "—")
    col4.metric("Readings Today", len(df))

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Scatter(x=df['timestamp'], y=df['moisture_pct'], mode='lines', name='Moisture %'),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(x=df['timestamp'], y=df['raw'], mode='lines', name='Raw ADC',
                   line=dict(dash='dot', color='orange'), visible='legendonly'),
        secondary_y=True,
    )
    fig.add_hline(y=40, line_dash="dash", line_color="red", annotation_text="Dry threshold")
    fig.update_yaxes(title_text="Moisture %", range=[0, 100], secondary_y=False)
    fig.update_yaxes(title_text="Raw ADC", secondary_y=True)
    fig.update_layout(xaxis_title="Time")
    st.plotly_chart(fig, use_container_width=True)

except requests.exceptions.ConnectionError:
    st.error("API unavailable — is the api container running?")

try:
    img_list = requests.get(f"{API}/images/list", timeout=5).json()
    if img_list:
        n = len(img_list)
        if 'img_idx' not in st.session_state:
            st.session_state.img_idx = n - 1
        st.session_state.img_idx = min(st.session_state.img_idx, n - 1)

        col_prev, col_label, col_next = st.columns([1, 8, 1])
        with col_prev:
            if st.button("◀", disabled=(st.session_state.img_idx == 0)):
                st.session_state.img_idx -= 1
                st.rerun()
        with col_next:
            if st.button("▶", disabled=(st.session_state.img_idx == n - 1)):
                st.session_state.img_idx += 1
                st.rerun()

        img_info = img_list[st.session_state.img_idx]
        ts = datetime.fromisoformat(img_info['timestamp'])
        label = f"Photo {st.session_state.img_idx + 1} of {n} — {ts.strftime('%b %d, %Y at %I:%M %p')}"
        with col_label:
            st.markdown(f"**{label}**")

        img_resp = requests.get(f"{API}/images/{img_info['filename']}", timeout=5)
        if img_resp.status_code == 200:
            st.image(img_resp.content, caption=label)
except requests.exceptions.ConnectionError:
    pass

time.sleep(60)
st.rerun()
