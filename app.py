# app.py
import streamlit as st
import pandas as pd
import plotly.express as px

# 1. 讀取資料
@st.cache_data(ttl=3600) # 設定快取，避免頻繁讀取
def load_data():
    # 注意：這裡要讀取 GitHub 上的 Raw URL，或者如果是本地開發直接讀路徑
    # 部署時，Streamlit Cloud 會從 Repo 讀取
    try:
        df = pd.read_csv('data/stock_data.csv')
        df['date'] = pd.to_datetime(df['date'])
        return df
    except FileNotFoundError:
        return pd.DataFrame()

df = load_data()

st.title('📊 台股三大法人資金流向觀測站')

if df.empty:
    st.warning("目前沒有資料，請等待自動排程執行或檢查數據源。")
    st.stop()

# 2. 側邊欄：功能選擇
mode = st.sidebar.radio("選擇功能", ["產業資金流向 (Top 20)", "個股詳細分析"])
days_options = [5, 15, 30, 60, 90, 120]
selected_days = st.sidebar.selectbox("選擇觀察天數 (累計買賣超)", days_options)

# 資料預處理：計算每個股票最近 N 天的累積買賣超
# 這裡以「外資 (Foreign_Investor_Diff)」為例，你可以加總三大法人
def calculate_momentum(data, days):
    # 篩選最近 N 天
    cutoff_date = data['date'].max() - pd.Timedelta(days=days)
    recent_data = data[data['date'] > cutoff_date]
    # 加總
    momentum = recent_data.groupby('stock_id')['Foreign_Investor_Diff'].sum().reset_index()
    momentum.columns = ['stock_id', 'Net_Flow']
    return momentum

# 3. 功能實作
if mode == "產業資金流向 (Top 20)":
    st.header(f"近 {selected_days} 天 產業/個股 資金流向排行")
    
    # 模擬產業分類 (實際專案你需要一個 mapping 表格來 merge)
    # 這裡我們假設所有抓到的股票都在 '半導體/電子' 類 (範例)
    
    momentum_df = calculate_momentum(df, selected_days)
    momentum_df = momentum_df.sort_values('Net_Flow', ascending=False).head(20)
    
    # 繪圖
    fig = px.bar(momentum_df, x='stock_id', y='Net_Flow', 
                 title=f'資金淨流入前 20 名 (近{selected_days}日)',
                 color='Net_Flow',
                 color_continuous_scale=['green', 'red'])
    st.plotly_chart(fig)
    
    st.dataframe(momentum_df)

elif mode == "個股詳細分析":
    st.header("個股資金流向查詢")
    stock_input = st.text_input("輸入股票代碼", "2330")
    
    stock_df = df[df['stock_id'] == stock_input].sort_values('date')
    
    if not stock_df.empty:
        # 計算區間統計
        total_flow = stock_df.tail(selected_days)['Foreign_Investor_Diff'].sum()
        st.metric(label=f"近 {selected_days} 天外資累計買賣超", value=f"{total_flow:,.0f}")
        
        # 繪製趨勢圖
        fig = px.line(stock_df.tail(120), x='date', y='Foreign_Investor_Diff', 
                      title=f'{stock_input} 每日外資買賣超趨勢')
        st.plotly_chart(fig)
        
        st.subheader("詳細數據")
        st.dataframe(stock_df.sort_values('date', ascending=False))
    else:
        st.error("找不到該股票資料，請確認代碼是否正確。")
