# .github/workflows/daily_update.yml
name: Daily Stock Data Update

on:
  schedule:
    # 設定每天 UTC 時間 08:00 (台灣時間 16:00 收盤後) 執行
    - cron: '0 8 * * *'
  workflow_dispatch: # 允許手動按按鈕執行

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'

      - name: Install dependencies
        run: |
          pip install pandas FinMind

      - name: Run updater script
        run: python data_updater.py

      - name: Commit and push changes
        run: |
          git config --global user.name 'GitHub Action'
          git config --global user.email 'action@github.com'
          git add data/stock_data.csv
          git commit -m "Auto-update stock data $(date +'%Y-%m-%d')" || exit 0
          git push
