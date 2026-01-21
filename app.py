import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Solana 监控面板-专业版", layout="wide")

# --- 1. 配置中心 ---
HELIUS_API_KEY = "85a37a6b-9251-4d87-8f52-59de4b95e297"
# 优先从 Secrets 读取，如果没有就用你刚才发的那个
BIRD_KEY = st.secrets.get("BIRD_KEY") or "d859424e5df840d4b495be40ae2ecaad"

st.title("🛡️ Solana 聪明钱深度监控")

with st.sidebar:
    st.header("⚙️ 系统设置")
    st.success(f"数据源: Birdeye 专业版")
    
    if 'wallets' not in st.session_state:
        st.session_state.wallets = []
    
    st.divider()
    new_addr = st.text_input("➕ 添加新监控地址")
    if st.button("确认添加"):
        if new_addr and new_addr not in st.session_state.wallets:
            st.session_state.wallets.append(new_addr)
            st.rerun()

# --- 2. 界面布局 ---
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("📋 监控名单")
    if not st.session_state.wallets:
        st.write("列表为空")
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
    target = st.session_state.get('selected_wallet')
    if not target:
        st.info("👈 请选择一个钱包查看详情")
    else:
        st.subheader(f"📊 资产实时分析")
        st.code(target)
        
        # 使用 Birdeye 接口获取钱包代币列表
        url = f"https://public-api.birdeye.so/v1/wallet/token_list?wallet={target}"
        headers = {"X-API-KEY": BIRD_KEY, "x-chain": "solana"}
        
        try:
            with st.spinner('正在调取 Birdeye 深度数据...'):
                res = requests.get(url, headers=headers).json()
                items = res.get('data', {}).get('items', [])
                
                if items:
                    data_list = []
                    total_value = 0
                    
                    for item in items:
                        usd_val = item.get('valueUsd', 0)
                        if usd_val > 1: # 过滤掉价值小于 1U 的垃圾币
                            total_value += usd_val
                            data_list.append({
                                "代币": item.get('symbol'),
                                "单价": f"${item.get('priceUsd', 0):.6f}",
                                "持仓数量": round(item.get('uiAmount', 0), 2),
                                "估值(USD)": round(usd_val, 2),
                                "合约": item.get('address')
                            })
                    
                    # 显示总价值
                    st.metric("钱包总估值 (USD)", f"${total_value:,.2f}")
                    
                    # 显示列表
                    df = pd.DataFrame(data_list)
                    st.dataframe(df, column_config={
                        "合约": st.column_config.LinkColumn("查看详情", help="跳转到 Birdeye 查看", validate="^https://.*", 
                                                         format="https://birdeye.so/token/%s?chain=solana")
                    }, use_container_width=True)
                else:
                    st.warning("该钱包暂时没有持仓数据或 API 额度受限。")
        except Exception as e:
            st.error(f"连接 Birdeye 出错: {e}")

# --- 3. 实时流水 (Helius) ---
if target:
    st.divider()
    st.subheader("🕒 最近交易流水 (Helius 驱动)")
    h_url = f"https://api.helius.xyz/v0/addresses/{target}/transactions?api-key={HELIUS_API_KEY}"
    try:
        txs = requests.get(h_url).json()
        for tx in txs[:5]: # 只看最近 5 笔
            with st.expander(f"交易类型: {tx.get('type')} | 时间: {tx.get('timestamp')}"):
                st.json(tx)
    except:
        st.write("无法加载流水")
