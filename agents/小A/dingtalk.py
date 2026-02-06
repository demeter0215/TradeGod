#!/usr/bin/env python3
"""
小A - 钉钉推送工具
A股交易信号推送模块
"""

import json
import urllib.request
import time
import hmac
import hashlib
import base64
from datetime import datetime

# 钉钉配置（从环境变量或配置文件读取更安全）
WEBHOOK = "https://oapi.dingtalk.com/robot/send?access_token=d40168005a8f54cd44ee5b1286b57f6dd5a0cd6537eebe6603a3fe80339a2b0a"
SECRET = "SEC51ccb38630ce6f1a160175eee23dda2c9bfd6dc5353d0761a232b077e0ef31df"

def send_markdown(title: str, content: str):
    """发送 Markdown 格式消息"""
    # 加签
    timestamp = str(round(time.time() * 1000))
    string_to_sign = f"{timestamp}\n{SECRET}"
    hmac_code = hmac.new(SECRET.encode('utf-8'), string_to_sign.encode('utf-8'), digestmod=hashlib.sha256).digest()
    sign = base64.b64encode(hmac_code).decode('utf-8')
    
    # 构建 URL
    url = f"{WEBHOOK}&timestamp={timestamp}&sign={sign}"
    
    # 构建消息
    data = {
        "msgtype": "markdown",
        "markdown": {
            "title": title,
            "text": content
        }
    }
    
    # 发送
    req = urllib.request.Request(
        url, 
        data=json.dumps(data).encode('utf-8'), 
        headers={'Content-Type': 'application/json'}, 
        method='POST'
    )
    response = urllib.request.urlopen(req)
    return json.loads(response.read().decode('utf-8'))

def send_text(content: str):
    """发送纯文本消息"""
    timestamp = str(round(time.time() * 1000))
    string_to_sign = f"{timestamp}\n{SECRET}"
    hmac_code = hmac.new(SECRET.encode('utf-8'), string_to_sign.encode('utf-8'), digestmod=hashlib.sha256).digest()
    sign = base64.b64encode(hmac_code).decode('utf-8')
    
    url = f"{WEBHOOK}&timestamp={timestamp}&sign={sign}"
    
    data = {
        "msgtype": "text",
        "text": {
            "content": content
        }
    }
    
    req = urllib.request.Request(
        url, 
        data=json.dumps(data).encode('utf-8'), 
        headers={'Content-Type': 'application/json'}, 
        method='POST'
    )
    response = urllib.request.urlopen(req)
    return json.loads(response.read().decode('utf-8'))

def send_trade_signal(
    symbol: str,
    name: str,
    action: str,  # 买入/卖出/观望
    price: float,
    reason: str,
    risk_level: str = "中",  # 高/中/低
    position: str = ""
):
    """发送交易信号"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    action_emoji = {"买入": "🟢", "卖出": "🔴", "观望": "🟡", "持有": "🔵"}.get(action, "⚪")
    
    content = f"""## {action_emoji} 交易信号 | {symbol} {name}

**操作建议：{action}**

| 项目 | 详情 |
|------|------|
| 代码 | {symbol} |
| 名称 | {name} |
| 参考价格 | ¥{price:.2f} |
| 风险等级 | {risk_level} |
| 时间 | {now} |
{f"| 建议仓位 | {position} |" if position else ""}

**分析理由：**
{reason}

---
*⚠️ 风险提示：以上仅供参考，不构成投资建议。市场有风险，投资需谨慎。*
"""
    
    return send_markdown(f"交易信号 - {symbol}", content)

def send_daily_report(
    market_summary: str,
    watchlist: list,
    signals: list
):
    """发送每日复盘报告"""
    now = datetime.now().strftime("%Y-%m-%d")
    
    watchlist_str = "\n".join([f"- {s['symbol']} {s['name']}: {s['change']}" for s in watchlist[:5]])
    signals_str = "\n".join([f"- {s['symbol']}: {s['action']}" for s in signals]) if signals else "今日无交易信号"
    
    content = f"""## 📊 每日市场复盘 | {now}

### 大盘概况
{market_summary}

### 自选股关注
{watchlist_str}

### 今日信号
{signals_str}

---
*🤖 小A | A股量化分析师*
"""
    
    return send_markdown(f"每日复盘 {now}", content)


if __name__ == "__main__":
    # 测试
    print("测试发送消息...")
    result = send_markdown(
        "小A 上线测试",
        "## ✅ 小A 已就绪\n\nA股量化交易专家已就位，等待指令。"
    )
    print(f"结果: {result}")
