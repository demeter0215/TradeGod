#!/usr/bin/env python3
"""
美股实时数据获取模块
使用腾讯财经API（稳定可靠）
"""

import requests
import re
from datetime import datetime
from typing import Dict, Optional

class USStockFetcher:
    """美股实时数据获取器"""
    
    def __init__(self):
        self.base_url = "https://qt.gtimg.cn/q="
    
    def get_stock_data(self, symbols: list) -> Dict:
        """
        获取美股实时数据
        
        Args:
            symbols: 股票代码列表，如 ['AAPL', 'NVDA', 'TSLA']
        
        Returns:
            字典格式的股票数据
        """
        # 转换符号格式
        symbol_str = ",".join([f"us{s}" for s in symbols])
        url = f"{self.base_url}{symbol_str}"
        
        try:
            response = requests.get(url, timeout=10)
            response.encoding = 'gb2312'
            
            result = {}
            for line in response.text.strip().split(';'):
                if not line.strip():
                    continue
                
                # 解析数据
                match = re.search(r'v_us(\w+)="(.+)"', line)
                if match:
                    symbol = match.group(1)
                    data = match.group(2).split('~')
                    
                    if len(data) >= 30:
                        result[symbol] = {
                            'symbol': symbol,
                            'name_cn': data[1] if len(data) > 1 else '',
                            'name_en': data[2] if len(data) > 2 else '',
                            'price': float(data[3]) if data[3] else 0,
                            'yesterday_close': float(data[4]) if data[4] else 0,
                            'open': float(data[5]) if data[5] else 0,
                            'volume': int(data[6]) if data[6] else 0,
                            'high': float(data[33]) if len(data) > 33 and data[33] else 0,
                            'low': float(data[34]) if len(data) > 34 and data[34] else 0,
                            'change': float(data[31]) if len(data) > 31 and data[31] else 0,
                            'change_percent': float(data[32]) if len(data) > 32 and data[32] else 0,
                            'update_time': data[30] if len(data) > 30 else '',
                            'market_cap': data[44] if len(data) > 44 else '',
                            'pe': data[39] if len(data) > 39 else '',
                            'pb': data[46] if len(data) > 46 else '',
                        }
            
            return result
            
        except Exception as e:
            print(f"获取美股数据失败: {e}")
            return {}
    
    def get_mag7_data(self) -> Dict:
        """获取MAG7实时数据"""
        mag7_symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA']
        return self.get_stock_data(mag7_symbols)
    
    def format_stock_info(self, data: Dict) -> str:
        """格式化股票信息"""
        if not data:
            return "无数据"
        
        symbol = data.get('symbol', 'N/A')
        price = data.get('price', 0)
        change = data.get('change', 0)
        change_pct = data.get('change_percent', 0)
        update_time = data.get('update_time', '')
        
        emoji = "🟢" if change >= 0 else "🔴"
        
        return f"{emoji} {symbol}: ${price:.2f} ({change:+.2f}, {change_pct:+.2f}%) [{update_time}]"
    
    def check_data_freshness(self, data: Dict, max_delay_minutes: int = 15) -> bool:
        """
        检查数据时效性
        
        Args:
            data: 股票数据
            max_delay_minutes: 最大允许延迟（分钟）
        
        Returns:
            数据是否新鲜
        """
        try:
            update_time = data.get('update_time', '')
            if not update_time:
                return False
            
            # 解析时间
            data_time = datetime.strptime(update_time, '%Y-%m-%d %H:%M:%S')
            now = datetime.now()
            
            # 计算延迟
            delay = (now - data_time).total_seconds() / 60
            
            return delay <= max_delay_minutes
            
        except:
            return False


# ==================== 测试 ====================

if __name__ == "__main__":
    print("=" * 70)
    print("🚀 美股实时数据测试 - 腾讯财经API")
    print("=" * 70)
    
    fetcher = USStockFetcher()
    
    # 测试MAG7
    print("\n📊 MAG7 实时数据:")
    print("-" * 70)
    
    mag7 = fetcher.get_mag7_data()
    
    for symbol, data in mag7.items():
        if data:
            info = fetcher.format_stock_info(data)
            print(info)
            
            # 检查时效性
            is_fresh = fetcher.check_data_freshness(data, max_delay_minutes=15)
            status = "✅ 实时" if is_fresh else "⚠️ 延迟"
            print(f"   数据状态: {status}")
    
    # 获取更新时间
    if mag7:
        first = list(mag7.values())[0]
        print(f"\n📅 数据更新时间: {first.get('update_time', 'N/A')}")
    
    print("\n" + "=" * 70)
    print("✅ 数据源可用！将集成到定时任务中")
    print("=" * 70)
