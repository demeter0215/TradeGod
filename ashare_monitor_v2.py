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
    
    def _prepare_save_data(self, current: Dict) -> Dict:
        """
        准备要保存的数据，用于15分钟窗口比较
        如果是新窗口（超过15分钟），重置period_high/low，并保存上一个窗口的成交量
        """
        result = {}
        last_time = None
        is_new_window = False
        
        if self.history and self.history.get('timestamp'):
            try:
                last_time = datetime.fromisoformat(self.history['timestamp'])
                # 判断是否新开一个15分钟窗口
                if (datetime.now() - last_time) >= timedelta(minutes=15):
                    is_new_window = True
            except:
                is_new_window = True
        else:
            is_new_window = True
        
        for code, data in current.items():
            result[code] = {
                'name': data['name'],
                'code': code,
                'price': data['price'],
                'change_pct': data['change_pct'],
                'amount': data['amount'],
                'volume': data['volume'],
                'update_time': data['update_time'],
            }
            
            hist = self.history.get(code, {})
            
            if is_new_window:
                # 新窗口：重置period_high/low为当前价格
                result[code]['period_high'] = data['price']
                result[code]['period_low'] = data['price']
                result[code]['window_start_price'] = data['price']
                result[code]['window_start_time'] = datetime.now().isoformat()
                # 记录窗口起始时的累计成交金额，用于计算本窗口成交量
                result[code]['window_start_amount'] = data['amount']
                
                # 保存上一个窗口的成交量
                # 计算上一个窗口的成交量 = 上次累计量 - 窗口起始时累计量
                last_amount = hist.get('amount', 0)
                last_window_start = hist.get('window_start_amount', 0)
                if last_amount > 0 and last_window_start > 0:
                    last_window_volume = max(0, last_amount - last_window_start)
                    result[code]['prev_window_volume'] = last_window_volume
                else:
                    result[code]['prev_window_volume'] = 0
                    
            else:
                # 同一窗口：继承并更新period_high/low
                old_high = hist.get('period_high', data['price'])
                old_low = hist.get('period_low', data['price'])
                
                result[code]['period_high'] = max(old_high, data['price'])
                result[code]['period_low'] = min(old_low, data['price'])
                result[code]['window_start_price'] = hist.get('window_start_price', data['price'])
                result[code]['window_start_time'] = hist.get('window_start_time', datetime.now().isoformat())
                result[code]['window_start_amount'] = hist.get('window_start_amount', data['amount'])
                
                # 继承历史成交量参考数据
                result[code]['prev_window_volume'] = hist.get('prev_window_volume', 0)
        
        return result
    
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
                        # 腾讯API字段说明：
                        # data[36] = 成交量（手）
                        # data[37] = 成交额（千元）
                        # 将千元转换为元：* 1000
                        amount_qianyuan = float(data[37]) if data[37] else 0
                        result[code] = {
                            'name': symbols.get(code, '未知'),
                            'code': code,
                            'price': float(data[3]) if data[3] else 0,
                            'change': float(data[31]) if data[31] else 0,
                            'change_pct': float(data[32]) if data[32] else 0,
                            'volume': int(data[36]) if data[36] else 0,
                            'amount': amount_qianyuan * 1000,  # 千元转元
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
    
    def analyze_trend(self, current: Dict, history: Dict) -> Tuple[float, str, str, str]:
        """
        分析15分钟走势形态和量价结构
        
        Returns:
            (max_fluctuation, trend_type, trend_desc, volume_structure)
            max_fluctuation: 15分钟区间内最大波动幅度(%)
            trend_type: 走势类型代码
            trend_desc: 走势描述
            volume_structure: 量价结构描述（如"放量上涨"、"缩量下跌"等）
        """
        if not history:
            return 0, 'unknown', '无历史数据', '数据不足'
        
        # 获取15分钟窗口的起始价格（即上次检查时的价格）
        start_price = history.get('price', current['price'])
        end_price = current['price']
        
        # 获取15分钟窗口内记录的高低点
        period_high = history.get('period_high', start_price)
        period_low = history.get('period_low', start_price)
        
        # 用当前价格更新15分钟窗口的高低点
        current_high = max(period_high, current['price'])
        current_low = min(period_low, current['price'])
        
        # 计算15分钟内的最大波动幅度（相对于起始价）
        if start_price > 0:
            up_fluctuation = (current_high - start_price) / start_price * 100
            down_fluctuation = (current_low - start_price) / start_price * 100
            max_fluctuation = max(abs(up_fluctuation), abs(down_fluctuation))
        else:
            max_fluctuation = 0
            up_fluctuation = down_fluctuation = 0
        
        # 判断走势形态
        price_change_pct = (end_price - start_price) / start_price * 100 if start_price > 0 else 0
        
        # 检查是否有V型反转特征（既有明显上涨又有明显下跌）
        v_threshold = 0.3  # V型判断阈值 0.3%
        if up_fluctuation > v_threshold and abs(down_fluctuation) > v_threshold:
            if price_change_pct > 0:
                trend_type = 'v_up'
                trend_desc = f'V型反转↑({current_low:.2f}→{current_high:.2f})'
            else:
                trend_type = 'v_down'
                trend_desc = f'倒V反转↓({current_high:.2f}→{current_low:.2f})'
        # 持续上涨（低点在起始价附近，高点明显高于起始价，最终收涨）
        elif up_fluctuation > 0.2 and price_change_pct > 0:
            trend_type = 'rise'
            trend_desc = f'15分钟上涨↑+{price_change_pct:.2f}%'
        # 持续下跌（高点在起始价附近，低点明显低于起始价，最终收跌）
        elif abs(down_fluctuation) > 0.2 and price_change_pct < 0:
            trend_type = 'fall'
            trend_desc = f'15分钟下跌↓{price_change_pct:.2f}%'
        # 横盘震荡（波动很小）
        elif max_fluctuation < 0.15:
            trend_type = 'consolidate'
            trend_desc = f'15分钟横盘({max_fluctuation:.2f}%)'
        # 其他震荡走势
        else:
            trend_type = 'mixed'
            trend_desc = f'15分钟震荡({price_change_pct:+.2f}%)'
        
        # 分析量价结构
        volume_structure = self._analyze_volume_structure(
            current, history, trend_type, price_change_pct
        )
        
        return max_fluctuation, trend_type, trend_desc, volume_structure
    
    def _analyze_volume_structure(self, current: Dict, history: Dict, 
                                   trend_type: str, price_change_pct: float) -> str:
        """
        分析量价结构
        结合15分钟走势和成交量变化给出盘面结构判断
        """
        # 计算当前15分钟内的成交量（累计成交量 - 窗口起始时累计量）
        current_amount = current.get('amount', 0)
        window_start_amount = history.get('window_start_amount', history.get('amount', 0))
        current_window_volume = max(0, current_amount - window_start_amount)
        
        # 获取上一个15分钟的成交量
        prev_window_volume = history.get('prev_window_volume', 0)
        
        # 计算成交量变化率
        if prev_window_volume > 0:
            volume_change_pct = (current_window_volume - prev_window_volume) / prev_window_volume * 100
        else:
            volume_change_pct = 0
        
        # 判断放量/缩量阈值
        is_volume_up = volume_change_pct >= 30   # 放量：增长30%以上
        is_volume_down = volume_change_pct <= -30  # 缩量：减少30%以上
        is_volume_normal = not is_volume_up and not is_volume_down
        
        # 构建量价结构描述
        volume_desc = ""
        if is_volume_up:
            volume_desc = "放量"
        elif is_volume_down:
            volume_desc = "缩量"
        else:
            volume_desc = "平量"
        
        # 结合价格走势给出完整结构
        if trend_type == 'v_up':
            if is_volume_up:
                return f"放量深V↑ 资金托底明显(+{volume_change_pct:.0f}%)"
            elif is_volume_down:
                return f"缩量深V↑ 反弹力度存疑({volume_change_pct:.0f}%)"
            else:
                return f"平量深V↑({volume_change_pct:.0f}%)"
        
        elif trend_type == 'v_down':
            if is_volume_up:
                return f"放量倒V↓ 资金出逃({volume_change_pct:.0f}%)"
            elif is_volume_down:
                return f"缩量倒V↓ 买盘不足({volume_change_pct:.0f}%)"
            else:
                return f"平量倒V↓({volume_change_pct:.0f}%)"
        
        elif trend_type == 'rise':
            if is_volume_up:
                return f"放量上涨↑ 资金入场积极(+{volume_change_pct:.0f}%)"
            elif is_volume_down:
                return f"缩量上涨↑ 上涨动能减弱({volume_change_pct:.0f}%)"
            else:
                return f"平量上涨↑({volume_change_pct:.0f}%)"
        
        elif trend_type == 'fall':
            if is_volume_up:
                return f"放量下跌↓ 恐慌盘涌出({volume_change_pct:.0f}%)"
            elif is_volume_down:
                return f"缩量下跌↓ 抛压减轻({volume_change_pct:.0f}%)"
            else:
                return f"平量下跌↓({volume_change_pct:.0f}%)"
        
        elif trend_type == 'consolidate':
            if is_volume_up:
                return f"放量横盘 变盘信号(+{volume_change_pct:.0f}%)"
            elif is_volume_down:
                return f"缩量横盘 观望情绪浓({volume_change_pct:.0f}%)"
            else:
                return f"平量横盘({volume_change_pct:.0f}%)"
        
        else:  # mixed
            if is_volume_up:
                return f"放量震荡 多空分歧加大(+{volume_change_pct:.0f}%)"
            elif is_volume_down:
                return f"缩量震荡 交投清淡({volume_change_pct:.0f}%)"
            else:
                return f"平量震荡({volume_change_pct:.0f}%)"
    
    def check_anomalies_v2(self, current: Dict, history: Dict) -> List[Dict]:
        """
        检查异常情况 V2
        基于15分钟最大波动、走势形态和成交量变化
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
            
            # 分析走势和量价结构
            max_fluct, trend_type, trend_desc, volume_structure = self.analyze_trend(data, hist_data)
            
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
                    'volume_structure': volume_structure,
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
                        'volume_structure': volume_structure,
                        'level': 'high',
                        'data': data
                    })
                    data['alerted_large_change'] = True
            
            # 检查3: 15分钟成交量较上一周期放大30%以上
            current_amount = data.get('amount', 0)
            window_start_amount = hist_data.get('window_start_amount', hist_data.get('amount', 0))
            current_window_volume = max(0, current_amount - window_start_amount)
            prev_window_volume = hist_data.get('prev_window_volume', 0)
            
            if prev_window_volume > 0:
                volume_change_pct = (current_window_volume - prev_window_volume) / prev_window_volume * 100
                
                # 成交量增长超过30%触发告警
                if volume_change_pct >= 30:
                    # 根据量价结构确定告警级别
                    if '放量' in volume_structure and ('下跌' in volume_structure or '恐慌' in volume_structure):
                        level = 'high'  # 放量下跌是高风险信号
                    elif '放量' in volume_structure and ('上涨' in volume_structure or '托底' in volume_structure):
                        level = 'medium'  # 放量上涨或托底是机会信号
                    else:
                        level = 'medium'
                    
                    alerts.append({
                        'type': 'volume_spike_15min',
                        'code': code,
                        'name': data['name'],
                        'message': f"15分钟成交量放量 +{volume_change_pct:.0f}%",
                        'detail': f"当前: {current_window_volume/10000:.0f}万 | 上周期: {prev_window_volume/10000:.0f}万",
                        'volume_structure': volume_structure,
                        'level': level,
                        'trend': trend_type,
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
            
            # 获取量价结构描述
            volume_structure = alert.get('volume_structure', '')
            
            lines.append(f"{level_emoji} 【{alert['name']}】{trend_emoji}")
            lines.append(f"   波动: {alert['message']}")
            lines.append(f"   走势: {alert['detail']}")
            if volume_structure:
                lines.append(f"   盘面: {volume_structure}")
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
        
        # 准备保存数据（包含15分钟窗口追踪）
        save_data = self._prepare_save_data(current)
        
        # 检查异常（使用当前数据和历史数据对比）
        if self.history:
            alerts = self.check_anomalies_v2(current, self.history)
            if alerts:
                message = self.format_alert_message_v2(alerts)
                print(f"发现 {len(alerts)} 个异常！")
                self._save_history(save_data)
                return message
            else:
                print("无异常")
        else:
            print("首次运行，记录基准数据")
        
        # 保存当前数据
        self._save_history(save_data)
        return None
    
    def debug_show_data(self) -> str:
        """调试模式：显示所有监控数据详情"""
        current = self.get_index_data()
        if not current:
            return "获取数据失败"
        
        lines = [
            "=" * 70,
            f"📊 A股监控V2 数据详情 | {datetime.now().strftime('%H:%M:%S')}",
            "=" * 70,
            ""
        ]
        
        for code, data in current.items():
            lines.append(f"【{data['name']}】{code}")
            lines.append(f"  当前价格: {data['price']:.2f} ({data['change_pct']:+.2f}%)")
            lines.append(f"  当日最高: {data['high']:.2f} | 当日最低: {data['low']:.2f}")
            lines.append(f"  累计成交额: {data['amount']/10000:.0f}万")
            lines.append("")
            
            if self.history and code in self.history:
                hist = self.history[code]
                
                # 15分钟窗口数据
                window_start = hist.get('window_start_price', 'N/A')
                window_start_time = hist.get('window_start_time', 'N/A')
                period_high = hist.get('period_high', 'N/A')
                period_low = hist.get('period_low', 'N/A')
                window_start_amount = hist.get('window_start_amount', 0)
                prev_volume = hist.get('prev_window_volume', 0)
                
                lines.append(f"  📌 当前15分钟窗口:")
                lines.append(f"     窗口起始价: {window_start}")
                lines.append(f"     窗口起始时间: {window_start_time}")
                lines.append(f"     窗口内高点: {period_high}")
                lines.append(f"     窗口内低点: {period_low}")
                lines.append(f"     窗口起始累计额: {window_start_amount/10000:.0f}万" if window_start_amount else f"     窗口起始累计额: N/A")
                lines.append("")
                
                lines.append(f"  📌 上一个15分钟窗口:")
                lines.append(f"     成交量: {prev_volume/10000:.0f}万" if prev_volume else f"     成交量: N/A (无历史数据)")
                lines.append("")
                
                # 计算当前窗口成交量
                if window_start_amount:
                    current_window_vol = max(0, data['amount'] - window_start_amount)
                    lines.append(f"  📌 当前窗口已成交: {current_window_vol/10000:.0f}万")
                    
                    if prev_volume > 0:
                        vol_change = (current_window_vol - prev_volume) / prev_volume * 100
                        lines.append(f"  📌 较上周期变化: {vol_change:+.1f}%")
                lines.append("")
                
                # 分析结果
                max_fluct, trend_type, trend_desc, vol_structure = self.analyze_trend(data, hist)
                lines.append(f"  📊 分析结果:")
                lines.append(f"     15分钟波动: {max_fluct:.2f}%")
                lines.append(f"     走势类型: {trend_type}")
                lines.append(f"     走势描述: {trend_desc}")
                lines.append(f"     量价结构: {vol_structure}")
            else:
                lines.append("  ⚠️ 无历史数据（首次运行）")
            
            lines.append("-" * 70)
            lines.append("")
        
        return "\n".join(lines)


def main():
    """主函数"""
    import sys
    monitor = AShareMonitor()
    
    # 检查是否有debug参数
    if len(sys.argv) > 1 and sys.argv[1] == '--debug':
        message = monitor.debug_show_data()
        print(message)
        return message
    
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
