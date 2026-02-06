#!/usr/bin/env python3
"""
TradeGod 新闻抓取 - 快速使用示例
"""

from tradegod_news import TradeGodNews

# 初始化
news = TradeGodNews()

# ==================== 常用场景 ====================

# 1. 获取A股最新新闻（最快）
a_news = news.fetch_a_stock(limit=15)
print(f"A股新闻 {len(a_news)} 条:")
for n in a_news[:5]:
    print(f"  [{n['time']}] {n['title'][:40]}...")

# 2. 搜索特定关键词（A股+全球）
result = news.search('比亚迪', sources=['a_stock', 'global'])
print(f"\n'比亚迪' 搜索结果:")
print(f"  A股: {len(result['a_stock'])} 条")
print(f"  全球: {len(result['global'].get('results', []))} 条")

# 3. 美股深度分析（给小纳）
us_analysis = news.search_us_market("Tesla stock Q4 earnings")
print(f"\nTesla 深度分析:")
print(f"  AI总结: {us_analysis.get('answer', 'N/A')[:60]}...")

# 4. 加密货币（给小聪）
crypto = news.search_crypto("Bitcoin ETF approval impact")
print(f"\nBTC ETF 分析:")
print(f"  结果: {len(crypto.get('results', []))} 条")

# 5. 行业监控
sectors = news.monitor_sectors(['新能源', '半导体', '银行'])
print(f"\n行业监控:")
for s, items in sectors.items():
    print(f"  [{s}] {len(items)} 条")

# 6. 市场综合摘要
summary = news.get_market_summary()
print(f"\n市场摘要:")
print(f"  A股: {len(summary['a_stock_news'])} 条快讯")
if summary['global_summary']:
    print(f"  全球: {summary['global_summary'][:80]}...")
