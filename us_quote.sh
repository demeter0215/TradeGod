#!/bin/bash
# TradeGod 美股实时查询快捷脚本
# 用法: ./us_quote.sh [股票代码，默认MAG7]

cd /home/node/clawd

if [ -z "$1" ]; then
    # 默认查询MAG7
    python3 -c "
import sys
sys.path.insert(0, '/home/node/clawd')
from us_market_reporter import USMarketReporter

reporter = USMarketReporter()
report = reporter.generate_market_report()
print(report)
"
else
    # 查询指定股票
    python3 -c "
import sys
sys.path.insert(0, '/home/node/clawd')
from us_stock_fetcher import USStockFetcher
from datetime import datetime

fetcher = USStockFetcher()
symbols = '$1'.split(',')
data = fetcher.get_stock_data(symbols)

print('=' * 60)
print(f'📊 美股实时行情 - {datetime.now().strftime(\"%H:%M:%S\")}')
print('=' * 60)

for symbol, info in data.items():
    if info:
        print(fetcher.format_stock_info(info))
"
fi
