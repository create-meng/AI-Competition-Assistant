"""
AI模型调用工具 - LLM封装
"""
import os
import json
import re
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from utils.crawler import Crawler
from utils.prompt_loader import load_prompt

load_dotenv()

# 模型配置
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-3.5-turbo")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

async def extract_from_html(url: str) -> Dict[str, Any]:
    """从HTML网页提取竞赛信息"""
    
    # 抓取网页
    crawler = Crawler()
    html_content = crawler.fetch(url)
    
    # 提取链接（基于规则）
    entrant_keywords = ["报名", "参赛", "注册", "提交作品", "entrance", "register", "student"]
    teacher_keywords = ["教师", "指导", "老师", "导师", "teacher", "mentor", "advisor"]
    
    entrant_links = crawler.extract_links(html_content, url, entrant_keywords)
    teacher_links = crawler.extract_links(html_content, url, teacher_keywords)
    
    # 提取文本
    text_content = crawler.extract_text(html_content)
    
    # 提取截止日期（简单正则）
    deadline = extract_deadline_from_text(text_content)
    
    # 构建结果
    extracted_data = {
        "entrant_url": entrant_links[0]["full_url"] if entrant_links else None,
        "teacher_url": teacher_links[0]["full_url"] if teacher_links else None,
        "deadline": deadline,
        "requirements": extract_requirements(text_content),
        "contact_info": extract_contact_info(text_content),
        "prize_info": None,
        "stages": []
    }
    
    # 评估置信度
    confidence = calculate_confidence(extracted_data)
    
    return {
        "extracted_data": extracted_data,
        "model": "rule_based",
        "prompt_id": "html_extraction_v1",
        "prompt_version": "v1",
        "raw_snippet": text_content[:500],
        "confidence": confidence
    }

async def extract_from_pdf(text_content: str) -> Dict[str, Any]:
    """从PDF文本提取竞赛信息"""
    
    # 提取信息（基于规则）
    extracted_data = {
        "entrant_url": extract_url_from_text(text_content, "participant"),
        "teacher_url": extract_url_from_text(text_content, "teacher"),
        "deadline": extract_deadline_from_text(text_content),
        "requirements": extract_requirements(text_content),
        "contact_info": extract_contact_info(text_content),
        "prize_info": extract_prize_info(text_content),
        "stages": []
    }
    
    # 评估置信度
    confidence = calculate_confidence(extracted_data)
    
    return {
        "extracted_data": extracted_data,
        "model": "rule_based",
        "prompt_id": "pdf_extraction_v1",
        "prompt_version": "v1",
        "raw_snippet": text_content[:500],
        "confidence": confidence
    }

def extract_deadline_from_text(text: str) -> Optional[str]:
    """从文本中提取截止日期"""
    # 日期模式：2025-10-06, 2025年10月6日
    patterns = [
        r'(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日]?)',
        r'截止[时日期]{0,2}[：:]\s*(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日]?)',
        r'报名[时日期]{0,2}[：:]\s*(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日]?)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            date_str = match.group(1)
            # 标准化格式
            date_str = date_str.replace('年', '-').replace('月', '-').replace('日', '')
            return date_str
    
    return None

def extract_url_from_text(text: str, context: str = "") -> Optional[str]:
    """从文本中提取URL"""
    # URL模式
    pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    matches = re.findall(pattern, text)
    
    if matches:
        return matches[0]
    
    return None

def extract_requirements(text: str) -> list:
    """提取参赛要求"""
    requirements = []
    
    # 查找包含"要求"、"条件"等关键词的段落
    keywords = ["参赛要求", "报名条件", "资格要求", "参赛对象"]
    
    for keyword in keywords:
        if keyword in text:
            # 简单提取：找到关键词后的几行
            idx = text.find(keyword)
            section = text[idx:idx+200]
            
            # 提取列表项
            lines = section.split('\n')
            for line in lines[1:4]:  # 取后面3行
                line = line.strip()
                if line and len(line) > 5:
                    requirements.append(line)
            
            break
    
    return requirements[:5]  # 最多返回5条

def extract_contact_info(text: str) -> Optional[str]:
    """提取联系方式"""
    # 邮箱模式
    email_pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
    email_match = re.search(email_pattern, text)
    
    # 电话模式
    phone_pattern = r'1[3-9]\d{9}|0\d{2,3}-?\d{7,8}'
    phone_match = re.search(phone_pattern, text)
    
    contact = []
    if email_match:
        contact.append(f"邮箱: {email_match.group()}")
    if phone_match:
        contact.append(f"电话: {phone_match.group()}")
    
    return " | ".join(contact) if contact else None

def extract_prize_info(text: str) -> Optional[str]:
    """提取奖项信息"""
    keywords = ["奖项", "奖金", "一等奖", "二等奖", "三等奖"]
    
    for keyword in keywords:
        if keyword in text:
            idx = text.find(keyword)
            section = text[max(0, idx-50):idx+150]
            return section.strip()
    
    return None

def calculate_confidence(extracted_data: Dict[str, Any]) -> float:
    """计算置信度"""
    score = 0.0
    total_fields = 0
    
    critical_fields = ['entrant_url', 'teacher_url', 'deadline']
    
    for field in critical_fields:
        total_fields += 1
        if extracted_data.get(field):
            score += 1.0
    
    # 其他字段加分
    if extracted_data.get('requirements'):
        score += 0.5
    if extracted_data.get('contact_info'):
        score += 0.3
    
    total_fields += 2
    
    confidence = score / total_fields if total_fields > 0 else 0.0
    return min(confidence, 1.0)

