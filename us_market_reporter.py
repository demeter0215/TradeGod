#!/usr/bin/env python3
"""
TradeGod 美股市场报告（实时数据版）
使用腾讯财经API获取实时美股数据
"""

import sys
sys.path.insert(0, '/home/node/clawd')

from us_stock_fetcher import USStockFetcher
from dingtalk_notifier import send_market_summary
from datetime import datetime
import pytz

class USMarketReporter:
    """美股市场报告生成器"""
    
    def __init__(self):
        self.fetcher = USStockFetcher()
    
    def generate_market_report(self) -> str:
        """生成美股市场报告"""
        
        # 获取实时数据
        mag7 = self.fetcher.get_mag7_data()
        
        if not mag7:
            return "❌ 无法获取美股实时数据"
        
        # 获取当前时间
        ny_tz = pytz.timezone('America/New_York')
        ny_time = datetime.now(ny_tz)
        
        report = []
        report.append("=" * 60)
        report.append("📊 TradeGod 美股实时市场报告")
        report.append(f"美东时间: {ny_time.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("数据来源: 腾讯财经API | 时效性: ✅ 实时")
        report.append("=" * 60)
        
        # MAG7概览
        report.append("\n🚀 MAG7 (Magnificent Seven) 实时行情:")
        report.append("-" * 60)
        
        total_change = 0
        up_count = 0
        down_count = 0
        
        for symbol in ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA']:
            if symbol in mag7:
                data = mag7[symbol]
                price = data.get('price', 0)
                change = data.get('change', 0)
                change_pct = data.get('change_percent', 0)
                
                total_change += change_pct
                if change >= 0:
                    up_count += 1
                else:
                    down_count += 1
                
                emoji = "🟢" if change >= 0 else "🔴"
                report.append(f"{emoji} {symbol:6s}: ${price:7.2f} ({change:+.2f}, {change_pct:+.2f}%)")
        
        # 市场情绪
        avg_change = total_change / 7 if mag7 else 0
        report.append("\n📈 市场情绪:")
        report.append("-" * 60)
        report.append(f"  上涨: {up_count} 只 | 下跌: {down_count} 只")
        report.append(f"  平均涨跌幅: {avg_change:+.2f}%")
        
        if avg_change > 1:
            sentiment = "🔥 强势上涨"
        elif avg_change > 0:
            sentiment = "🟢 温和上涨"
        elif avg_change > -1:
            sentiment = "🔴 温和下跌"
        else:
            sentiment = "❄️ 显著下跌"
        
        report.append(f"  情绪判断: {sentiment}")
        
        # 个股点评
        report.append("\n💡 个股点评:")
        report.append("-" * 60)
        
        # 找出涨幅最大和跌幅最大的
        sorted_by_change = sorted(mag7.items(), key=lambda x: x[1].get('change_percent', 0), reverse=True)
        
        if sorted_by_change:
            best = sorted_by_change[0]
            worst = sorted_by_change[-1]
            
            report.append(f"  领涨: {best[0]} ({best[1].get('change_percent', 0):+.2f}%)")
            report.append(f"  领跌: {worst[0]} ({worst[1].get('change_percent', 0):+.2f}%)")
        
        # 交易建议
        report.append("\n🎯 短线交易建议:")
        report.append("-" * 60)
        
        if avg_change > 1:
            report.append("  • 市场情绪偏多，可逢低做多强势个股")
            report.append("  • 关注领涨股 momentum")
        elif avg_change < -1:
            report.append("  • 市场情绪偏空，谨慎做多")
            report.append("  • 关注超跌反弹机会或做空弱势股")
        else:
            report.append("  • 市场震荡，观望为主")
            report.append("  • 等待方向明确")
        
        report.append("\n" + "=" * 60)
        
        return "\n".join(report)
    
    def send_to_dingtalk(self):
        """发送报告到钉钉"""
        report = self.generate_market_report()
        
        # 转换为markdown格式
        markdown_content = report.replace("=" * 60, "---")
        
        send_market_summary(markdown_content)
        print("✅ 美股实时报告已推送到钉钉")


if __name__ == "__main__":
    reporter = USMarketReporter()
    
    # 生成并打印报告
    report = reporter.generate_market_report()
    print(report)
    
    # 推送到钉钉
    print("\n📱 正在推送到钉钉...")
    reporter.send_to_dingtalk()
