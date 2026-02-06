#!/usr/bin/env python3
"""
TradeGod 早晚新闻报告生成器（优化版）
- 减少Tavily调用次数（每次报告最多2次）
- 只在工作日运行
"""

import sys
sys.path.insert(0, '/home/node/clawd')

from tradegod_news import TradeGodNews
from tavily_monitor import TavilyMonitor, check_before_report
from datetime import datetime
import json
import os

class NewsReporter:
    """新闻报告生成器"""
    
    def __init__(self):
        self.news = TradeGodNews()
        self.monitor = TavilyMonitor()
        self.api_calls = 0
    
    def log_api_call(self, purpose: str):
        """记录API调用"""
        self.api_calls += 1
        self.monitor.record_call(purpose)
        print(f"  [API {self.api_calls}] {purpose}")
    
    def generate_morning_report(self) -> str:
        """
        早7点报告: 美股复盘 + A股预判
        包含具体美股涨跌数据
        """
        now = datetime.now()
        report = []
        
        report.append("=" * 70)
        report.append(f"📈 TradeGod 早间报告 | {now.strftime('%Y-%m-%d %H:%M')}")
        report.append("=" * 70)
        
        # ===== 1. 美股收盘数据（关键！）=====
        report.append("\n🌍 【美股收盘】隔夜涨跌一览")
        report.append("-" * 70)
        
        # 获取美股实时数据
        try:
            from us_stock_fetcher import USStockFetcher
            fetcher = USStockFetcher()
            us_data = fetcher.get_mag7_data()
            
            if us_data:
                # 计算涨跌统计
                up_stocks = []
                down_stocks = []
                total_change = 0
                
                for symbol, data in us_data.items():
                    if data and data.get('price'):
                        change_pct = data.get('change_percent', 0)
                        total_change += change_pct
                        
                        if change_pct >= 0:
                            up_stocks.append((symbol, change_pct, data.get('price')))
                        else:
                            down_stocks.append((symbol, change_pct, data.get('price')))
                
                avg_change = total_change / len(us_data) if us_data else 0
                
                # 市场总体判断
                if avg_change > 1:
                    market_status = "🔥 美股大涨"
                elif avg_change > 0:
                    market_status = "🟢 美股小涨"
                elif avg_change > -1:
                    market_status = "🔴 美股小跌"
                else:
                    market_status = "❄️ 美股大跌"
                
                report.append(f"\n📊 市场总览: {market_status} (平均 {avg_change:+.2f}%)")
                report.append(f"📈 上涨: {len(up_stocks)} 只 | 📉 下跌: {len(down_stocks)} 只")
                
                # 详细涨跌
                if up_stocks:
                    report.append(f"\n🟢 领涨:")
                    for symbol, change, price in sorted(up_stocks, key=lambda x: x[1], reverse=True):
                        report.append(f"   {symbol}: ${price:.2f} (+{change:.2f}%)")
                
                if down_stocks:
                    report.append(f"\n🔴 领跌:")
                    for symbol, change, price in sorted(down_stocks, key=lambda x: x[1]):
                        report.append(f"   {symbol}: ${price:.2f} ({change:.2f}%)")
            else:
                report.append("⚠️ 美股数据获取失败")
        except Exception as e:
            report.append(f"⚠️ 美股数据获取异常: {e}")
        
        # ===== 2. 深度新闻分析 =====
        report.append("\n📰 【深度分析】重要新闻解读")
        report.append("-" * 70)
        
        self.log_api_call("美股深度搜索")
        us_market = self.news.search_tavily(
            "US stock market yesterday close China ADR Alibaba PDD Fed interest rate news",
            max_results=8,
            include_answer=True,
            search_depth="advanced"
        )
        
        if 'answer' in us_market and us_market['answer']:
            report.append(f"\n💡 市场解读:\n{us_market['answer'][:250]}")
        
        # 分类新闻
        china_news = [r for r in us_market.get('results', []) 
                     if any(k in r.get('title','').lower() for k in ['china', 'alibaba', 'pdd', 'jd', '中概'])]
        fed_news = [r for r in us_market.get('results', []) 
                   if any(k in r.get('title','').lower() for k in ['fed', 'powell', 'rate'])]
        
        if china_news:
            report.append(f"\n🏮 中概股相关:")
            for r in china_news[:2]:
                report.append(f"   • {r['title'][:55]}...")
        
        if fed_news:
            report.append(f"\n🏦 美联储/宏观:")
            for r in fed_news[:2]:
                report.append(f"   • {r['title'][:55]}...")
        
        # ===== 3. A股策略 =====
        report.append("\n🇨🇳 【A股策略】今日操作建议")
        report.append("-" * 70)
        
        # 获取A股早盘新闻
        a_news = self.news.fetch_a_stock(10)
        
        # 根据美股情况给出具体建议
        report.append(f"\n🎯 基于美股表现的应对策略:\n")
        
        try:
            if avg_change > 1 and len(up_stocks) > len(down_stocks):
                report.append("✅ 建议: 美股强势，A股可能高开")
                report.append("   • 关注科技/互联网板块（跟随美股）")
                report.append("   • 高开不追，等回踩5日线低吸")
                report.append("   • 仓位可增至40-50%")
            elif avg_change < -1 and len(down_stocks) > len(up_stocks):
                report.append("⚠️ 建议: 美股大跌，A股承压")
                report.append("   • 防御为主，关注高股息/银行")
                report.append("   • 等待大盘企稳信号")
                report.append("   • 仓位控制在20-30%")
            else:
                report.append("🟡 建议: 美股震荡，A股观望")
                report.append("   • 结构性行情，精选个股")
                report.append("   • 关注业绩确定性板块")
                report.append("   • 仓位30%左右")
        except:
            report.append("🟡 建议: 等待市场方向明确")
        
        # 重要新闻
        if a_news:
            policy_news = [n for n in a_news if any(k in n['title'] for k in ['央行', '政策', '证监会'])]
            if policy_news:
                report.append(f"\n📜 国内政策动向:")
                for n in policy_news[:2]:
                    report.append(f"   • [{n['source']}] {n['title'][:50]}...")
        
        report.append("\n" + "=" * 70)
        report.append(f"✅ 报告完成 | API调用: {self.api_calls}次")
        report.append("=" * 70)
        
        return "\n".join(report)
    
    def generate_evening_report(self) -> str:
        """
        晚7点报告: A股复盘 + 美股预判
        Tavily调用: 1次（美股盘前）
        """
        now = datetime.now()
        report = []
        
        report.append("=" * 60)
        report.append(f"📊 TradeGod 晚间新闻报告")
        report.append(f"时间: {now.strftime('%Y-%m-%d %H:%M')} | 策略: A股复盘 → 美股预判")
        report.append("=" * 60)
        
        # 1. A股收盘总结（RSS，免费）
        report.append("\n🇨🇳 【A股复盘】今日市场表现")
        report.append("-" * 50)
        
        a_news = self.news.fetch_a_stock(25)
        report.append(f"今日要闻共 {len(a_news)} 条\n")
        
        # 按板块分类
        sectors_map = {
            '新能源': [],
            '半导体': [],
            '银行': [],
            '房地产': [],
            '医药': [],
            'AI': [],
            '消费': []
        }
        
        for n in a_news:
            title_summary = n['title'] + n.get('summary', '')
            for sector in sectors_map.keys():
                if sector in title_summary:
                    sectors_map[sector].append(n)
        
        # 展示有新闻的板块
        has_news = False
        for sector, items in sectors_map.items():
            if items:
                if not has_news:
                    report.append("🔥 热点板块:")
                    has_news = True
                report.append(f"\n【{sector}】")
                for n in items[:2]:
                    report.append(f"  • {n['title'][:45]}...")
        
        # 2. 政策要闻（RSS，免费）
        report.append("\n📜 【政策动向】")
        report.append("-" * 50)
        
        policy_keywords = ['央行', '证监会', '政策', '降准', '降息']
        policy_news = [n for n in a_news if any(k in n['title'] for k in policy_keywords)]
        
        if policy_news:
            for n in policy_news[:4]:
                report.append(f"  • [{n['source']}] {n['title'][:50]}...")
        else:
            report.append("  今日无重大政策新闻")
        
        # 3. 美股前瞻（1次API调用）
        report.append("\n🌙 【美股前瞻】夜盘预判")
        report.append("-" * 50)
        
        self.log_api_call("美股盘前+中概股预期")
        us_premarket = self.news.search_tavily(
            "US stock futures premarket China ADR reaction A-shares impact",
            max_results=8,
            include_answer=True,
            search_depth="advanced"
        )
        
        if 'answer' in us_premarket and us_premarket['answer']:
            report.append(f"📊 盘前预期:\n{us_premarket['answer'][:250]}...")
        
        if us_premarket.get('results'):
            report.append("\n相关动态:")
            for r in us_premarket['results'][:4]:
                report.append(f"  • {r['title'][:50]}...")
        
        # 4. 影响路径分析（纯逻辑）
        report.append("\n📈 【A股→美股】影响路径")
        report.append("-" * 50)
        report.append("今日A股表现对美股的可能影响:")
        report.append("  • A股大涨 → 中概股/ADR可能高开")
        report.append("  • 新能源强势 → 关注美股光伏/电动车板块")
        report.append("  • 半导体异动 → 关注NVDA/AMD等芯片股")
        report.append("  • 人民币走势 → 影响外资流向中概股")
        
        # 5. 明日关注要点
        report.append("\n📅 【明日关注】")
        report.append("-" * 50)
        report.append("  • 美股开盘后中概股ADR表现")
        report.append("  • A50期货夜盘走势")
        report.append("  • 美联储官员讲话日程")
        report.append("  • 重要经济数据(非农/CPI/零售等)")
        
        report.append("\n" + "=" * 60)
        report.append(f"报告完成 | API调用: {self.api_calls}次 | 晚安！🌙")
        report.append("=" * 60)
        
        return "\n".join(report)
    
    def save_report(self, report: str, report_type: str):
        """保存报告到文件"""
        filename = f"/home/node/clawd/reports/{report_type}_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report)
        
        return filename


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='TradeGod 新闻报告生成（优化版）')
    parser.add_argument('type', choices=['morning', 'evening'], help='报告类型')
    parser.add_argument('--save', action='store_true', help='保存到文件')
    
    args = parser.parse_args()
    
    # 检查额度
    if not check_before_report():
        print("\n❌ 额度不足，跳过报告生成")
        print("💡 建议: 使用RSS源继续获取A股新闻（不消耗API额度）")
        sys.exit(1)
    
    reporter = NewsReporter()
    
    if args.type == 'morning':
        report = reporter.generate_morning_report()
    else:
        report = reporter.generate_evening_report()
    
    print(report)
    print(f"\n📊 本次报告共调用 Tavily API: {reporter.api_calls} 次")
    
    # 显示额度状态
    print("\n")
    reporter.monitor.print_report()
    
    if args.save:
        filename = reporter.save_report(report, args.type)
        print(f"\n📄 报告已保存: {filename}")
