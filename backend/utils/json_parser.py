"""
JSON解析工具
用于处理AI返回的各种格式的JSON内容
"""
import json
import re
from typing import Optional, Dict, Any, Tuple


class JSONParser:
    """JSON解析器"""
    
    @staticmethod
    def extract_json_from_text(text: str) -> Tuple[Optional[Dict[str, Any]], str, str]:
        """
        从文本中提取JSON内容
        
        Args:
            text: 包含JSON的文本
            
        Returns:
            (parsed_json, error_message, raw_json_text)
        """
        if not text or not text.strip():
            return None, "文本为空", ""
        
        # 方法1: 尝试直接解析整个文本
        try:
            parsed = json.loads(text.strip())
            return parsed, "", text.strip()
        except json.JSONDecodeError:
            pass
        
        # 方法2: 提取markdown代码块中的JSON
        json_patterns = [
            r'```json\s*(\{.*?\})\s*```',  # ```json {...} ```
            r'```\s*(\{.*?\})\s*```',      # ``` {...} ```
            r'`(\{.*?\})`',                # `{...}`
        ]
        
        # 方法2.5: 处理AI思考过程格式
        think_patterns = [
            r'<think>.*?</think>\s*(\{.*?\})',  # <think>...</think> {...}
            r'<thinking>.*?</thinking>\s*(\{.*?\})',  # <thinking>...</thinking> {...}
            r'思考过程.*?(\{.*?\})',  # 思考过程... {...}
            r'分析.*?(\{.*?\})',  # 分析... {...}
        ]
        
        # 合并所有模式
        all_patterns = json_patterns + think_patterns
        
        for pattern in all_patterns:
            matches = re.findall(pattern, text, re.DOTALL)
            for match in matches:
                try:
                    parsed = json.loads(match.strip())
                    return parsed, "", match.strip()
                except json.JSONDecodeError:
                    continue
        
        # 方法3: 查找大括号包围的JSON对象
        brace_patterns = [
            r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}',  # 简单嵌套
            r'\{.*\}',  # 任意内容
        ]
        
        for pattern in brace_patterns:
            matches = re.findall(pattern, text, re.DOTALL)
            for match in matches:
                try:
                    parsed = json.loads(match.strip())
                    return parsed, "", match.strip()
                except json.JSONDecodeError:
                    continue
        
        # 方法4: 尝试从思考过程中提取JSON
        think_json = JSONParser._extract_json_from_thinking(text)
        if think_json:
            try:
                parsed = json.loads(think_json)
                return parsed, "", think_json
            except json.JSONDecodeError:
                pass
        
        # 方法5: 尝试修复常见的JSON问题
        fixed_json = JSONParser._fix_common_json_issues(text)
        if fixed_json:
            try:
                parsed = json.loads(fixed_json)
                return parsed, "", fixed_json
            except json.JSONDecodeError:
                pass
        
        # 方法6: 尝试提取部分JSON（如果被截断）
        partial_json = JSONParser._extract_partial_json(text)
        if partial_json:
            try:
                parsed = json.loads(partial_json)
                return parsed, "", partial_json
            except json.JSONDecodeError:
                pass
        
        # 所有方法都失败
        error_msg = f"无法从文本中提取有效的JSON格式。原始响应: {text[:200]}..."
        return None, error_msg, text[:500]
    
    @staticmethod
    def _extract_json_from_thinking(text: str) -> Optional[str]:
        """
        从AI思考过程中提取JSON
        处理类似 <think>...</think> 后面跟JSON的情况
        """
        if not text:
            return None
        
        # 查找思考过程后的JSON
        patterns = [
            # <think>...</think> 后面跟JSON
            r'<think>.*?</think>\s*(\{.*?\})',
            # <thinking>...</thinking> 后面跟JSON  
            r'<thinking>.*?</thinking>\s*(\{.*?\})',
            # 中文思考过程后面跟JSON
            r'(?:思考|分析|理解|处理).*?(\{.*?\})',
            # 任何文本后面跟JSON（作为最后手段）
            r'[^}]*?(\{.*?\})',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
            for match in matches:
                # 尝试找到完整的JSON对象
                json_candidate = match.strip()
                if json_candidate.startswith('{'):
                    # 尝试找到匹配的结束括号
                    brace_count = 0
                    end_pos = 0
                    for i, char in enumerate(json_candidate):
                        if char == '{':
                            brace_count += 1
                        elif char == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                end_pos = i + 1
                                break
                    
                    if brace_count == 0 and end_pos > 0:
                        return json_candidate[:end_pos]
        
        return None
    
    @staticmethod
    def _fix_common_json_issues(text: str) -> Optional[str]:
        """修复常见的JSON问题"""
        if not text:
            return None
        
        # 移除可能的前缀和后缀
        text = text.strip()
        
        # 查找JSON开始位置
        start_pos = text.find('{')
        if start_pos == -1:
            return None
        
        # 查找JSON结束位置（从后往前找）
        end_pos = text.rfind('}')
        if end_pos == -1 or end_pos <= start_pos:
            return None
        
        json_text = text[start_pos:end_pos + 1]
        
        # 修复常见问题
        fixes = [
            # 修复未闭合的字符串
            (r'"([^"]*?)\n', r'"\1"'),
            # 修复缺少逗号
            (r'"\s*\n\s*"', r'",\n"'),
            # 修复多余的逗号
            (r',\s*}', r'}'),
            (r',\s*]', r']'),
            # 修复单引号
            (r"'([^']*)'", r'"\1"'),
        ]
        
        for pattern, replacement in fixes:
            json_text = re.sub(pattern, replacement, json_text)
        
        return json_text
    
    @staticmethod
    def _extract_partial_json(text: str) -> Optional[str]:
        """尝试提取部分JSON（处理截断情况）"""
        if not text:
            return None
        
        # 查找第一个完整的JSON对象
        start_pos = text.find('{')
        if start_pos == -1:
            return None
        
        # 尝试找到匹配的结束括号
        brace_count = 0
        end_pos = start_pos
        
        for i, char in enumerate(text[start_pos:], start_pos):
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    end_pos = i
                    break
        
        if brace_count == 0:
            return text[start_pos:end_pos + 1]
        
        # 如果括号不匹配，尝试添加缺失的括号
        if brace_count > 0:
            # 添加缺失的右括号
            partial_json = text[start_pos:end_pos + 1]
            partial_json += '}' * brace_count
            return partial_json
        
        return None
    
    @staticmethod
    def validate_json_structure(data: Dict[str, Any], required_fields: list = None) -> Tuple[bool, str]:
        """
        验证JSON结构是否符合预期
        
        Args:
            data: 解析后的JSON数据
            required_fields: 必需字段列表
            
        Returns:
            (is_valid, error_message)
        """
        if not isinstance(data, dict):
            return False, "数据不是有效的JSON对象"
        
        if required_fields:
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                return False, f"缺少必需字段: {', '.join(missing_fields)}"
        
        return True, ""
    
    @staticmethod
    def format_json_error(error: json.JSONDecodeError, text: str) -> str:
        """
        格式化JSON解析错误信息
        
        Args:
            error: JSONDecodeError异常
            text: 原始文本
            
        Returns:
            格式化的错误信息
        """
        lines = text.split('\n')
        error_line = error.lineno - 1 if error.lineno > 0 else 0
        error_col = error.colno - 1 if error.colno > 0 else 0
        
        # 获取错误行及其上下文
        context_start = max(0, error_line - 2)
        context_end = min(len(lines), error_line + 3)
        context_lines = lines[context_start:context_end]
        
        error_info = f"JSON解析错误在第{error.lineno}行第{error.colno}列: {error.msg}\n\n"
        error_info += "上下文:\n"
        
        for i, line in enumerate(context_lines):
            line_num = context_start + i + 1
            if line_num == error.lineno:
                error_info += f"→ {line_num:3d}: {line}\n"
                error_info += f"    {' ' * error_col}^\n"
            else:
                error_info += f"  {line_num:3d}: {line}\n"
        
        return error_info


# 便捷函数
def extract_json_from_text(text: str) -> Tuple[Optional[Dict[str, Any]], str, str]:
    """从文本中提取JSON的便捷函数"""
    return JSONParser.extract_json_from_text(text)

def validate_json_structure(data: Dict[str, Any], required_fields: list = None) -> Tuple[bool, str]:
    """验证JSON结构的便捷函数"""
    return JSONParser.validate_json_structure(data, required_fields)
