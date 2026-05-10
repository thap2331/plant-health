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

df = None

# Fetch image list early — used in both chart and gallery
img_list = []
try:
    resp = requests.get(f"{API}/images/list", timeout=5)
    if resp.status_code == 200:
        img_list = resp.json()
except requests.exceptions.ConnectionError:
    pass

try:
    rows = requests.get(f"{API}/moisture/latest", timeout=5).json()
    if not rows:
        st.warning("No moisture data in the last 24 hours.")
    else:
        df = pd.DataFrame(rows)
        df['timestamp'] = pd.to_datetime(df['timestamp'])

        latest = df.iloc[-1]
        last_watered = df[df['watered']]['timestamp'].max()

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

        watered_df = df[df['watered']]
        if not watered_df.empty:
            fig.add_trace(
                go.Scatter(x=watered_df['timestamp'], y=watered_df['moisture_pct'],
                           mode='text', name='Watered',
                           text='💧', textfont=dict(size=20)),
                secondary_y=False,
            )

        if img_list:
            img_ts_df = pd.DataFrame(img_list)
            img_ts_df['timestamp'] = pd.to_datetime(img_ts_df['timestamp'])
            # Snap each 📷 to the y-value of the nearest moisture reading
            img_ts_df['y'] = img_ts_df['timestamp'].apply(
                lambda ts: df.loc[(df['timestamp'] - ts).abs().idxmin(), 'moisture_pct']
            )
            fig.add_trace(
                go.Scatter(x=img_ts_df['timestamp'], y=img_ts_df['y'],
                           mode='text', name='Photo taken',
                           text='📷', textfont=dict(size=16),
                           hovertext=img_ts_df['filename']),
                secondary_y=False,
            )

        fig.add_hline(y=40, line_dash="dash", line_color="red", annotation_text="Dry threshold")
        fig.update_yaxes(title_text="Moisture %", range=[0, 100], secondary_y=False)
        fig.update_yaxes(title_text="Raw ADC", secondary_y=True)
        fig.update_layout(xaxis_title="Time")
        st.plotly_chart(fig, use_container_width=True)

except requests.exceptions.ConnectionError:
    st.error("API unavailable — is the api container running?")

# Image gallery with moisture context
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
    img_ts = pd.Timestamp(img_info['timestamp'])
    label = f"Photo {st.session_state.img_idx + 1} of {n} — {img_ts.strftime('%b %d, %Y at %I:%M %p')}"
    with col_label:
        st.markdown(f"**{label}**")

    if df is not None:
        idx = (df['timestamp'] - img_ts).abs().idxmin()
        nearest = df.loc[idx]
        delta_min = abs((nearest['timestamp'] - img_ts).total_seconds()) / 60
        mc1, mc2, mc3 = st.columns(3)
        mc1.metric("Moisture at photo", f"{nearest['moisture_pct']}%")
        mc2.metric("Status", "Dry" if nearest['is_dry'] else "OK")
        mc3.metric("Reading offset", f"{delta_min:.0f} min")

    try:
        img_resp = requests.get(f"{API}/images/{img_info['filename']}", timeout=5)
        if img_resp.status_code == 200:
            st.image(img_resp.content, caption=label)
    except requests.exceptions.ConnectionError:
        pass

time.sleep(60)
st.rerun()
