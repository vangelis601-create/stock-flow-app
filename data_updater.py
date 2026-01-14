import pandas as pd
from FinMind.data import DataLoader
import os
from datetime import datetime, timedelta

# 設定要抓取的股票代碼 (範例：台積電、聯發科、長榮、鴻海、富邦金)
stock_ids = ['2330', '2454', '2603', '2317', '2881'] 

# 初始化 FinMind
api = DataLoader()

# 設定日期：抓取「過去 5 天」到「今天」的資料 (確保假日後也能補到數據)
start_date = (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d')
end_date = datetime.now().strftime('%Y-%m-%d')

print(f"開始抓取資料: {start_date} to {end_date}")

# 抓取三大法人買賣超
df_list = []
for stock_id in stock_ids:
    print(f"正在抓取 {stock_id}...")
    try:
        df = api.taiwan_stock_daily(
            stock_id=stock_id,
            start_date=start_date,
            end_date=end_date
        )
        # 簡單檢查是否有抓到資料
        if df is not None and not df.empty:
            df_list.append(df)
    except Exception as e:
        print(f"抓取 {stock_id} 時發生錯誤: {e}")

if df_list:
    new_data = pd.concat(df_list)
    
    # 確保資料夾存在
    os.makedirs('data', exist_ok=True)
    file_path = 'data/stock_data.csv'
    
    # 如果檔案存在，讀取舊資料並合併
    if os.path.exists(file_path):
        try:
            old_data = pd.read_csv(file_path)
            # 合併新舊資料
            combined_data = pd.concat([old_data, new_data])
            # 移除重複 (根據 股票代號 和 日期)，保留最新的
            combined_data = combined_data.drop_duplicates(subset=['date', 'stock_id'], keep='last')
        except pd.errors.EmptyDataError:
            # 如果舊檔案是空的
            combined_data = new_data
    else:
        combined_data = new_data
        
    # 儲存
    combined_data.to_csv(file_path, index=False)
    print(f"資料更新成功！目前共有 {len(combined_data)} 筆數據。")
else:
    print("本次執行沒有抓取到新資料 (可能是非交易日或 API 回傳空值)。")
