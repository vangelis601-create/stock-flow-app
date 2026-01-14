import streamlit as st
import pandas as pd
import plotly.express as px

# --- 設定網頁寬度 ---
st.set_page_config(layout="wide", page_title="台股籌碼戰情室")

# --- 數值格式化函式 (變成 億/萬) ---
def format_currency(value):
    if abs(value) >= 100000000: # 億
        return f"{value/100000000:.2f} 億"
    elif abs(value) >= 10000: # 萬
        return f"{value/10000:.1f} 萬"
    else:
        return f"{value:.0f}"

# --- 讀取資料 ---
@st.cache_data
def load_data():
    try:
        df = pd.read_csv('data/stock_data.csv')
        df['date'] = pd.to_datetime(df['date'])
        # 建立一個顯示名稱: "2330 台積電"
        df['display_name'] = df['stock_id'].astype(str) + " " + df['stock_name']
        return df
    except FileNotFoundError:
        return None

df = load_data()

st.title("📊 台股資金流向儀表板 (Taiwan Stock Flow)")

if df is None:
    st.error("找不到資料檔 (data/stock_data.csv)，請確認 GitHub Actions 是否執行成功。")
else:
    # --- 側邊欄設定 ---
    st.sidebar.header("⚙️ 篩選設定")
    
    # 1. 選擇投資人類型
    investor_map = {
        '外資 (Foreign)': 'Foreign_Diff',
        '投信 (Trust)': 'Trust_Diff',
        '自營商 (Dealer)': 'Dealer_Diff'
    }
    selected_investor_label = st.sidebar.selectbox("選擇觀察法人", list(investor_map.keys()))
    selected_col = investor_map[selected_investor_label]
    
    # 2. 選擇天數
    days_options = [1, 3, 5, 10, 20]
    selected_days = st.sidebar.selectbox("累計天數 (N Days)", days_options, index=2)

    # --- 資料處理 ---
    # 篩選最近 N 天
    latest_date = df['date'].max()
    start_date = latest_date - pd.Timedelta(days=selected_days)
    recent_data = df[df['date'] > start_date]

    # 計算這段時間的總買賣超
    # 依照 'stock_id', 'display_name', 'industry_category' 分組加總
    momentum = recent_data.groupby(['stock_id', 'display_name', 'industry_category'])[selected_col].sum().reset_index()
    
    # 改名方便後續處理
    momentum.rename(columns={selected_col: 'Net_Flow'}, inplace=True)

    # --- 頁面佈局 ---
    
    # 分頁顯示
    tab1, tab2 = st.tabs(["🏭 產業資金流向", "📈 個股排名"])

    # === Tab 1: 產業分析 ===
    with tab1:
        st.subheader(f"近 {selected_days} 日 - {selected_investor_label} 產業佈局")
        
        # 依照產業加總
        industry_flow = momentum.groupby('industry_category')['Net_Flow'].sum().reset_index()
        industry_flow = industry_flow.sort_values('Net_Flow', ascending=False)
        
        # 畫圖 (Bar Chart)
        fig_ind = px.bar(
            industry_flow,
            x='industry_category',
            y='Net_Flow',
            color='Net_Flow',
            color_continuous_scale=['green', 'white', 'red'], # 綠色賣, 紅色買
            title=f"各產業資金淨流入/流出 ({selected_investor_label})",
            text_auto='.2s'
        )
        fig_ind.update_layout(xaxis_title="產業類別", yaxis_title="淨流量 (元)")
        st.plotly_chart(fig_ind, use_container_width=True)
        
        # 顯示詳細數據表格
        st.write("產業詳細數據：")
        industry_flow['格式化金額'] = industry_flow['Net_Flow'].apply(format_currency)
        st.dataframe(industry_flow[['industry_category', '格式化金額']].set_index('industry_category'))

    # === Tab 2: 個股排名 ===
    with tab2:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🔥 資金買超前 10 名")
            top_buy = momentum.sort_values('Net_Flow', ascending=False).head(10)
            
            # 畫圖
            fig_buy = px.bar(
                top_buy, 
                x='Net_Flow', 
                y='display_name', 
                orientation='h',
                color='Net_Flow',
                color_continuous_scale='Reds',
                text='Net_Flow' # 顯示數值
            )
            fig_buy.update_layout(yaxis={'categoryorder':'total ascending'}, xaxis_title="淨買超金額")
            fig_buy.update_traces(texttemplate='%{text:.2s}', textposition='outside')
            st.plotly_chart(fig_buy, use_container_width=True)

        with col2:
            st.subheader("❄️ 資金賣超前 10 名")
            top_sell = momentum.sort_values('Net_Flow', ascending=True).head(10)
            
            # 為了讓 bar 向左長，圖表不用特別改負號，Plotly 會自動處理
            fig_sell = px.bar(
                top_sell, 
                x='Net_Flow', 
                y='display_name', 
                orientation='h',
                color='Net_Flow',
                color_continuous_scale='Greens_r', # 綠色倒轉
                text='Net_Flow'
            )
            # 賣超由多到少排
            fig_sell.update_layout(yaxis={'categoryorder':'total descending'}, xaxis_title="淨賣超金額")
            fig_sell.update_traces(texttemplate='%{text:.2s}', textposition='outside')
            st.plotly_chart(fig_sell, use_container_width=True)

        # 詳細清單
        st.divider()
        st.subheader("詳細個股清單")
        # 格式化金額欄位
        momentum['金額'] = momentum['Net_Flow'].apply(format_currency)
        st.dataframe(
            momentum[['industry_category', 'stock_id', 'stock_name', '金額']]
            .sort_values('金額', ascending=False)
            .reset_index(drop=True)
        )
