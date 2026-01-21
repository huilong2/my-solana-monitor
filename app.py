import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Solana 监控面板", layout="wide")

# 自定义 CSS 让界面更专业
st.markdown("""
    <style>
    .stCode { background-color: #1e1e1e !important; color: #00ff00 !important; }
    .stButton>button { width: 100%; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚀 Solana 聪明钱监控看板")

# --- 配置中心 ---
# 为了方便你测试，我直接把你刚才给的 Key 填入作为默认值（建议以后存入 Streamlit Secrets）
HELIUS_API_KEY = "85a37a6b-9251-4d87-8f52-59de4b95e297"

with st.sidebar:
    st.header("⚙️ 配置中心")
    st.info(f"Helius 状态: {'✅ 已连接' if HELIUS_API_KEY else '❌ 未配置'}")
    
    st.divider()
    st.subheader("➕ 添加监控地址")
    if 'wallets' not in st.session_state:
        st.session_state.wallets = []
        
    new_addr = st.text_input("输入 Solana 钱包地址")
    if st.button("确认添加"):
        if new_addr and new_addr not in st.session_state.wallets:
            st.session_state.wallets.append(new_addr)
            st.success("添加成功！")

# --- 主界面 ---
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("📋 监控名单")
    if not st.session_state.wallets:
        st.write("暂无监控地址，请在左侧添加。")
    else:
        for addr in st.session_state.wallets:
            col_addr, col_del = st.columns([4, 1])
            with col_addr:
                if st.button(f"🔍 分析: {addr[:6]}...{addr[-4:]}", key=addr):
                    st.session_state.selected_wallet = addr
            with col_del:
                if st.button("🗑️", key=f"del_{addr}"):
                    st.session_state.wallets.remove(addr)
                    st.rerun()

with col2:
    st.subheader("📊 钱包详细分析")
    target_wallet = st.session_state.get('selected_wallet')
    
    if not target_wallet:
        st.info("请在左侧点击一个钱包地址开始分析。")
    else:
        st.write(f"正在查询地址: `{target_wallet}`")
        
        # 调用 Helius API 获取资产信息
        url = f"https://mainnet.helius-rpc.com/?api-key={HELIUS_API_KEY}"
        payload = {
            "jsonrpc": "2.0",
            "id": "my-id",
            "method": "getAssetsByOwner",
            "params": {
                "ownerAddress": target_wallet,
                "page": 1,
                "limit": 100,
                "displayOptions": { "showFungible": True }
            }
        }
        
        try:
            response = requests.post(url, json=payload)
            data = response.json()
            items = data.get('result', {}).get('items', [])
            
            if not items:
                st.warning("该钱包没有持仓或查询失败。")
            else:
                asset_list = []
                for item in items:
                    info = item.get('token_info', {})
                    metadata = item.get('content', {}).get('metadata', {})
                    name = metadata.get('name', 'Unknown')
                    symbol = info.get('symbol', 'N/A')
                    balance = info.get('balance', 0)
                    decimals = info.get('decimals', 0)
                    
                    if balance > 0:
                        real_balance = float(balance) / (10 ** decimals)
                        asset_list.append({
                            "名称": name,
                            "符号": symbol,
                            "余额": round(real_balance, 4),
                            "合约地址": item.get('id')
                        })
                
                df = pd.DataFrame(asset_list)
                st.dataframe(df, use_container_width=True)
                
        except Exception as e:
            st.error(f"查询出错: {e}")
