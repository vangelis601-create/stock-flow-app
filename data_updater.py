import pandas as pd
from FinMind.data import DataLoader
import os
from datetime import datetime, timedelta
from tqdm import tqdm

# 初始化 API
api = DataLoader()

# --- 設定 1: 抓取台灣50成分股 (範例) ---
# 為了讓您看到產業分佈，我們抓取 0050 成分股，這樣資料量剛好且具代表性
# 如果想抓全市場，可以改用 api.taiwan_stock_info() 取得所有代碼，但執行時間會很久
target_stocks = [
    '2330', '2317', '2454', '2308', '2303', '2881', '2882', '2886', '2891', '2884',
    '2603', '2609', '2615', '2002', '1301', '1303', '1326', '6505', '2912', '5871',
    '2382', '2357', '2412', '3008', '3045', '4904', '4938', '2885', '2892', '2880',
    '2883', '2887', '5876', '2890', '1101', '1216', '2207', '2327', '2379', '2395',
    '2408', '2610', '2618', '2801', '2915', '3034', '3037', '3711', '5880', '9910'
]

# --- 設定 2: 取得股票基本資料 (名稱、產業) ---
print("正在下載股票清單與產業分類...")
stock_info = api.taiwan_stock_info()
# 只保留需要的欄位
stock_info = stock_info[['stock_id', 'stock_name', 'industry_category']]
# 篩選出我們關注的股票
stock_info = stock_info[stock_info['stock_id'].isin(target_stocks)]

# --- 設定 3: 設定日期區間 (過去 30 天) ---
start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
end_date = datetime.now().strftime('%Y-%m-%d')

print(f"開始抓取資料: {start_date} to {end_date}")

df_list = []

for stock_id in tqdm(target_stocks):
    try:
        # 抓取三大法人資料
        df = api.taiwan_stock_institutional_investors(
            stock_id=stock_id,
            start_date=start_date,
            end_date=end_date
        )
        
        if df is not None and not df.empty:
            # 計算買賣超 (Diff)
            df['diff'] = df['buy'] - df['sell']
            
            # 使用 Pivot Table 轉置資料
            # 原始格式: date, stock_id, name(外資), diff
            # 目標格式: date, stock_id, Foreign_Diff, Investment_Trust_Diff, Dealer_Diff
            df_pivot = df.pivot_table(
                index=['date', 'stock_id'], 
                columns='name', 
                values='diff', 
                aggfunc='sum'
            ).reset_index()
            
            # 重新命名欄位，處理可能缺失的法人 (有些股票某天投信沒動作)
            rename_map = {
                'Foreign_Investor': 'Foreign_Diff',
                'Investment_Trust': 'Trust_Diff',
                'Dealer_Self_Analysis': 'Dealer_Diff', # 自營商(自行買賣)
                'Dealer_Hedging': 'Dealer_Hedging_Diff' # 自營商(避險) - 這裡我們簡化，只取前三個或合併
            }
            # 為了簡化，我們把所有自營商加總，或者只看自行買賣
            # 這裡簡單處理：如果有欄位就改名，沒有就算了
            df_pivot.rename(columns=rename_map, inplace=True)
            
            # 補 0 (防止某些天沒有數據變成 NaN)
            df_pivot = df_pivot.fillna(0)
            
            # 確保欄位存在 (如果完全沒人買，要補上欄位)
            for col in ['Foreign_Diff', 'Trust_Diff', 'Dealer_Diff']:
                if col not in df_pivot.columns:
                    df_pivot[col] = 0
            
            df_list.append(df_pivot)
            
    except Exception as e:
        print(f"Error scraping {stock_id}: {e}")

if df_list:
    # 1. 合併所有股價資料
    combined_df = pd.concat(df_list)
    
    # 2. 合併股票基本資料 (加上中文名稱與產業)
    final_df = pd.merge(combined_df, stock_info, on='stock_id', how='left')
    
    # 3. 儲存
    os.makedirs('data', exist_ok=True)
    file_path = 'data/stock_data.csv'
    final_df.to_csv(file_path, index=False)
    print(f"資料更新成功！包含欄位: {final_df.columns.tolist()}")
else:
    print("本次沒有抓到資料。")
