"""
网页爬虫工具
"""
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
from time import sleep
from typing import Optional
from urllib.parse import urljoin
import re


class Crawler:
    """网页爬虫，支持连接池复用和自动重试"""
    
    def __init__(self, delay: float = 1.0):
        self.delay = delay
        self.headers = {
            'User-Agent': 'AICompetitionAssistantBot/1.0 (+mailto:contact@example.com)'
        }
        # 创建带连接池的Session
        self.session = requests.Session()
        
        # 配置重试策略
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,
            pool_maxsize=10
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
    
    def __del__(self):
        """清理Session资源"""
        if hasattr(self, 'session'):
            self.session.close()
    
    def fetch(self, url: str, max_retries: int = 3) -> str:
        """抓取网页内容"""
        try:
            response = self.session.get(
                url,
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            sleep(self.delay)
            return response.text
        except Exception as e:
            raise Exception(f"抓取失败: {str(e)}")
    
    def parse_html(self, html_content: str) -> BeautifulSoup:
        """解析HTML内容"""
        return BeautifulSoup(html_content, 'lxml')
    
    def extract_links(self, html_content: str, base_url: str, keywords: list) -> list:
        """提取包含特定关键词的链接"""
        soup = self.parse_html(html_content)
        links = []
        
        for a in soup.find_all('a', href=True):
            text = a.get_text().strip().lower()
            href = a['href']
            
            # 检查链接文本是否包含关键词
            if any(keyword.lower() in text for keyword in keywords):
                full_url = urljoin(base_url, href)
                links.append({
                    'text': a.get_text().strip(),
                    'href': href,
                    'full_url': full_url
                })
        
        return links
    
    def extract_text(self, html_content: str) -> str:
        """提取网页文本内容"""
        soup = self.parse_html(html_content)
        
        # 移除script和style标签
        for script in soup(["script", "style"]):
            script.decompose()
        
        # 获取文本
        text = soup.get_text()
        
        # 清理文本
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        return text

