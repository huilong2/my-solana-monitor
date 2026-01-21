import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Solana 监控面板", layout="wide")

st.title("🚀 Solana 聪明钱监控看板")

# 侧边栏：配置钥匙
with st.sidebar:
    st.header("配置中心")
    helius_key = st.text_input("Helius API Key", type="password")
    bird_key = st.text_input("Birdeye API Key", type="password")
    
    st.divider()
    st.subheader("添加监控地址")
    new_address = st.text_input("输入 Solana 钱包地址")
    if st.button("添加"):
        if 'wallets' not in st.session_state:
            st.session_state.wallets = []
        st.session_state.wallets.append(new_address)

# 主界面
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📋 正在监控的钱包")
    if 'wallets' in st.session_state:
        for addr in st.session_state.wallets:
            st.code(addr)
            if st.button(f"删除 {addr[:5]}"):
                st.session_state.wallets.remove(addr)

with col2:
    st.subheader("💰 实时盈利分析 (PnL)")
    if not bird_key:
        st.warning("请在左侧填入 Birdeye API Key 以查看分析")
    else:
        st.info("正在调取链上资产数据...")
        # 这里后续会接入 Birdeye 的盈利计算 API
        st.write("暂无持仓数据（正在对接 API...）")