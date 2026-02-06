#!/usr/bin/env python3
"""
A股四大板块指数实时监控系统 V2
记录15分钟高低点，判断走势形态
"""

import sys
sys.path.insert(0, '/home/node/clawd')

import requests
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import os

class AShareMonitor:
    """A股板块监控器 V2"""
    
    def __init__(self):
        self.data_file = '/home/node/clawd/.market_monitor_data_v2.json'
        self.history = self._load_history()
    
    def _load_history(self) -> Dict:
        """加载历史数据（包含15分钟内的高低记录）"""
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
    
    def _save_history(self, data: Dict):
        """保存历史数据"""
        data['timestamp'] = datetime.now().isoformat()
        try:
            with open(self.data_file, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            print(f"保存数据失败: {e}")
    
    def get_index_data(self) -> Dict:
        """获取四大板块指数数据"""
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
                            'volume': int(data[36]) if data[36] else 0,
                            'amount': float(data[37]) if data[37] else 0,
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
    
    def analyze_trend(self, current: Dict, history: Dict) -> Tuple[float, str, str]:
        """
        分析15分钟走势形态
        
        Returns:
            (max_fluctuation, trend_type, trend_desc)
            max_fluctuation: 最大波动幅度(%)
            trend_type: 走势类型代码
            trend_desc: 走势描述
        """
        if not history or 'high' not in history:
            return 0, 'unknown', '无历史数据'
        
        # 计算15分钟内最大波动（用历史记录的高低vs当前）
        # 或者如果历史有记录期间高低，直接用
        period_high = max(current['high'], history.get('period_high', current['high']))
        period_low = min(current['low'], history.get('period_low', current['low']))
        
        start_price = history.get('price', current['price'])
        end_price = current['price']
        
        # 最大波动幅度（相对于起始价）
        if start_price > 0:
            high_fluctuation = (period_high - start_price) / start_price * 100
            low_fluctuation = (period_low - start_price) / start_price * 100
            max_fluctuation = max(abs(high_fluctuation), abs(low_fluctuation))
        else:
            max_fluctuation = 0
        
        # 判断走势形态
        price_change = end_price - start_price
        
        # 检查是否有V型反转特征
        if period_high > start_price * 1.003 and period_low < start_price * 0.997:
            # 既有新高又有新低，可能是震荡或V型
            if price_change > 0:
                return max_fluctuation, 'v_up', f'V型反转↑(低{period_low:.2f}→高{period_high:.2f})'
            else:
                return max_fluctuation, 'v_down', f'倒V反转↓(高{period_high:.2f}→低{period_low:.2f})'
        
        # 持续上涨
        if period_high > start_price * 1.002 and period_low >= start_price * 0.998:
            if price_change > 0:
                return max_fluctuation, 'rise', f'持续上涨↑({start_price:.2f}→{period_high:.2f})'
        
        # 持续下跌
        if period_low < start_price * 0.998 and period_high <= start_price * 1.002:
            if price_change < 0:
                return max_fluctuation, 'fall', f'持续下跌↓({start_price:.2f}→{period_low:.2f})'
        
        # 横盘震荡
        if abs(price_change) / start_price < 0.002:
            return max_fluctuation, 'consolidate', f'横盘震荡({period_low:.2f}-{period_high:.2f})'
        
        # 其他
        return max_fluctuation, 'mixed', f'震荡走势({period_low:.2f}-{period_high:.2f})'
    
    def check_anomalies_v2(self, current: Dict, history: Dict) -> List[Dict]:
        """
        检查异常情况 V2
        基于15分钟最大波动和走势形态
        """
        alerts = []
        
        # 阈值设置
        thresholds = {
            'sh000001': {'rapid': 0.5, 'large': 1.5},
            'sz399001': {'rapid': 0.7, 'large': 2.0},
            'sz399006': {'rapid': 1.0, 'large': 2.5},
            'sh000688': {'rapid': 1.0, 'large': 2.5},
        }
        
        for code, data in current.items():
            if code not in history:
                continue
            
            threshold = thresholds.get(code, {'rapid': 0.7, 'large': 2.0})
            hist_data = history[code]
            
            # 分析走势
            max_fluct, trend_type, trend_desc = self.analyze_trend(data, hist_data)
            
            # 检查1: 15分钟最大波动超过阈值
            if max_fluct >= threshold['rapid']:
                # 根据走势类型确定级别
                if trend_type in ['v_up', 'v_down']:
                    level = 'high'
                elif trend_type in ['rise', 'fall']:
                    level = 'medium'
                else:
                    level = 'medium'
                
                alerts.append({
                    'type': 'fluctuation',
                    'code': code,
                    'name': data['name'],
                    'message': f"15分钟波动 {max_fluct:.2f}%",
                    'detail': trend_desc,
                    'level': level,
                    'trend': trend_type,
                    'data': data
                })
            
            # 检查2: 当日大波动
            if abs(data['change_pct']) >= threshold['large']:
                if not hist_data.get('alerted_large_change'):
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
            
            # 检查3: 成交量放大
            if hist_data.get('amount') and hist_data['amount'] > 0:
                volume_change = (data['amount'] - hist_data['amount']) / hist_data['amount'] * 100
                if volume_change > 50:
                    alerts.append({
                        'type': 'volume_spike',
                        'code': code,
                        'name': data['name'],
                        'message': f"成交量放大 {volume_change:.0f}%",
                        'detail': f"成交激增",
                        'level': 'medium',
                        'data': data
                    })
        
        return alerts
    
    def format_alert_message_v2(self, alerts: List[Dict]) -> str:
        """格式化告警消息 V2"""
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
            trend_emoji = {
                'rise': '📈',
                'fall': '📉',
                'v_up': '〰️📈',
                'v_down': '〰️📉',
                'consolidate': '➡️',
                'mixed': '〰️'
            }.get(alert.get('trend'), '⚠️')
            
            lines.append(f"{level_emoji} 【{alert['name']}】{trend_emoji}")
            lines.append(f"   波动: {alert['message']}")
            lines.append(f"   走势: {alert['detail']}")
            lines.append(f"   现价: {alert['data']['price']:.2f} ({alert['data']['change_pct']:+.2f}%)")
            lines.append("")
        
        lines.append("=" * 60)
        lines.append("⚠️ 建议关注，注意风险控制")
        lines.append("💡 走势说明: 📈持续涨 📉持续跌 〰️V型 ➡️横盘")
        
        return "\n".join(lines)
    
    def run_check(self) -> Optional[str]:
        """执行检查 V2"""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 开始检查A股板块（V2）...")
        
        # 获取当前数据
        current = self.get_index_data()
        if not current:
            print("获取数据失败")
            return None
        
        print(f"获取到 {len(current)} 个指数数据")
        
        # 检查异常
        if self.history:
            alerts = self.check_anomalies_v2(current, self.history)
            if alerts:
                message = self.format_alert_message_v2(alerts)
                print(f"发现 {len(alerts)} 个异常！")
                self._save_history(current)
                return message
            else:
                print("无异常")
        else:
            print("首次运行，记录基准数据")
        
        # 保存当前数据
        self._save_history(current)
        return None


def main():
    """主函数"""
    monitor = AShareMonitor()
    message = monitor.run_check()
    
    if message:
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
