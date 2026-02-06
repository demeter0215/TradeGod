#!/bin/bash
# TradeGod 交易信号钉钉推送快捷脚本
# 用法: ./send_signal.sh <股票代码> <做多/做空> <入场价> <目标价> <止损价> [理由]

SYMBOL=$1
ACTION=$2
PRICE=$3
TARGET=$4
STOP=$5
REASON=${6:-"技术面/消息面触发"}

cd /home/node/clawd
python3 -c "
import sys
sys.path.insert(0, '/home/node/clawd')
from dingtalk_notifier import send_trade_signal

send_trade_signal(
    symbol='$SYMBOL',
    action='$ACTION',
    price='$PRICE',
    target='$TARGET',
    stop_loss='$STOP',
    reason='$REASON',
    timeframe='短线'
)
"
