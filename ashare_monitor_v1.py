#!/usr/bin/env python3
"""
A股四大板块指数实时监控系统
交易时段内每15分钟检查，异常时推送告警
"""

import sys
sys.path.insert(0, '/home/node/clawd')

import requests
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os

class AShareMonitor:
    """A股板块监控器"""
    
    def __init__(self):
        # 存储历史数据用于对比
        self.data_file = '/home/node/clawd/.market_monitor_data.json'
        self.last_data = self._load_last_data()
    
    def _load_last_data(self) -> Dict:
        """加载上次数据"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    # 检查数据是否过期（超过20分钟）
                    if data.get('timestamp'):
                        last_time = datetime.fromisoformat(data['timestamp'])
                        if datetime.now() - last_time < timedelta(minutes=20):
                            return data
            except:
                pass
        return {}
    
    def _save_data(self, data: Dict):
        """保存当前数据"""
        data['timestamp'] = datetime.now().isoformat()
        try:
            with open(self.data_file, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            print(f"保存数据失败: {e}")
    
    def get_index_data(self) -> Dict:
        """
        获取四大板块指数数据
        上证、深证、创业板、科创50
        """
        # 腾讯财经API
        symbols = {
            'sh000001': '上证指数',
            'sz399001': '深证成指', 
            'sz399006': '创业板指',
            'sh000688': '科创50'
        }
        
        symbol_str = ','.join(symbols.keys())
        url = f"https://qt.gtimg.cn/q={symbol_str}"
        
        try:
            response = requests.get(url, timeout=10)
            response.encoding = 'gb2312'
            
            result = {}
            for line in response.text.strip().split(';'):
                if not line.strip():
                    continue
                
                match = re.search(r'v_(sh\d+|sz\d+)="(.+)"', line)
                if match:
                    code = match.group(1)
                    data = match.group(2).split('~')
                    
                    if len(data) >= 45:
                        result[code] = {
                            'name': symbols.get(code, '未知'),
                            'code': code,
                            'price': float(data[3]) if data[3] else 0,
                            'change': float(data[31]) if data[31] else 0,
                            'change_pct': float(data[32]) if data[32] else 0,
                            'volume': int(data[36]) if data[36] else 0,  # 成交量（手）
                            'amount': float(data[37]) if data[37] else 0,  # 成交额（万）
                            'high': float(data[33]) if data[33] else 0,
                            'low': float(data[34]) if data[34] else 0,
                            'open': float(data[5]) if data[5] else 0,
                            'pre_close': float(data[4]) if data[4] else 0,
                            'update_time': data[30] if len(data) > 30 else '',
                        }
            
            return result
            
        except Exception as e:
            print(f"获取指数数据失败: {e}")
            return {}
    
    def check_anomalies(self, current: Dict, last: Dict) -> List[Dict]:
        """
        检查异常情况
        
        板块阈值设置（考虑不同波动性）：
        ┌──────────────┬────────────┬────────────┐
        │ 板块         │ 快速涨跌   │ 日内大波动 │
        ├──────────────┼────────────┼────────────┤
        │ 上证指数     │ ±0.5%      │ ±1.5%      │
        │ 深证成指     │ ±0.7%      │ ±2.0%      │
        │ 创业板指     │ ±1.0%      │ ±2.5%      │
        │ 科创50       │ ±1.0%      │ ±2.5%      │
        └──────────────┴────────────┴────────────┘
        
        其他监控项：
        - 成交量放大：≥50%（各板块一致）
        - 跌破开盘价：≥0.3%（各板块一致）
        """
        alerts = []
        
        # 定义不同板块的阈值
        thresholds = {
            'sh000001': {'rapid': 0.5, 'large': 1.5},   # 上证指数
            'sz399001': {'rapid': 0.7, 'large': 2.0},   # 深证成指
            'sz399006': {'rapid': 1.0, 'large': 2.5},   # 创业板指
            'sh000688': {'rapid': 1.0, 'large': 2.5},   # 科创50
        }
        
        for code, data in current.items():
            if code not in last:
                continue
            
            # 获取该板块的阈值
            threshold = thresholds.get(code, {'rapid': 0.7, 'large': 2.0})
            
            last_data = last[code]
            
            # 检查1: 15分钟快速涨跌（按板块设不同阈值）
            price_change = data['price'] - last_data['price']
            change_pct_15min = (price_change / last_data['price']) * 100 if last_data['price'] else 0
            
            if abs(change_pct_15min) >= threshold['rapid']:
                level = 'high' if abs(change_pct_15min) >= threshold['rapid'] * 2 else 'medium'
                direction = '上涨' if change_pct_15min > 0 else '下跌'
                alerts.append({
                    'type': 'rapid_change',
                    'code': code,
                    'name': data['name'],
                    'message': f"15分钟{direction}{change_pct_15min:+.2f}%",
                    'detail': f"从 {last_data['price']:.2f} → {data['price']:.2f}",
                    'level': level,
                    'data': data
                })
            
            # 检查2: 成交量突然放大
            if last_data.get('amount') and last_data['amount'] > 0:
                volume_change = (data['amount'] - last_data['amount']) / last_data['amount'] * 100
                if volume_change > 50:  # 成交量放大50%以上
                    alerts.append({
                        'type': 'volume_spike',
                        'code': code,
                        'name': data['name'],
                        'message': f"成交量放大 {volume_change:.0f}%",
                        'detail': f"成交额: {last_data['amount']/10000:.0f}万 → {data['amount']/10000:.0f}万",
                        'level': 'medium',
                        'data': data
                    })
            
            # 检查3: 当日涨跌幅过大（按板块设不同阈值）
            if abs(data['change_pct']) >= threshold['large']:
                if not last_data.get('alerted_large_change'):
                    direction = '大涨' if data['change_pct'] > 0 else '大跌'
                    alerts.append({
                        'type': 'large_daily_change',
                        'code': code,
                        'name': data['name'],
                        'message': f"当日{data['change_pct']:+.2f}%",
                        'detail': f"{direction}（超过{threshold['large']}%阈值）",
                        'level': 'high',
                        'data': data
                    })
                    data['alerted_large_change'] = True
            
            # 检查4: 跌破开盘价（阈值0.3%，各板块一致）
            if data['price'] < data['open'] * 0.997:
                drop_pct = (data['price'] - data['open']) / data['open'] * 100
                if not last_data.get('alerted_below_open'):
                    alerts.append({
                        'type': 'below_open',
                        'code': code,
                        'name': data['name'],
                        'message': f"跌破开盘价 {drop_pct:.2f}%",
                        'detail': f"开盘 {data['open']:.2f} → 当前 {data['price']:.2f}",
                        'level': 'medium',
                        'data': data
                    })
                    data['alerted_below_open'] = True
        
        return alerts
    
    def format_alert_message(self, alerts: List[Dict]) -> str:
        """格式化告警消息"""
        if not alerts:
            return ""
        
        now = datetime.now().strftime('%H:%M:%S')
        
        lines = [
            f"🚨 A股异常波动告警 | {now}",
            "=" * 60,
            f"发现 {len(alerts)} 个异常:\n"
        ]
        
        for alert in alerts:
            level_emoji = "🔴" if alert['level'] == 'high' else "🟡"
            lines.append(f"{level_emoji} 【{alert['name']}】")
            lines.append(f"   异常: {alert['message']}")
            lines.append(f"   详情: {alert['detail']}")
            lines.append(f"   现价: {alert['data']['price']:.2f} ({alert['data']['change_pct']:+.2f}%)")
            lines.append("")
        
        lines.append("=" * 60)
        lines.append("⚠️ 建议关注，注意风险控制")
        
        return "\n".join(lines)
    
    def run_check(self) -> Optional[str]:
        """
        执行检查
        返回: 如果有异常返回消息，否则返回None
        """
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 开始检查A股板块...")
        
        # 获取当前数据
        current = self.get_index_data()
        if not current:
            print("获取数据失败")
            return None
        
        print(f"获取到 {len(current)} 个指数数据")
        for code, data in current.items():
            print(f"  {data['name']}: {data['price']:.2f} ({data['change_pct']:+.2f}%)")
        
        # 检查异常
        if self.last_data:
            alerts = self.check_anomalies(current, self.last_data)
            if alerts:
                message = self.format_alert_message(alerts)
                print(f"发现 {len(alerts)} 个异常！")
                # 保存当前数据
                self._save_data(current)
                return message
            else:
                print("无异常")
        else:
            print("首次运行，无历史数据对比")
        
        # 保存当前数据
        self._save_data(current)
        return None


def main():
    """主函数"""
    monitor = AShareMonitor()
    message = monitor.run_check()
    
    if message:
        # 发送钉钉通知
        try:
            from dingtalk_notifier import send_market_summary
            send_market_summary(message)
            print("✅ 告警已发送")
        except Exception as e:
            print(f"发送通知失败: {e}")
            print(message)
    else:
        print("✅ 检查完成，无异常")


if __name__ == "__main__":
    main()
