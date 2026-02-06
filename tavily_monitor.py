#!/usr/bin/env python3
"""
Tavily API 额度监控
每月1000次免费额度管理
"""

import os
import json
from datetime import datetime, timedelta
from pathlib import Path

API_LIMIT = 1000  # 每月免费额度
USAGE_FILE = '/home/node/clawd/.tavily_usage.json'

class TavilyMonitor:
    """Tavily额度监控器"""
    
    def __init__(self):
        self.usage_data = self._load_usage()
    
    def _load_usage(self) -> dict:
        """加载使用记录"""
        if os.path.exists(USAGE_FILE):
            with open(USAGE_FILE, 'r') as f:
                return json.load(f)
        return {
            'month': datetime.now().strftime('%Y-%m'),
            'calls': 0,
            'daily_usage': {},
            'last_reset': datetime.now().isoformat()
        }
    
    def _save_usage(self):
        """保存使用记录"""
        with open(USAGE_FILE, 'w') as f:
            json.dump(self.usage_data, f, indent=2)
    
    def check_and_reset(self):
        """检查是否需要重置月度额度"""
        current_month = datetime.now().strftime('%Y-%m')
        if self.usage_data['month'] != current_month:
            print(f"🔄 新月度额度重置: {current_month}")
            self.usage_data = {
                'month': current_month,
                'calls': 0,
                'daily_usage': {},
                'last_reset': datetime.now().isoformat()
            }
            self._save_usage()
    
    def record_call(self, purpose: str = ""):
        """记录一次API调用"""
        self.check_and_reset()
        
        self.usage_data['calls'] += 1
        
        today = datetime.now().strftime('%Y-%m-%d')
        if today not in self.usage_data['daily_usage']:
            self.usage_data['daily_usage'][today] = 0
        self.usage_data['daily_usage'][today] += 1
        
        self._save_usage()
        return self.usage_data['calls']
    
    def get_status(self) -> dict:
        """获取额度状态"""
        self.check_and_reset()
        
        used = self.usage_data['calls']
        remaining = API_LIMIT - used
        percentage = (used / API_LIMIT) * 100
        
        today = datetime.now().strftime('%Y-%m-%d')
        today_calls = self.usage_data['daily_usage'].get(today, 0)
        
        # 计算预估
        days_in_month = 30  # 简化计算
        day_of_month = datetime.now().day
        if day_of_month > 1:
            daily_avg = used / day_of_month
            projected = daily_avg * days_in_month
        else:
            projected = used
        
        return {
            'month': self.usage_data['month'],
            'used': used,
            'remaining': remaining,
            'percentage': round(percentage, 1),
            'today_calls': today_calls,
            'projected_monthly': round(projected),
            'status': 'ok' if remaining > 100 else 'warning' if remaining > 20 else 'critical'
        }
    
    def print_report(self):
        """打印额度报告"""
        status = self.get_status()
        
        print("=" * 50)
        print(f"📊 Tavily API 额度报告 ({status['month']})")
        print("=" * 50)
        print(f"总配额:    {API_LIMIT} 次/月")
        print(f"已使用:    {status['used']} 次 ({status['percentage']}%)")
        print(f"剩余:      {status['remaining']} 次")
        print(f"今日使用:  {status['today_calls']} 次")
        print(f"预估月耗:  ~{status['projected_monthly']} 次")
        print("-" * 50)
        
        if status['status'] == 'ok':
            print("✅ 额度充足")
        elif status['status'] == 'warning':
            print("⚠️  额度紧张，建议关注")
        else:
            print("🚨 额度严重不足！")
        
        # 使用建议
        remaining = status['remaining']
        days_left = 30 - datetime.now().day
        if days_left > 0:
            daily_allowance = remaining // days_left
            print(f"建议: 剩余{days_left}天，每天可用约{daily_allowance}次")
        
        print("=" * 50)


def check_before_report() -> bool:
    """
    生成报告前检查额度
    返回: True可以生成, False额度不足
    """
    monitor = TavilyMonitor()
    status = monitor.get_status()
    
    if status['remaining'] < 2:
        print(f"🚨 API额度不足！剩余{status['remaining']}次，至少需要2次")
        return False
    
    if status['remaining'] < 10:
        print(f"⚠️  API额度紧张，剩余{status['remaining']}次")
    
    return True


if __name__ == "__main__":
    import sys
    
    monitor = TavilyMonitor()
    
    if len(sys.argv) > 1 and sys.argv[1] == 'record':
        # 记录一次调用
        count = monitor.record_call()
        print(f"✅ 已记录API调用，本月累计: {count}次")
    else:
        # 显示报告
        monitor.print_report()
