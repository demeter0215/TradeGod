#!/usr/bin/env python3
"""
TradeGod 财报监控模块
定时扫描业绩预告、关注财报发布
"""

import sys
sys.path.insert(0, '/home/node/clawd')

from earnings_fetcher import FinancialReportFetcher, EarningsMonitor
from datetime import datetime

class EarningsReporter:
    """财报报告生成器"""
    
    def __init__(self):
        self.fetcher = FinancialReportFetcher()
        self.monitor = EarningsMonitor()
    
    def generate_daily_scan(self) -> str:
        """
        每日财报扫描报告
        """
        report = []
        report.append("=" * 60)
        report.append(f"📊 TradeGod 财报日报 ({datetime.now().strftime('%Y-%m-%d')})")
        report.append("=" * 60)
        
        # 1. 高增长扫描
        report.append("\n🚀 【业绩预增】高增长股票")
        report.append("-" * 50)
        
        growth = self.fetcher.get_high_growth_stocks(min_growth=50)
        for i, stock in enumerate(growth[:10], 1):
            report.append(f"{i}. {stock['code']} {stock['name']} [{stock['type']}]")
            if stock['summary']:
                report.append(f"   {stock['summary'][:60]}...")
        
        # 2. 业绩预警
        report.append("\n⚠️ 【业绩预警】需关注股票")
        report.append("-" * 50)
        
        surprises = self.monitor.scan_surprises()
        warnings = [s for s in surprises if s['type'] == '预警']
        for i, stock in enumerate(warnings[:5], 1):
            report.append(f"{i}. {stock['code']} {stock['name']}")
        
        # 3. 即将披露
        report.append("\n📅 【即将披露】财报日历")
        report.append("-" * 50)
        
        upcoming = self.fetcher.get_upcoming_reports(days=7)
        for stock in upcoming[:10]:
            report.append(f"  • {stock['code']} {stock['name']} - {stock['scheduled_date']}")
        
        # 4. 关注列表检查
        watchlist = ['000001', '600519', '688256']  # 平安银行、茅台、寒武纪
        report.append("\n👀 【关注列表】财报追踪")
        report.append("-" * 50)
        
        watch_results = self.monitor.check_watchlist(watchlist)
        for r in watch_results.get('reports', []):
            report.append(f"  • {r['symbol']}: 营收 {r['data'].get('营业收入', 'N/A')}亿, ROE {r['data'].get('ROE', 'N/A')}%")
        
        report.append("\n" + "=" * 60)
        
        return "\n".join(report)


if __name__ == "__main__":
    reporter = EarningsReporter()
    print(reporter.generate_daily_scan())
