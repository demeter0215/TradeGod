#!/usr/bin/env python3
"""
TradeGod 交易推荐钉钉推送
发送交易信号到钉钉
"""

import requests
import json
import time
import hmac
import hashlib
import base64
from datetime import datetime
import os

# 钉钉配置（从环境变量或配置文件读取）
DINGTALK_WEBHOOK = "https://oapi.dingtalk.com/robot/send?access_token=d40168005a8f54cd44ee5b1286b57f6dd5a0cd6537eebe6603a3fe80339a2b0a"
DINGTALK_SECRET = "SEC51ccb38630ce6f1a160175eee23dda2c9bfd6dc5353d0761a232b077e0ef31df"

def generate_sign(secret, timestamp):
    """生成钉钉签名"""
    secret_enc = secret.encode('utf-8')
    string_to_sign = f'{timestamp}\n{secret}'
    string_to_sign_enc = string_to_sign.encode('utf-8')
    hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
    sign = base64.b64encode(hmac_code).decode('utf-8')
    return sign

def send_dingtalk_message(content, title="TradeGod交易信号", is_markdown=True):
    """
    发送钉钉消息
    
    Args:
        content: 消息内容
        title: 消息标题
        is_markdown: 是否使用markdown格式
    """
    timestamp = str(round(time.time() * 1000))
    sign = generate_sign(DINGTALK_SECRET, timestamp)
    
    url = f"{DINGTALK_WEBHOOK}&timestamp={timestamp}&sign={sign}"
    
    if is_markdown:
        data = {
            "msgtype": "markdown",
            "markdown": {
                "title": title,
                "text": content
            }
        }
    else:
        data = {
            "msgtype": "text",
            "text": {
                "content": content
            }
        }
    
    headers = {'Content-Type': 'application/json'}
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data), timeout=10)
        result = response.json()
        if result.get('errcode') == 0:
            print(f"✅ 钉钉消息发送成功: {title}")
            return True
        else:
            print(f"❌ 钉钉消息发送失败: {result}")
            return False
    except Exception as e:
        print(f"❌ 发送异常: {e}")
        return False

def send_trade_signal(symbol, action, price, target, stop_loss, reason="", timeframe="短线"):
    """
    发送交易信号到钉钉
    
    Args:
        symbol: 股票代码
        action: 操作 (做多/做空)
        price: 入场价格
        target: 目标价格
        stop_loss: 止损价格
        reason: 交易理由
        timeframe: 时间框架
    """
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    # 计算盈亏比
    try:
        price_f = float(price)
        target_f = float(target)
        stop_f = float(stop_loss)
        
        if action == "做多":
            profit = target_f - price_f
            loss = price_f - stop_f
            rr = profit / loss if loss != 0 else 0
        else:  # 做空
            profit = price_f - target_f
            loss = stop_f - price_f
            rr = profit / loss if loss != 0 else 0
    except:
        rr = 0
    
    emoji = "🟢" if action == "做多" else "🔴"
    
    content = f"""## {emoji} TradeGod 交易信号

**时间:** {now}  
**标的:** {symbol}  
**操作:** {action}  
**时间框架:** {timeframe}

---

**入场:** {price}  
**目标:** {target}  
**止损:** {stop_loss}  
**盈亏比:** 1:{rr:.1f}

---

**交易理由:**  
{reason}

---

⚠️ **风险提示:**  
- 严格止损，不扛单  
- 单笔仓位不超过20%  
- 盈利1%后设保本  

---
*免责声明：以上信号仅供参考，不构成投资建议*
"""
    
    return send_dingtalk_message(content, title=f"TradeGod {symbol} {action}信号")

def send_market_summary(market_data):
    """发送市场总结"""
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    content = f"""## 📊 TradeGod 市场总结

**时间:** {now}

{market_data}

---
*TradeGod AI量化分析系统*
"""
    
    return send_dingtalk_message(content, title="TradeGod市场总结")

def send_report_summary(report_type, content_summary):
    """发送报告摘要"""
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    emoji = "🌅" if "早间" in report_type else "🌙"
    
    content = f"""## {emoji} TradeGod {report_type}

**时间:** {now}

{content_summary}

---
📎 详细报告请查看聊天记录

---
*TradeGod AI量化分析系统*
"""
    
    return send_dingtalk_message(content, title=f"TradeGod {report_type}")


# 测试发送
if __name__ == "__main__":
    print("=" * 50)
    print("TradeGod 钉钉推送测试")
    print("=" * 50)
    
    # 测试交易信号
    print("\n1. 测试交易信号...")
    send_trade_signal(
        symbol="NVDA",
        action="做空",
        price="142.50",
        target="138.00",
        stop_loss="144.00",
        reason="盘前中国AI芯片竞争消息利空，开盘冲高无力，技术面出现长上影线",
        timeframe="短线(30-60分钟)"
    )
    
    # 测试市场总结
    print("\n2. 测试市场总结...")
    market_summary = """
**美股盘前动态:**
• 纳斯达克期货: +0.3%
• MAG7情绪: 偏谨慎
• VIX: 18.5 (+2%)

**今日关注:**
• 美联储官员讲话
• 英伟达盘前下跌2%
• 特斯拉欧洲销量下滑
"""
    send_market_summary(market_summary)
    
    print("\n✅ 测试完成")
