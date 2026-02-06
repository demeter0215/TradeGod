#!/usr/bin/env python3
"""
寒武纪(688256) 2025年年报预告分析
基于2026年1月31日发布的最新业绩预告
"""

import sys
sys.path.insert(0, '/home/node/clawd')
from earnings_fetcher import FinancialReportFetcher
from datetime import datetime

def analyze_cambricon_realtime():
    """
    基于实时数据生成寒武纪分析报告
    """
    fetcher = FinancialReportFetcher()
    
    print("=" * 70)
    print("🎯 寒武纪(688256) 2025年报预告分析")
    print("数据来源: 东方财富 / 新浪财经")
    print("=" * 70)
    
    # 获取实时数据
    print("\n📊 正在获取实时财报数据...")
    data = fetcher.search_stock_financial('688256')
    
    # 业绩预告信息
    forecast = data.get('forecast', {})
    fin = data.get('financial', {})
    
    print("\n" + "=" * 70)
    print("🔮 2025年年报预告（2026-01-31发布）")
    print("=" * 70)
    
    if forecast.get('found'):
        print(f"预告类型: 🟢 {forecast['type']} ✅")
        print(f"公告日期: {forecast['date']}")
        if forecast.get('summary'):
            print(f"\n预告摘要:\n{forecast['summary']}")
        
        # 分析解读
        print("\n" + "-" * 70)
        print("💡 预告解读:")
        print("-" * 70)
        
        if forecast['type'] in ['预增', '略增', '扭亏']:
            print("""
✅ 积极信号:
• 2025年全年业绩向好，AI芯片业务可能迎来突破
• 可能是大客户订单落地（互联网厂商/运营商）
• 产品迭代见效，出货量提升

⚠️ 需关注细节:
• 预增幅度多少？（50%以上才算超预期）
• 是否扭亏为盈？（还是仅亏损收窄）
• 扣非净利润如何？（排除政府补贴影响）
""")
        else:
            print("⚠️ 业绩承压，需关注改善进度")
    
    # 历史财务对比
    print("\n" + "=" * 70)
    print("📈 历史财务表现")
    print("=" * 70)
    
    if 'indicators' in fin:
        ind = fin['indicators']
        print(f"最新报告期: {ind.get('报告期', 'N/A')}")
        print(f"营业收入: {ind.get('营业收入', 'N/A')} 亿元")
        print(f"净利润: {ind.get('净利润', 'N/A')} 亿元")
        print(f"ROE: {ind.get('ROE', 'N/A')} %")
        print(f"毛利率: {ind.get('毛利率', 'N/A')} %")
    
    print("""
📊 关键观察:
• 寒武纪作为AI芯片龙头，2025年受益于AI算力需求爆发
• 2024年营收已呈现高速增长态势
• 2025年预增预示业务拐点可能到来
• 但需区分：是营收增长还是盈亏平衡？
""")
    
    # 投资策略
    print("\n" + "=" * 70)
    print("💰 投资策略建议")
    print("=" * 70)
    
    if forecast.get('type') == '预增':
        print("""
🟢 乐观情景:
• 预增+扭亏: 业绩拐点确认，可逢低布局
• 大客户订单持续：关注互联网大厂、运营商招标
• 新产品放量：思元590等高端芯片出货

🟡 谨慎情景:
• 仅增收未扭亏: 仍处高投入期，需控制仓位
• 依赖单一大客户: 客户集中风险
• 估值偏高: PE仍为负，按PS估值较贵

📌 操作建议:
1. 等年报全文披露，看扣非净利润和现金流
2. 关注Q1订单情况，判断增长持续性
3. 技术面：如突破前高可跟进，否则震荡观望
4. 仓位：建议 <3%，作为AI主题卫星配置
""")
    
    # 风险提示
    print("\n" + "=" * 70)
    print("⚠️ 风险提示")
    print("=" * 70)
    print("""
• 竞争加剧：英伟达H20入华、华为昇腾、海光等竞争
• 技术迭代：AI芯片技术更新快，需持续高研发投入
• 地缘政治：美国出口管制可能影响供应链
• 客户集中：大B端客户占比高，议价能力受限
• 估值泡沫：当前市值可能已反映乐观预期
""")
    
    print("\n" + "=" * 70)
    print("📅 下一步关注")
    print("=" * 70)
    print("""
1. 2025年报全文披露（预计2026年3-4月）
2. 2026年一季报预告（2026年4月）
3. 大模型厂商芯片采购公告
4. 新产品发布会（思元系列迭代）
5. 美国出口管制政策变化
""")
    
    print("\n" + "=" * 70)
    print("免责声明：本分析仅供参考，不构成投资建议")
    print("=" * 70)


if __name__ == "__main__":
    analyze_cambricon_realtime()
