import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Solana 免费监控版", layout="wide")

# 配置中心 (只用免费的 Helius)
HELIUS_API_KEY = "85a37a6b-9251-4d87-8f52-59de4b95e297"

def get_jup_price(mint_addresses):
    """从 Jupiter 批量获取代币价格 (免费且无需 Key)"""
    if not mint_addresses: return {}
    mints = ",".join(mint_addresses)
    url = f"https://api.jup.ag/price/v2?ids={mints}"
    try:
        res = requests.get(url).json()
        return res.get('data', {})
    except:
        return {}

st.title("🚀 Solana 零成本监控看板")

with st.sidebar:
    st.header("⚙️ 配置中心")
    st.success("Helius API: 已连接")
    st.info("价格数据源: Jupiter (免费)")
    
    st.divider()
    if 'wallets' not in st.session_state:
        st.session_state.wallets = []
    
    new_addr = st.text_input("输入监控地址")
    if st.button("确认添加"):
        if new_addr and new_addr not in st.session_state.wallets:
            st.session_state.wallets.append(new_addr)
            st.rerun()

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("📋 监控名单")
    for addr in st.session_state.wallets:
        c1, c2 = st.columns([4, 1])
        with c1:
            if st.button(f"🔍 {addr[:6]}...{addr[-4:]}", key=addr):
                st.session_state.selected_wallet = addr
        with c2:
            if st.button("🗑️", key=f"del_{addr}"):
                st.session_state.wallets.remove(addr)
                st.rerun()

with col2:
    target_wallet = st.session_state.get('selected_wallet')
    if not target_wallet:
        st.info("👈 请选择一个钱包地址")
    else:
        st.subheader(f"📊 资产分析: `{target_wallet[:10]}...`")
        
        # 1. 获取 Helius 资产
        h_url = f"https://mainnet.helius-rpc.com/?api-key={HELIUS_API_KEY}"
        payload = {
            "jsonrpc": "2.0", "id": "1", "method": "getAssetsByOwner",
            "params": {"ownerAddress": target_wallet, "displayOptions": {"showFungible": True}}
        }
        
        with st.spinner('正在同步链上数据...'):
            try:
                items = requests.post(h_url, json=payload).json().get('result', {}).get('items', [])
                
                asset_data = []
                mint_list = []
                
                for item in items:
                    info = item.get('token_info', {})
                    mint = item.get('id')
                    balance = float(info.get('balance', 0)) / (10**info.get('decimals', 0))
                    
                    if balance > 0.01: # 过滤掉极小余额
                        asset_data.append({"mint": mint, "symbol": info.get('symbol'), "balance": balance})
                        mint_list.append(mint)
                
                # 2. 从 Jupiter 获取价格
                prices = get_jup_price(mint_list)
                
                final_assets = []
                total_usd = 0
                for a in asset_data:
                    price_info = prices.get(a['mint'], {})
                    price = float(price_info.get('price', 0)) if price_info else 0
                    value = a['balance'] * price
                    total_usd += value
                    
                    final_assets.append({
                        "代币": a['symbol'],
                        "余额": f"{a['balance']:.2f}",
                        "价格": f"${price:.4f}" if price > 0 else "未知",
                        "价值(USD)": round(value, 2),
                        "操作": f"https://dexscreener.com/solana/{a['mint']}"
                    })

                st.metric("估算总价值", f"${total_usd:.2f}")
                df = pd.DataFrame(final_assets)
                if not df.empty:
                    # 使用 streamlit 的链接渲染功能
                    st.dataframe(df, column_config={
                        "操作": st.column_config.LinkColumn("查看 K 线")
                    }, use_container_width=True)
                else:
                    st.write("该钱包目前没有显著持仓。")
                    
            except Exception as e:
                st.error(f"数据加载失败: {e}")
