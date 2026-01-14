import pandas as pd
from FinMind.data import DataLoader
import os
from datetime import datetime, timedelta
from tqdm import tqdm

# 設定要抓取的股票代碼
stock_ids = ['2330', '2454', '2603', '2317', '2881'] 

api = DataLoader()

# 設定日期：抓取過去 10 天 (確保有足夠數據畫圖)
start_date = (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d')
end_date = datetime.now().strftime('%Y-%m-%d')

print(f"開始抓取法人資料: {start_date} to {end_date}")

df_list = []

# 使用 tqdm 顯示進度條
for stock_id in tqdm(stock_ids):
    try:
        # --- 關鍵修正：改用 taiwan_stock_institutional_investors 抓法人資料 ---
        df = api.taiwan_stock_institutional_investors(
            stock_id=stock_id,
            start_date=start_date,
            end_date=end_date
        )
        
        if df is not None and not df.empty:
            # FinMind 的資料格式是 name='Foreign_Investor', buy=..., sell=...
            # 我們要篩選出「外資 (Foreign_Investor)」
            df_foreign = df[df['name'] == 'Foreign_Investor'].copy()
            
            # 計算買賣超 (Diff = Buy - Sell)
            df_foreign['Foreign_Investor_Diff'] = df_foreign['buy'] - df_foreign['sell']
            
            # 只保留需要的欄位
            df_final = df_foreign[['date', 'stock_id', 'Foreign_Investor_Diff']]
            
            df_list.append(df_final)
            
    except Exception as e:
        print(f"抓取 {stock_id} 時發生錯誤: {e}")

if df_list:
    new_data = pd.concat(df_list)
    
    # 處理檔案
    os.makedirs('data', exist_ok=True)
    file_path = 'data/stock_data.csv'
    
    # --- 自動修復機制 ---
    # 因為舊資料格式是錯的 (只有股價)，我們這次強制「覆蓋」舊檔，重新開始
    # 之後每天執行時，這行會改成 append 模式 (這裡為了修復錯誤，我們先直接存新的)
    if os.path.exists(file_path):
        try:
            old_data = pd.read_csv(file_path)
            # 檢查舊檔案有沒有我們需要的欄位，如果沒有，代表是舊的錯誤格式，直接覆蓋
            if 'Foreign_Investor_Diff' not in old_data.columns:
                print("偵測到舊資料格式不符，正在重建資料庫...")
                combined_data = new_data
            else:
                combined_data = pd.concat([old_data, new_data])
                combined_data = combined_data.drop_duplicates(subset=['date', 'stock_id'], keep='last')
        except:
            combined_data = new_data
    else:
        combined_data = new_data
        
    combined_data.to_csv(file_path, index=False)
    print(f"資料更新成功！包含欄位: {combined_data.columns.tolist()}")
else:
    print("本次沒有抓到資料。")
