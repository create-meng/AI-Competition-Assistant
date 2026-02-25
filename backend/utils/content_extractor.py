"""
内容提取工具
用于从文件和URL中提取内容
支持多种提取策略处理不同类型的网页
"""
import httpx
from bs4 import BeautifulSoup
from pathlib import Path
from typing import Optional, Dict, Any
import re
import asyncio
from urllib.parse import urljoin
import os

# 导入文件解析器
from .file_parser import file_parser


class ContentExtractor:
    """内容提取器"""
    
    @staticmethod
    async def extract_from_url(url: str) -> dict:
        """
        从URL提取内容（使用多种策略）
        
        Args:
            url: 网页URL
            
        Returns:
            {
                "success": bool,
                "content": str,
                "url": str,
                "title": str (可选),
                "method": str (可选, "http" 或 "api"),
                "error": str (可选)
            }
        """
        # 策略1: 尝试直接HTTP请求
        try:
            result = await ContentExtractor._extract_from_url_http(url)
            if result["success"]:
                return result
        except Exception as e:
            print(f"⚠️ HTTP提取失败: {str(e)}")
        
        # 策略2: 尝试使用API服务（如果有的话）
        try:
            result = await ContentExtractor._extract_from_url_api(url)
            if result["success"]:
                return result
        except Exception as e:
            print(f"⚠️ API提取失败: {str(e)}")
        
        # 策略3: 返回基础信息
        return {
            "success": False,
            "content": "",
            "url": url,
            "error": "所有提取策略都失败了"
        }
    
    @staticmethod
    def _is_spa_page(html_content: str) -> bool:
        """
        检测是否为单页应用(SPA)页面
        
        Args:
            html_content: HTML内容
            
        Returns:
            bool: 是否为SPA页面
        """
        if not html_content:
            return False
        
        # 转换为小写进行检测
        content_lower = html_content.lower()
        
        # SPA页面特征
        spa_indicators = [
            # 1. 包含JavaScript框架
            'react', 'vue', 'angular', 'svelte',
            # 2. 包含SPA相关的JavaScript
            'single page application', 'spa',
            # 3. 包含路由相关代码
            'router', 'routing', 'history.pushstate',
            # 4. 包含状态管理
            'redux', 'vuex', 'mobx', 'zustand',
            # 5. 包含构建工具标识
            'webpack', 'vite', 'rollup', 'parcel',
            # 6. 包含现代前端框架标识
            'next.js', 'nuxt.js', 'gatsby',
            # 7. 页面内容很少但包含大量JavaScript
            len(html_content) < 1000 and 'script' in content_lower and content_lower.count('script') > 5,
            # 8. 包含"JavaScript enabled"提示
            'javascript enabled' in content_lower,
            # 9. 包含noscript标签提示
            'noscript' in content_lower and 'enable javascript' in content_lower,
            # 10. 包含动态内容加载标识
            'loading', 'spinner', 'skeleton'
        ]
        
        # 检查是否满足SPA特征
        spa_score = sum(1 for indicator in spa_indicators if indicator)
        
        # 如果满足3个或以上特征，认为是SPA页面
        return spa_score >= 3
    
    @staticmethod
    async def _extract_from_url_http(url: str) -> dict:
        """
        使用HTTP方式从URL提取内容（私有方法）
        
        Args:
            url: 网页URL
            
        Returns:
            提取结果字典
        """
        try:
            headers = {
                'User-Agent': 'AICompetitionAssistantBot/1.0 (+mailto:contact@example.com)',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                
                # 解析HTML
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 提取标题
                title = ""
                if soup.title:
                    title = soup.title.get_text().strip()
                elif soup.find('h1'):
                    title = soup.find('h1').get_text().strip()
                
                # 提取主要内容
                content = ContentExtractor._extract_main_content(soup)
                
                return {
                    "success": True,
                    "content": content,
                    "url": str(response.url),
                    "title": title,
                    "method": "http"
                }
                
        except Exception as e:
            return {
                "success": False,
                "content": "",
                "url": url,
                "error": f"HTTP提取失败: {str(e)}"
            }
    
    @staticmethod
    async def _extract_from_url_api(url: str) -> dict:
        """
        使用API服务从URL提取内容（私有方法）
        这里可以集成第三方API服务，如ScrapingBee、ScraperAPI等
        
        Args:
            url: 网页URL
            
        Returns:
            提取结果字典
        """
        # 目前返回失败，可以后续集成第三方API
        return {
            "success": False,
            "content": "",
            "url": url,
            "error": "API服务暂未配置"
        }
    
    @staticmethod
    def _extract_main_content(soup: BeautifulSoup) -> str:
        """
        从BeautifulSoup对象中提取主要内容
        
        Args:
            soup: BeautifulSoup对象
            
        Returns:
            提取的文本内容
        """
        # 移除脚本和样式标签
        for script in soup(["script", "style", "nav", "footer", "header", "aside"]):
            script.decompose()
        
        # 尝试找到主要内容区域
        main_content = None
        
        # 常见的正文容器标签
        content_selectors = [
            'main', 'article', '.content', '.main-content', 
            '.post-content', '.entry-content', '.article-content',
            '#content', '#main', '.container', '.wrapper'
        ]
        
        for selector in content_selectors:
            if selector.startswith('.'):
                main_content = soup.find(class_=selector[1:])
            elif selector.startswith('#'):
                main_content = soup.find(id=selector[1:])
            else:
                main_content = soup.find(selector)
            
            if main_content:
                break
        
        # 如果没有找到特定的内容区域，使用body
        if not main_content:
            main_content = soup.find('body') or soup
        
        # 提取文本
        text = main_content.get_text(separator='\n', strip=True)
        
        # 清理文本
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        cleaned_text = '\n'.join(lines)
        
        return cleaned_text
    
    @staticmethod
    async def extract_from_url_deep(url: str) -> dict:
        """
        深度提取URL内容（保持向后兼容）
        
        Args:
            url: 网页URL
            
        Returns:
            提取结果字典
        """
        # 直接调用新的提取方法
        result = await ContentExtractor.extract_from_url(url)
        
        # 如果是SPA页面，尝试提取更多信息
        if result["success"] and ContentExtractor._is_spa_page(result["content"]):
            print(f"⚠️ 检测到SPA页面，内容可能不完整: {url}")
            # 可以在这里添加额外的处理逻辑
        
        return result
    
    @staticmethod
    async def extract_from_file(file_path: str) -> dict:
        """
        从文件提取内容
        
        Args:
            file_path: 文件路径
            
        Returns:
            提取结果字典
        """
        try:
            path = Path(file_path)
            if not path.exists():
                return {
                    "success": False,
                    "content": "",
                    "file_path": file_path,
                    "error": "文件不存在"
                }
            
            # 使用文件解析器
            parse_result = file_parser.parse_file(str(path))
            if not parse_result.get("success", False):
                raise Exception(parse_result.get("error", "文件解析失败"))
            content = parse_result.get("content", "")
            
            return {
                "success": True,
                "content": content,
                "file_path": file_path,
                "method": "file_parser"
            }
            
        except Exception as e:
            return {
                "success": False,
                "content": "",
                "file_path": file_path,
                "error": f"文件提取失败: {str(e)}"
            }
    
    @staticmethod
    def extract_urls_from_content(content: str, base_url: str = None) -> Dict[str, str]:
        """
        从内容中提取URL链接
        
        Args:
            content: 文本内容
            base_url: 基础URL（用于相对链接转换）
            
        Returns:
            包含entrant_url和teacher_url的字典
        """
        if not content:
            return {"entrant_url": None, "teacher_url": None}
        
        # 参赛者入口关键词
        entrant_keywords = [
            '报名', '参赛', '注册', '提交作品', 'entrance', 'register', 
            'submit', 'student', 'participant', 'entry'
        ]
        
        # 教师入口关键词
        teacher_keywords = [
            '教师', '指导老师', '导师', 'teacher', 'mentor', 'advisor',
            'instructor', 'supervisor'
        ]
        
        # 查找链接
        entrant_url = ContentExtractor._find_url_by_keywords(content, entrant_keywords, base_url)
        teacher_url = ContentExtractor._find_url_by_keywords(content, teacher_keywords, base_url)
        
        return {
            "entrant_url": entrant_url,
            "teacher_url": teacher_url
        }
    
    @staticmethod
    def _find_url_by_keywords(content: str, keywords: list, base_url: str = None) -> Optional[str]:
        """
        根据关键词查找URL
        
        Args:
            content: 文本内容
            keywords: 关键词列表
            base_url: 基础URL
            
        Returns:
            找到的URL或None
        """
        # 简单的URL匹配正则
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        urls = re.findall(url_pattern, content, re.IGNORECASE)
        
        for url in urls:
            # 检查URL周围的文本是否包含关键词
            url_lower = url.lower()
            for keyword in keywords:
                if keyword.lower() in url_lower:
                    return url
        
        # 如果没有找到完整URL，尝试查找相对链接
        if base_url:
            relative_pattern = r'href=["\']([^"\']+)["\']'
            relative_links = re.findall(relative_pattern, content, re.IGNORECASE)
            
            for link in relative_links:
                if any(keyword.lower() in link.lower() for keyword in keywords):
                    full_url = urljoin(base_url, link)
                    return full_url
        
        return None