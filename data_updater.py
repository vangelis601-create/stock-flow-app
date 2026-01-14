import pandas as pd
from FinMind.data import DataLoader
import os
from datetime import datetime, timedelta
from tqdm import tqdm

# 設定股票
stock_ids = ['2330', '2454', '2603', '2317', '2881'] 

api = DataLoader()

# --- 強制抓取過去 30 天 (確保一定有資料) ---
start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
end_date = datetime.now().strftime('%Y-%m-%d')

print(f"🔄 正在執行強制重置，抓取區間: {start_date} 到 {end_date}")

df_list = []

for stock_id in tqdm(stock_ids):
    try:
        # 抓取法人買賣超資料
        df = api.taiwan_stock_institutional_investors(
            stock_id=stock_id,
            start_date=start_date,
            end_date=end_date
        )
        
        if df is not None and not df.empty:
            # 篩選外資
            df_foreign = df[df['name'] == 'Foreign_Investor'].copy()
            
            # 建立關鍵欄位
            df_foreign['Foreign_Investor_Diff'] = df_foreign['buy'] - df_foreign['sell']
            
            # 整理欄位
            df_final = df_foreign[['date', 'stock_id', 'Foreign_Investor_Diff']]
            df_list.append(df_final)
            print(f"✅ {stock_id} 抓取成功，筆數: {len(df_final)}")
        else:
            print(f"⚠️ {stock_id} 無資料")
            
    except Exception as e:
        print(f"❌ {stock_id} 錯誤: {e}")

# --- 關鍵修正：不管舊檔案是否存在，直接覆蓋 (mode='w') ---
if df_list:
    combined_data = pd.concat(df_list)
    
    os.makedirs('data', exist_ok=True)
    file_path = 'data/stock_data.csv'
    
    # 直接存檔，不合併舊的 (因為舊的是錯的)
    combined_data.to_csv(file_path, index=False)
    print(f"🎉 資料庫重置成功！檔案已建立於: {file_path}")
    print("包含欄位:", combined_data.columns.tolist())
else:
    print("❌ 嚴重錯誤：抓不到任何資料，請檢查 FinMind API 狀態。")
    # 建立一個空的但格式正確的 DataFrame 防止網頁崩潰
    os.makedirs('data', exist_ok=True)
    pd.DataFrame(columns=['date', 'stock_id', 'Foreign_Investor_Diff']).to_csv('data/stock_data.csv', index=False)
