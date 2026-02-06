#!/usr/bin/env python3
"""
TradeGod 统一新闻抓取器
整合：新浪财经(A股) + Tavily(全球深度搜索)

配置：将 API Key 写入 /home/node/clawd/.env
    TAVILY_API_KEY=your_key_here
"""

import requests
import xml.etree.ElementTree as ET
import os
from datetime import datetime
from typing import List, Dict, Optional

# 加载环境变量
ENV_FILE = '/home/node/clawd/.env'
if os.path.exists(ENV_FILE):
    with open(ENV_FILE) as f:
        for line in f:
            if line.strip() and not line.startswith('#') and '=' in line:
                key, value = line.strip().split('=', 1)
                os.environ[key] = value


class TradeGodNews:
    """TradeGod 统一新闻接口"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        self.tavily_key = os.getenv('TAVILY_API_KEY')
    
    # ==================== A股新闻 (RSS) ====================
    
    def get_sina_finance(self, limit: int = 20) -> List[Dict]:
        """新浪财经-财经新闻 - 最稳定实时"""
        url = "https://feed.mix.sina.com.cn/api/roll/get"
        params = {"pageid": "153", "lid": "2516", "num": limit, "page": "1", "encode": "utf-8"}
        
        try:
            resp = self.session.get(url, params=params, timeout=10)
            data = resp.json()
            results = []
            for item in data.get('result', {}).get('data', []):
                ctime = int(item.get('ctime', 0))
                dt = datetime.fromtimestamp(ctime) if ctime else datetime.now()
                results.append({
                    'title': item.get('title', ''),
                    'summary': item.get('intro', '')[:150],
                    'url': item.get('wapurl', ''),
                    'time': dt.strftime('%m-%d %H:%M'),
                    'full_time': dt.strftime('%Y-%m-%d %H:%M:%S'),
                    'source': '新浪财经',
                    'type': 'a_stock'
                })
            return results
        except Exception as e:
            print(f"[错误] 新浪财经: {e}")
            return []
    
    def get_sina_stock(self, limit: int = 10) -> List[Dict]:
        """新浪财经-股票新闻"""
        url = "https://feed.mix.sina.com.cn/api/roll/get"
        params = {"pageid": "153", "lid": "2517", "num": limit, "page": "1", "encode": "utf-8"}
        
        try:
            resp = self.session.get(url, params=params, timeout=10)
            data = resp.json()
            results = []
            for item in data.get('result', {}).get('data', []):
                ctime = int(item.get('ctime', 0))
                dt = datetime.fromtimestamp(ctime) if ctime else datetime.now()
                results.append({
                    'title': item.get('title', ''),
                    'summary': item.get('intro', '')[:150],
                    'url': item.get('wapurl', ''),
                    'time': dt.strftime('%m-%d %H:%M'),
                    'full_time': dt.strftime('%Y-%m-%d %H:%M:%S'),
                    'source': '新浪股票',
                    'type': 'a_stock'
                })
            return results
        except Exception as e:
            print(f"[错误] 新浪股票: {e}")
            return []
    
    def fetch_a_stock(self, limit: int = 20) -> List[Dict]:
        """获取A股综合新闻"""
        finance = self.get_sina_finance(limit)
        stock = self.get_sina_stock(limit // 2)
        return finance + stock
    
    # ==================== 全球深度搜索 (Tavily) ====================
    
    def search_tavily(self, query: str, max_results: int = 10, 
                      include_answer: bool = True,
                      search_depth: str = "basic") -> Dict:
        """
        Tavily AI搜索 - 全球深度搜索
        
        Args:
            query: 搜索关键词
            max_results: 最大结果数 (默认10)
            include_answer: 是否包含AI总结
            search_depth: basic(快) / advanced(深)
        """
        if not self.tavily_key:
            return {"error": "TAVILY_API_KEY not configured", "results": []}
        
        url = "https://api.tavily.com/search"
        headers = {"Authorization": f"Bearer {self.tavily_key}"}
        data = {
            "query": query,
            "search_depth": search_depth,
            "max_results": max_results,
            "include_answer": include_answer
        }
        
        try:
            resp = self.session.post(url, json=data, headers=headers, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"error": str(e), "results": []}
    
    def search_us_market(self, query: str = None) -> Dict:
        """美股市场搜索 (给小纳用)"""
        if query is None:
            query = "US stock market today Federal Reserve interest rate"
        return self.search_tavily(query, max_results=10, search_depth="advanced")
    
    def search_crypto(self, query: str = None) -> Dict:
        """加密货币搜索 (给小聪用)"""
        if query is None:
            query = "Bitcoin Ethereum crypto market today"
        return self.search_tavily(query, max_results=10, search_depth="advanced")
    
    def search_company(self, company: str, market: str = "US") -> Dict:
        """个股深度搜索"""
        if market == "US":
            query = f"{company} stock analysis news today 2025"
        elif market == "HK":
            query = f"{company} 港股 分析"
        else:
            query = f"{company} A股 分析"
        
        return self.search_tavily(query, max_results=10, search_depth="advanced")
    
    # ==================== 统一搜索接口 ====================
    
    def search(self, keyword: str, sources: List[str] = None) -> Dict:
        """
        统一搜索接口
        
        Args:
            keyword: 搜索关键词
            sources: ['a_stock'] 或 ['global'] 或 ['a_stock', 'global']
        """
        if sources is None:
            sources = ['a_stock', 'global']
        
        result = {
            'keyword': keyword,
            'search_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'a_stock': [],
            'global': {}
        }
        
        # A股搜索 (RSS)
        if 'a_stock' in sources:
            a_news = self.fetch_a_stock(30)
            keyword_lower = keyword.lower()
            result['a_stock'] = [
                n for n in a_news 
                if keyword_lower in (n['title'] + n['summary']).lower()
            ][:10]
        
        # 全球搜索 (Tavily)
        if 'global' in sources and self.tavily_key:
            result['global'] = self.search_tavily(
                keyword, 
                max_results=10, 
                search_depth="advanced"
            )
        
        return result
    
    # ==================== 行业/板块监控 ====================
    
    def monitor_sectors(self, sectors: List[str] = None) -> Dict:
        """
        监控重点行业新闻
        """
        if sectors is None:
            sectors = ['新能源', '半导体', '银行', '房地产', '医药']
        
        a_news = self.fetch_a_stock(50)
        result = {}
        
        for sector in sectors:
            sector_lower = sector.lower()
            matched = [
                n for n in a_news 
                if sector_lower in (n['title'] + n['summary']).lower()
            ][:5]
            if matched:
                result[sector] = matched
        
        return result
    
    def get_market_summary(self) -> Dict:
        """
        获取市场综合摘要
        """
        # A股快讯
        a_news = self.fetch_a_stock(15)
        
        # 全球概要
        global_summary = {}
        if self.tavily_key:
            global_summary = self.search_tavily(
                "global stock market summary today Asia US Europe",
                max_results=5,
                include_answer=True,
                search_depth="basic"
            )
        
        return {
            'a_stock_news': a_news[:10],
            'global_summary': global_summary.get('answer', ''),
            'fetch_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }


# ==================== 测试运行 ====================

if __name__ == "__main__":
    print("=" * 60)
    print("TradeGod 新闻抓取器测试")
    print("=" * 60)
    
    news = TradeGodNews()
    
    # 1. 测试A股新闻
    print("\n📈 测试 A股新闻 (新浪财经)...")
    a_news = news.fetch_a_stock(10)
    print(f"✅ 抓取到 {len(a_news)} 条")
    for n in a_news[:3]:
        print(f"   [{n['time']}] {n['title'][:40]}...")
    
    # 2. 测试Tavily美股
    if news.tavily_key:
        print("\n🌍 测试 Tavily 美股搜索...")
        us_result = news.search_us_market()
        if 'error' not in us_result:
            print(f"✅ 查询: {us_result.get('query', 'N/A')}")
            answer = us_result.get('answer', '')
            if answer:
                print(f"   AI总结: {answer[:100]}...")
            print(f"   结果数: {len(us_result.get('results', []))}")
        else:
            print(f"❌ 错误: {us_result['error']}")
    else:
        print("\n⚠️ Tavily Key 未配置")
    
    # 3. 测试统一搜索
    print("\n🔍 测试 统一搜索 '港股'...")
    search_result = news.search('港股', sources=['a_stock', 'global'])
    print(f"   A股结果: {len(search_result['a_stock'])} 条")
    if search_result.get('global') and 'results' in search_result['global']:
        print(f"   全球结果: {len(search_result['global']['results'])} 条")
    
    # 4. 测试行业监控
    print("\n📊 测试 行业监控...")
    sectors = news.monitor_sectors(['新能源', '半导体'])
    for sector, items in sectors.items():
        print(f"   [{sector}] {len(items)} 条新闻")
    
    print("\n" + "=" * 60)
    print("✅ 测试完成！")
    print("=" * 60)
