import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide", page_title="台股籌碼戰情室 Pro")

# --- 輔助函式 ---
def format_currency(value):
    if abs(value) >= 100000000:
        return f"{value/100000000:.2f} 億"
    elif abs(value) >= 10000:
        return f"{value/10000:.1f} 萬"
    else:
        return f"{value:.0f}"

@st.cache_data
def load_data():
    try:
        df = pd.read_csv('data/stock_data.csv')
        df['date'] = pd.to_datetime(df['date'])
        df['stock_name'] = df['stock_name'].astype(str)
        df['display_name'] = df['stock_id'].astype(str) + " " + df['stock_name']
        return df
    except FileNotFoundError:
        return None

df = load_data()

st.title("📊 台股資金流向儀表板 Pro")

if df is None:
    st.error("找不到資料檔，請檢查 GitHub Actions。")
else:
    # --- 全域側邊欄 ---
    st.sidebar.header("⚙️ 全域設定")
    
    # 選擇法人
    investor_map = {
        '外資 (Foreign)': 'Foreign_Diff',
        '投信 (Trust)': 'Trust_Diff',
        '自營商 (Dealer)': 'Dealer_Diff'
    }
    selected_investor_label = st.sidebar.selectbox("觀察法人", list(investor_map.keys()))
    selected_col = investor_map[selected_investor_label]
    
    # 選擇天數 (新增 60, 90, 120 天)
    days_options = [1, 3, 5, 10, 20, 60, 90, 120]
    selected_days = st.sidebar.selectbox("累計天數 (N Days)", days_options, index=2)

    # 計算區間資料
    latest_date = df['date'].max()
    start_date = latest_date - pd.Timedelta(days=selected_days)
    recent_data = df[df['date'] > start_date]

    # --- 三大功能分頁 ---
    tab1, tab2, tab3 = st.tabs(["🌍 全市場概覽", "🏭 產業資金細項", "📈 個股趨勢分析"])

    # === Tab 1: 全市場概覽 ===
    with tab1:
        # 計算累計
        momentum = recent_data.groupby(['stock_id', 'stock_name', 'display_name', 'industry_category'])[selected_col].sum().reset_index()
        momentum.rename(columns={selected_col: 'Net_Flow'}, inplace=True)
        
        col_main_1, col_main_2 = st.columns([2, 1])
        
        with col_main_1:
            st.subheader(f"各產業 {selected_investor_label} 資金流向 ({selected_days}日)")
            industry_flow = momentum.groupby('industry_category')['Net_Flow'].sum().reset_index()
            industry_flow = industry_flow.sort_values('Net_Flow', ascending=False)
            
            fig_ind = px.bar(
                industry_flow, x='industry_category', y='Net_Flow',
                color='Net_Flow', color_continuous_scale=['green', 'white', 'red'],
                text_auto='.2s'
            )
            st.plotly_chart(fig_ind, use_container_width=True)
            
        with col_main_2:
            st.subheader("全市場買超 Top 10")
            top_stocks = momentum.sort_values('Net_Flow', ascending=False).head(10)
            st.dataframe(
                top_stocks[['display_name', 'Net_Flow']].style.format({'Net_Flow': format_currency})
            )

    # === Tab 2: 產業資金細項 (您的新需求) ===
    with tab2:
        st.subheader("🔍 產業資金深度分析")
        
        # 取得所有產業列表
        all_industries = sorted(df['industry_category'].unique().tolist())
        selected_industry = st.selectbox("請選擇要查看的產業:", all_industries)
        
        # 篩選該產業的股票
        industry_data = momentum[momentum['industry_category'] == selected_industry].sort_values('Net_Flow', ascending=False)
        
        if not industry_data.empty:
            # 畫圖
            fig_ind_detail = px.bar(
                industry_data,
                x='Net_Flow', y='display_name', orientation='h',
                title=f"{selected_industry} - {selected_investor_label} 資金分布 ({selected_days}日)",
                color='Net_Flow', color_continuous_scale=['green', 'white', 'red'],
                text='Net_Flow'
            )
            fig_ind_detail.update_traces(texttemplate='%{text:.2s}', textposition='outside')
            fig_ind_detail.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_ind_detail, use_container_width=True)
            
            # 表格
            st.write(f"{selected_industry} 詳細數據")
            industry_data['金額'] = industry_data['Net_Flow'].apply(format_currency)
            st.dataframe(industry_data[['stock_id', 'stock_name', '金額']])
        else:
            st.info("此產業在選定區間內無交易資料。")

    # === Tab 3: 個股趨勢分析 (您的新需求) ===
    with tab3:
        st.subheader("📈 個股每日買賣超趨勢")
        
        # 選擇股票
        all_stocks = sorted(df['display_name'].unique().tolist())
        target_stock = st.selectbox("輸入代號或名稱搜尋股票:", all_stocks)
        
        # 抓取該股的所有歷史資料 (不受側邊欄天數限制，預設看 120 天趨勢)
        stock_trend = df[df['display_name'] == target_stock].sort_values('date')
        
        # 畫每日買賣超 Bar Chart
        fig_trend = px.bar(
            stock_trend,
            x='date',
            y=selected_col,
            title=f"{target_stock} - {selected_investor_label} 每日買賣超金額",
            color=selected_col,
            color_continuous_scale=['green', 'white', 'red'] # 綠賣紅買
        )
        # 加入一條累計買賣超的線 (可以看出波段趨勢)
        stock_trend['Cumulative'] = stock_trend[selected_col].cumsum()
        
        st.plotly_chart(fig_trend, use_container_width=True)
        
        # 顯示統計
        total_buy = stock_trend[selected_col].sum()
        st.metric(label=f"近 {len(stock_trend)} 交易日總買賣超", value=format_currency(total_buy))
