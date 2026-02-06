#!/usr/bin/env python3
"""
财经新闻抓取器 - TradeGod专用
稳定源：新浪财经(中文A股实时)
备用源：Bloomberg(英文)、CoinDesk(加密)
"""

import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List, Dict

class FinanceNewsFetcher:
    """财经新闻抓取器"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
    
    # ==================== 中文A股（主力）====================
    
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
    
    # ==================== 英文/加密（备用）====================
    
    def get_bloomberg(self, limit: int = 5) -> List[Dict]:
        """Bloomberg Markets - 需翻墙"""
        url = "https://feeds.bloomberg.com/markets/news.rss"
        
        try:
            resp = self.session.get(url, timeout=8)
            root = ET.fromstring(resp.content)
            results = []
            
            for item in root.findall('.//item')[:limit]:
                title = item.find('title').text or ''
                link = item.find('link').text or ''
                pub = item.find('pubDate').text or ''
                
                results.append({
                    'title': title.replace('<![CDATA[', '').replace(']]>', ''),
                    'summary': '',
                    'url': link,
                    'time': pub[:17] if pub else '',
                    'source': 'Bloomberg',
                    'type': 'global'
                })
            return results
        except Exception as e:
            return []
    
    def get_coindesk(self, limit: int = 5) -> List[Dict]:
        """CoinDesk - 加密货币"""
        url = "https://www.coindesk.com/arc/outboundfeeds/rss/"
        
        try:
            resp = self.session.get(url, timeout=8)
            root = ET.fromstring(resp.content)
            results = []
            
            for item in root.findall('.//item')[:limit]:
                title = item.find('title').text or ''
                link = item.find('link').text or ''
                pub = item.find('pubDate').text or ''
                desc = item.find('description').text or ''
                
                results.append({
                    'title': title,
                    'summary': desc[:100] if desc else '',
                    'url': link,
                    'time': pub[:17] if pub else '',
                    'source': 'CoinDesk',
                    'type': 'crypto'
                })
            return results
        except Exception as e:
            return []
    
    # ==================== 统一接口 ====================
    
    def fetch_a_stock(self, limit: int = 20) -> List[Dict]:
        """
        只抓取A股新闻（最常用）
        """
        finance = self.get_sina_finance(limit)
        stock = self.get_sina_stock(limit // 2)
        return finance + stock
    
    def fetch_all(self, include_global: bool = False) -> Dict:
        """
        抓取全部新闻
        include_global: 是否包含英文源（较慢）
        """
        a_stock = self.fetch_a_stock(15)
        
        result = {
            'a_stock': a_stock,
            'fetch_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }
        
        if include_global:
            result['global'] = self.get_bloomberg(5)
            result['crypto'] = self.get_coindesk(5)
        
        return result
    
    def search(self, keyword: str, news_list: List[Dict] = None) -> List[Dict]:
        """
        关键词搜索
        """
        if news_list is None:
            news_list = self.fetch_a_stock(30)
        
        keyword_lower = keyword.lower()
        results = []
        
        for news in news_list:
            text = (news.get('title', '') + news.get('summary', '')).lower()
            if keyword_lower in text:
                results.append(news)
        
        return results
    
    def filter_by_time(self, news_list: List[Dict], hours: int = 1) -> List[Dict]:
        """
        筛选最近N小时的新闻
        """
        now = datetime.now()
        results = []
        
        for news in news_list:
            try:
                news_time = datetime.strptime(news.get('full_time', ''), '%Y-%m-%d %H:%M:%S')
                if (now - news_time) <= timedelta(hours=hours):
                    results.append(news)
            except:
                # 如果解析失败，默认保留
                results.append(news)
        
        return results


# ==================== 直接运行测试 ====================

if __name__ == "__main__":
    fetcher = FinanceNewsFetcher()
    
    print("=" * 60)
    print("A股实时新闻抓取测试")
    print("=" * 60)
    
    # 只抓A股（最快）
    news = fetcher.fetch_a_stock(15)
    
    print(f"\n✅ 抓取到 {len(news)} 条新闻\n")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    print("-" * 60)
    print("最新10条:")
    print("-" * 60)
    
    for i, n in enumerate(news[:10], 1):
        print(f"\n{i}. [{n['time']}] [{n['source']}]")
        print(f"   {n['title']}")
        if n['summary']:
            print(f"   {n['summary'][:80]}...")
    
    # 关键词搜索示例
    print("\n" + "=" * 60)
    print("搜索 '港股':")
    print("=" * 60)
    
    search_results = fetcher.search('港股', news)
    for r in search_results[:5]:
        print(f"- {r['title'][:50]}... [{r['source']}] [{r['time']}]")
    
    print("\n" + "=" * 60)
    print(f"脚本路径: /home/node/clawd/finance_news.py")
    print("=" * 60)
