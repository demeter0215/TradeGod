#!/usr/bin/env python3
"""
A股财报数据抓取器 - 修复版
自动获取最新报告期数据
"""

import akshare as ak
import pandas as pd
from datetime import datetime
from typing import List, Dict, Optional
import requests
import json

class FinancialReportFetcher:
    """财报数据抓取器 - 自动获取最新数据"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def get_high_growth_stocks(self, min_growth: int = 50) -> List[Dict]:
        """
        获取高增长股票（业绩预告中净利润增长较高的）
        """
        results = []
        
        try:
            df = self.get_performance_forecast()
            if df.empty:
                return results
            
            # 解析增长数据
            for _, row in df.iterrows():
                stock_type = row.get('预告类型', '')
                summary = row.get('业绩预告摘要', '')
                
                # 只关注预增类型
                if '增' not in stock_type and '盈' not in stock_type:
                    continue
                
                code = row.get('股票代码', '')
                name = row.get('股票简称', '')
                
                results.append({
                    'code': code,
                    'name': name,
                    'type': stock_type,
                    'summary': summary
                })
            
            # 限制返回数量
            return results[:20]
            
        except Exception as e:
            print(f"获取高增长股票失败: {e}")
            return results
    
    def get_upcoming_reports(self, days: int = 7) -> List[Dict]:
        """
        获取即将披露的财报日程
        """
        results = []
        
        try:
            import akshare as ak
            # 获取财报披露日程
            df = ak.stock_yjyg_em(date=self.get_latest_report_period())
            if not df.empty:
                # 获取公告日期最近的
                df_sorted = df.sort_values('公告日期', ascending=False)
                for _, row in df_sorted.head(10).iterrows():
                    results.append({
                        'code': row.get('股票代码', ''),
                        'name': row.get('股票简称', ''),
                        'scheduled_date': row.get('公告日期', ''),
                        'type': row.get('预告类型', '')
                    })
        except Exception as e:
            print(f"获取财报日程失败: {e}")
        
        return results
    
    def get_latest_report_period(self) -> str:
        """
        获取当前最新的财报期
        根据当前日期自动判断
        """
        now = datetime.now()
        year = now.year
        month = now.month
        
        # A股财报披露时间线：
        # 年报：1月-4月（披露上年）
        # 一季报：4月
        # 半年报：7-8月
        # 三季报：10月
        
        if month >= 10:  # 10-12月：三季报已出
            return f"{year}0930"
        elif month >= 7:   # 7-9月：半年报
            return f"{year}0630"
        elif month >= 4:   # 4-6月：一季报
            return f"{year}0331"
        else:               # 1-3月：上年年报
            return f"{year-1}1231"
    
    def get_performance_forecast(self, date: str = None) -> pd.DataFrame:
        """
        获取业绩预告 - 自动获取最新
        """
        if date is None:
            date = self.get_latest_report_period()
        
        print(f"正在获取 {date} 期业绩预告...")
        
        try:
            df = ak.stock_yjyg_em(date=date)
            print(f"✅ 获取成功，共 {len(df)} 条")
            return df
        except Exception as e:
            print(f"❌ 获取失败: {e}")
            # 尝试上一个季度
            if '1231' in date:
                fallback = date.replace('1231', '0930')
            elif '0930' in date:
                fallback = date.replace('0930', '0630')
            elif '0630' in date:
                fallback = date.replace('0630', '0331')
            else:
                fallback = str(int(date[:4])-1) + '1231'
            
            print(f"尝试获取上一期 {fallback}...")
            try:
                df = ak.stock_yjyg_em(date=fallback)
                print(f"✅ 获取成功，共 {len(df)} 条")
                return df
            except Exception as e2:
                print(f"❌ 也失败: {e2}")
                return pd.DataFrame()
    
    def get_stock_financial(self, symbol: str) -> Dict:
        """
        获取个股最新财务指标
        """
        result = {'symbol': symbol, 'timestamp': datetime.now().isoformat()}
        
        # 方法1: 主要财务指标
        try:
            df = ak.stock_financial_analysis_indicator(symbol=symbol)
            if not df.empty:
                latest = df.iloc[0]
                result['latest_period'] = str(latest.get('报告期', 'N/A'))
                result['indicators'] = {
                    '报告期': latest.get('报告期', 'N/A'),
                    '净利润': latest.get('净利润(亿元)', latest.get('净利润(亿)', 'N/A')),
                    '营业收入': latest.get('营业收入(亿元)', latest.get('总营收(亿)', 'N/A')),
                    'ROE': latest.get('净资产收益率(%)', 'N/A'),
                    '毛利率': latest.get('毛利率(%)', 'N/A'),
                    '净利率': latest.get('净利率(%)', 'N/A'),
                    '资产负债率': latest.get('资产负债率(%)', 'N/A'),
                }
                # 保存原始DataFrame用于趋势分析
                result['historical'] = df
        except Exception as e:
            result['indicators_error'] = str(e)
        
        return result
    
    def get_stock_earnings_forecast(self, symbol: str) -> Dict:
        """
        获取个股业绩预告（如有）
        """
        # 尝试最新几个报告期
        periods = [
            self.get_latest_report_period(),
        ]
        
        # 添加其他可能的日期
        now = datetime.now()
        for year in [now.year, now.year-1]:
            for q in ['1231', '0930', '0630', '0331']:
                p = f"{year}{q}"
                if p not in periods:
                    periods.append(p)
        
        for period in periods[:4]:  # 最多试4个
            try:
                df = ak.stock_yjyg_em(date=period)
                stock_data = df[df['股票代码'] == symbol]
                if not stock_data.empty:
                    row = stock_data.iloc[0]
                    return {
                        'period': period,
                        'type': row.get('预告类型', 'N/A'),
                        'date': row.get('公告日期', 'N/A'),
                        'summary': row.get('业绩预告摘要', '')[:200] if row.get('业绩预告摘要') else '',
                        'found': True
                    }
            except:
                continue
        
        return {'found': False, 'period': None}
    
    def search_stock_financial(self, symbol: str) -> Dict:
        """
        综合搜索个股财报信息
        """
        print(f"\n🔍 正在查询 {symbol} 财报数据...")
        print("=" * 50)
        
        result = {
            'symbol': symbol,
            'query_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # 1. 财务指标
        print("1. 获取财务指标...")
        financial = self.get_stock_financial(symbol)
        result['financial'] = financial
        
        # 2. 业绩预告
        print("2. 查询业绩预告...")
        forecast = self.get_stock_earnings_forecast(symbol)
        result['forecast'] = forecast
        
        print("✅ 查询完成")
        return result


def analyze_stock_report(symbol: str, name: str = None) -> str:
    """
    生成个股财报分析报告
    """
    fetcher = FinancialReportFetcher()
    data = fetcher.search_stock_financial(symbol)
    
    if name is None:
        name = symbol
    
    report = []
    report.append("=" * 60)
    report.append(f"📊 {name}({symbol}) 财报分析报告")
    report.append(f"查询时间: {data['query_time']}")
    report.append("=" * 60)
    
    # 财务指标
    fin = data.get('financial', {})
    if 'indicators' in fin:
        indicators = fin['indicators']
        report.append("\n💰 最新财务指标")
        report.append("-" * 50)
        report.append(f"报告期: {indicators.get('报告期', 'N/A')}")
        report.append(f"营业收入: {indicators.get('营业收入', 'N/A')} 亿元")
        report.append(f"净利润: {indicators.get('净利润', 'N/A')} 亿元")
        report.append(f"ROE: {indicators.get('ROE', 'N/A')} %")
        report.append(f"毛利率: {indicators.get('毛利率', 'N/A')} %")
        report.append(f"资产负债率: {indicators.get('资产负债率', 'N/A')} %")
    
    # 业绩预告
    forecast = data.get('forecast', {})
    if forecast.get('found'):
        report.append("\n🔮 最新业绩预告")
        report.append("-" * 50)
        report.append(f"预告类型: {forecast['type']}")
        report.append(f"公告日期: {forecast['date']}")
        if forecast.get('summary'):
            report.append(f"预告摘要: {forecast['summary']}")
    else:
        report.append("\n🔮 业绩预告: 暂无最新预告")
    
    report.append("\n" + "=" * 60)
    
    return "\n".join(report)


class EarningsMonitor:
    """财报监控器 - 扫描业绩异动"""
    
    def __init__(self):
        self.fetcher = FinancialReportFetcher()
    
    def scan_surprises(self) -> List[Dict]:
        """
        扫描业绩超预期/预警股票
        """
        results = []
        
        try:
            # 获取最新业绩预告
            df = self.fetcher.get_performance_forecast()
            if df.empty:
                return results
            
            for _, row in df.iterrows():
                stock_type = row.get('预告类型', '')
                code = row.get('股票代码', '')
                name = row.get('股票简称', '')
                
                # 分类
                if '增' in stock_type or '盈' in stock_type:
                    stype = '预增'
                elif '减' in stock_type or '亏' in stock_type:
                    stype = '预警'
                else:
                    stype = '其他'
                
                results.append({
                    'code': code,
                    'name': name,
                    'type': stype,
                    'forecast_type': stock_type,
                    'summary': row.get('业绩预告摘要', '')
                })
        except Exception as e:
            print(f"扫描失败: {e}")
        
        return results
    
    def get_watchlist_earnings(self, watchlist: List[str]) -> List[Dict]:
        """
        获取关注列表的财报信息
        """
        results = []
        for symbol in watchlist:
            try:
                forecast = self.fetcher.get_stock_earnings_forecast(symbol)
                if forecast.get('found'):
                    results.append({
                        'code': symbol,
                        'forecast': forecast
                    })
            except:
                continue
    def check_watchlist(self, watchlist: List[str]) -> Dict:
        """
        检查关注列表的财报情况
        """
        return {
            'checked': len(watchlist),
            'with_earnings': self.get_watchlist_earnings(watchlist)
        }
    import sys
    
    if len(sys.argv) > 1:
        symbol = sys.argv[1]
        name = sys.argv[2] if len(sys.argv) > 2 else symbol
    else:
        symbol = '688256'  # 寒武纪
        name = '寒武纪'
    
    print(analyze_stock_report(symbol, name))
