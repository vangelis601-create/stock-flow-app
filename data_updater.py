import pandas as pd
from FinMind.data import DataLoader
import os
from datetime import datetime, timedelta
from tqdm import tqdm

# 初始化 API
api = DataLoader()

# --- 設定 1: 股票清單 (台灣50成分股範例) ---
target_stocks = [
    '2330', '2317', '2454', '2308', '2303', '2881', '2882', '2886', '2891', '2884',
    '2603', '2609', '2615', '2002', '1301', '1303', '1326', '6505', '2912', '5871',
    '2382', '2357', '2412', '3008', '3045', '4904', '4938', '2885', '2892', '2880',
    '2883', '2887', '5876', '2890', '1101', '1216', '2207', '2327', '2379', '2395',
    '2408', '2610', '2618', '2801', '2915', '3034', '3037', '3711', '5880', '9910'
]

# --- 設定 2: 取得股票基本資料 ---
print("正在下載股票清單與產業分類...")
stock_info = api.taiwan_stock_info()
stock_info = stock_info[['stock_id', 'stock_name', 'industry_category']]
stock_info = stock_info[stock_info['stock_id'].isin(target_stocks)]

# --- 設定 3: 日期區間 (擴大到 150 天) ---
# 為了滿足 120 天的累計分析，我們至少要抓 150 天的資料
start_date = (datetime.now() - timedelta(days=150)).strftime('%Y-%m-%d')
end_date = datetime.now().strftime('%Y-%m-%d')

print(f"開始抓取資料 (擴大區間): {start_date} to {end_date}")

df_list = []

for stock_id in tqdm(target_stocks):
    try:
        df = api.taiwan_stock_institutional_investors(
            stock_id=stock_id,
            start_date=start_date,
            end_date=end_date
        )
        
        if df is not None and not df.empty:
            df['diff'] = df['buy'] - df['sell']
            
            # 轉置資料
            df_pivot = df.pivot_table(
                index=['date', 'stock_id'], 
                columns='name', 
                values='diff', 
                aggfunc='sum'
            ).reset_index()
            
            rename_map = {
                'Foreign_Investor': 'Foreign_Diff',
                'Investment_Trust': 'Trust_Diff',
                'Dealer_Self_Analysis': 'Dealer_Diff',
                'Dealer_Hedging': 'Dealer_Hedging_Diff'
            }
            df_pivot.rename(columns=rename_map, inplace=True)
            df_pivot = df_pivot.fillna(0)
            
            # 確保欄位存在
            for col in ['Foreign_Diff', 'Trust_Diff', 'Dealer_Diff']:
                if col not in df_pivot.columns:
                    df_pivot[col] = 0
            
            df_list.append(df_pivot)
            
    except Exception as e:
        print(f"Error scraping {stock_id}: {e}")

if df_list:
    combined_df = pd.concat(df_list)
    final_df = pd.merge(combined_df, stock_info, on='stock_id', how='left')
    
    os.makedirs('data', exist_ok=True)
    file_path = 'data/stock_data.csv'
    final_df.to_csv(file_path, index=False)
    print(f"資料更新成功！包含欄位: {final_df.columns.tolist()}")
else:
    print("本次沒有抓到資料。")
