#!/usr/bin/env python3
"""
小A - 实时行情监控与做T信号推送
监控标的：澜起科技(688008)、江波龙(301308)
推送渠道：钉钉
"""

import sys
sys.path.insert(0, '/home/node/clawd/agents/小A')

import akshare as ak
import json
import urllib.request
import time
import hmac
import hashlib
import base64
from datetime import datetime

# 钉钉配置
WEBHOOK = "https://oapi.dingtalk.com/robot/send?access_token=d40168005a8f54cd44ee5b1286b57f6dd5a0cd6537eebe6603a3fe80339a2b0a"
SECRET = "SEC51ccb38630ce6f1a160175eee23dda2c9bfd6dc5353d0761a232b077e0ef31df"

# 监控标的
STOCKS = {
    "688008": {"name": "澜起科技", "strategy": "反T", "position": 86.7},
    "301308": {"name": "江波龙", "strategy": "正T", "position": 7.8}
}

def send_dingtalk(title, content):
    """发送钉钉消息"""
    try:
        timestamp = str(round(time.time() * 1000))
        string_to_sign = f"{timestamp}\n{SECRET}"
        hmac_code = hmac.new(SECRET.encode('utf-8'), string_to_sign.encode('utf-8'), digestmod=hashlib.sha256).digest()
        sign = base64.b64encode(hmac_code).decode('utf-8')
        
        url = f"{WEBHOOK}&timestamp={timestamp}&sign={sign}"
        data = {
            "msgtype": "markdown",
            "markdown": {"title": title, "text": content}
        }
        
        req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), 
                                     headers={'Content-Type': 'application/json'}, method='POST')
        response = urllib.request.urlopen(req)
        return response.status == 200
    except Exception as e:
        print(f"推送失败: {e}")
        return False

def get_stock_data(symbol):
    """获取股票实时数据"""
    try:
        # 获取当日分时数据
        df = ak.stock_zh_a_hist(symbol=symbol, period="daily", 
                                start_date=datetime.now().strftime("%Y%m%d"),
                                end_date=datetime.now().strftime("%Y%m%d"))
        if not df.empty:
            return df.iloc[0]
        return None
    except Exception as e:
        print(f"获取{symbol}数据失败: {e}")
        return None

def check_signals():
    """检查交易信号"""
    now = datetime.now()
    time_str = now.strftime("%H:%M")
    
    messages = []
    
    for code, info in STOCKS.items():
        data = get_stock_data(code)
        if data is None:
            continue
            
        name = info["name"]
        strategy = info["strategy"]
        position = info["position"]
        
        open_price = data['开盘']
        current = data['收盘']  # 最新价
        high = data['最高']
        low = data['最低']
        change_pct = data['涨跌幅']
        
        # 计算与开盘价和5日位置的偏差
        open_change = (current - open_price) / open_price * 100
        
        signal = None
        urgency = ""
        
        # 澜起科技 - 反T策略（高位减仓）
        if code == "688008":
            # 反T：冲高减仓
            if open_change > 3:
                signal = f"🔴 反T机会 | 高开{open_change:+.2f}%，建议减仓"
                urgency = "高"
            elif high > open_price * 1.02 and current < high * 0.99:
                signal = f"🟡 反T提示 | 冲高回落，可考虑减仓"
                urgency = "中"
                
        # 江波龙 - 正T策略（低位加仓）
        elif code == "301308":
            # 正T：低开或跳水加仓
            if open_change < -2:
                signal = f"🟢 正T机会 | 低开{open_change:.2f}%，建议加仓"
                urgency = "高"
            elif low < open_price * 0.98 and current > low * 1.01:
                signal = f"🟡 正T提示 | 探底回升，可考虑加仓"
                urgency = "中"
        
        if signal:
            msg = f"""### {name} ({code}) {urgency}优先级
**时间**: {time_str}
**价格**: ¥{current:.2f} ({change_pct:+.2f}%)
**信号**: {signal}
**开盘**: ¥{open_price:.2f} ({open_change:+.2f}%)
**最高**: ¥{high:.2f}
**最低**: ¥{low:.2f}
---
"""
            messages.append(msg)
    
    return messages

def send_summary():
    """发送收盘总结"""
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    
    content = f"## 📊 收盘总结 | {date_str}\n\n"
    
    for code, info in STOCKS.items():
        data = get_stock_data(code)
        if data:
            name = info["name"]
            content += f"**{name} ({code})**: ¥{data['收盘']:.2f} ({data['涨跌幅']:+.2f}%)\n\n"
    
    content += "---\n*🤖 小A | A股交易监控*"
    send_dingtalk("收盘总结", content)

def main():
    """主函数"""
    now = datetime.now()
    time_str = now.strftime("%H:%M")
    
    print(f"[{time_str}] 小A监控运行中...")
    
    # 检查是否在交易时间
    # 早盘: 09:30-11:30, 午盘: 13:00-15:00
    hour = now.hour
    minute = now.minute
    time_val = hour * 100 + minute
    
    is_trading = (930 <= time_val <= 1130) or (1300 <= time_val <= 1500)
    
    if not is_trading:
        print("非交易时间，跳过")
        return
    
    # 检查信号
    signals = check_signals()
    
    if signals:
        # 合并发送
        full_content = "## 🔔 做T信号提醒\n\n" + "\n".join(signals)
        full_content += f"\n*时间: {time_str}*"
        send_dingtalk("做T信号", full_content)
        print(f"已发送 {len(signals)} 条信号")
    else:
        print("无信号")
    
    # 收盘总结 (15:00)
    if time_val == 1500:
        send_summary()

if __name__ == "__main__":
    main()
