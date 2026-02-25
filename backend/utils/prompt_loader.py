"""
Prompt模板加载工具
"""
from pathlib import Path
from typing import Optional

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"

def load_prompt(prompt_file: str) -> str:
    """加载prompt模板"""
    prompt_path = PROMPTS_DIR / prompt_file
    
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt文件不存在: {prompt_file}")
    
    return prompt_path.read_text(encoding='utf-8')

def get_latest_prompt_version(prompt_name: str) -> str:
    """获取最新版本的prompt"""
    versions = list(PROMPTS_DIR.glob(f"{prompt_name}_v*.txt"))
    
    if not versions:
        raise FileNotFoundError(f"未找到prompt: {prompt_name}")
    
    # 按版本号排序，返回最新版
    latest = sorted(versions, key=lambda p: p.stem.split('_v')[-1])[-1]
    return latest.name

def replace_placeholders(prompt: str, **kwargs) -> str:
    """替换prompt中的占位符"""
    for key, value in kwargs.items():
        placeholder = f"<<{key.upper()}>>"
        prompt = prompt.replace(placeholder, str(value))
    
    return prompt

