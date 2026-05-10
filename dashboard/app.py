import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import time

API = "http://api:8000"
st.set_page_config(page_title="Plant Health Dashboard", layout="wide")
st.title("Plant Health Dashboard")

try:
    rows = requests.get(f"{API}/moisture/latest", timeout=5).json()
    df = pd.DataFrame(rows)
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    latest = df.iloc[-1]
    last_watered = df[df['watered'] == True]['timestamp'].max()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Moisture", f"{latest['moisture_pct']}%")
    col2.metric("Status", "Dry" if latest['is_dry'] else "OK")
    col3.metric("Last Watered", last_watered.strftime("%b %d %H:%M") if pd.notna(last_watered) else "—")
    col4.metric("Readings Today", len(df))

    fig = go.Figure()
    fig.add_scatter(x=df['timestamp'], y=df['moisture_pct'], mode='lines', name='Moisture %')
    fig.add_hline(y=40, line_dash="dash", line_color="red", annotation_text="Dry threshold")
    fig.update_layout(yaxis_range=[0, 100], xaxis_title="Time", yaxis_title="Moisture %")
    st.plotly_chart(fig, use_container_width=True)

except requests.exceptions.ConnectionError:
    st.error("API unavailable — is the api container running?")

try:
    img_resp = requests.get(f"{API}/images/latest", timeout=5)
    if img_resp.status_code == 200:
        st.image(img_resp.content, caption="Latest plant image")
except requests.exceptions.ConnectionError:
    pass

time.sleep(60)
st.rerun()
