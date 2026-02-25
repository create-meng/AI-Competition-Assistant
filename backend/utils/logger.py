"""
结构化日志模块
提供统一的日志记录功能
"""
import logging
import sys
import json
from datetime import datetime
from typing import Any, Dict, Optional
from pathlib import Path
import os


class JSONFormatter(logging.Formatter):
    """JSON 格式化器"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # 添加额外字段
        if hasattr(record, "extra_data"):
            log_data["data"] = record.extra_data
        
        # 添加异常信息
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, ensure_ascii=False, default=str)


class ColoredFormatter(logging.Formatter):
    """彩色控制台格式化器"""
    
    COLORS = {
        "DEBUG": "\033[36m",     # 青色
        "INFO": "\033[32m",      # 绿色
        "WARNING": "\033[33m",   # 黄色
        "ERROR": "\033[31m",     # 红色
        "CRITICAL": "\033[35m",  # 紫色
    }
    RESET = "\033[0m"
    
    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.RESET)
        
        # 时间戳
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 基础消息
        message = f"{color}[{timestamp}] [{record.levelname:8}]{self.RESET} "
        message += f"{record.name}: {record.getMessage()}"
        
        # 添加额外数据
        if hasattr(record, "extra_data") and record.extra_data:
            data_str = json.dumps(record.extra_data, ensure_ascii=False, default=str)
            message += f" | {data_str}"
        
        # 添加异常信息
        if record.exc_info:
            message += f"\n{self.formatException(record.exc_info)}"
        
        return message


class AppLogger:
    """应用日志器"""
    
    def __init__(self, name: str = "app"):
        self.logger = logging.getLogger(name)
        self._setup_done = False
    
    def setup(
        self,
        level: str = "INFO",
        log_file: Optional[str] = None,
        json_format: bool = False
    ):
        """配置日志器"""
        if self._setup_done:
            return
        
        self.logger.setLevel(getattr(logging, level.upper(), logging.INFO))
        
        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        
        if json_format:
            console_handler.setFormatter(JSONFormatter())
        else:
            console_handler.setFormatter(ColoredFormatter())
        
        self.logger.addHandler(console_handler)
        
        # 文件处理器
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(JSONFormatter())
            self.logger.addHandler(file_handler)
        
        self._setup_done = True
    
    def _log(self, level: int, message: str, data: Optional[Dict] = None, **kwargs):
        """内部日志方法"""
        extra = {"extra_data": data} if data else {}
        self.logger.log(level, message, extra=extra, **kwargs)
    
    def debug(self, message: str, data: Optional[Dict] = None):
        """调试日志"""
        self._log(logging.DEBUG, message, data)
    
    def info(self, message: str, data: Optional[Dict] = None):
        """信息日志"""
        self._log(logging.INFO, message, data)
    
    def warning(self, message: str, data: Optional[Dict] = None):
        """警告日志"""
        self._log(logging.WARNING, message, data)
    
    def error(self, message: str, data: Optional[Dict] = None, exc_info: bool = False):
        """错误日志"""
        self._log(logging.ERROR, message, data, exc_info=exc_info)
    
    def critical(self, message: str, data: Optional[Dict] = None, exc_info: bool = False):
        """严重错误日志"""
        self._log(logging.CRITICAL, message, data, exc_info=exc_info)
    
    # 业务日志方法
    def api_request(self, method: str, path: str, client_ip: str, user_id: Optional[str] = None):
        """API 请求日志"""
        self.info("API请求", {
            "type": "api_request",
            "method": method,
            "path": path,
            "client_ip": client_ip,
            "user_id": user_id
        })
    
    def api_response(self, method: str, path: str, status_code: int, duration_ms: float):
        """API 响应日志"""
        level = logging.INFO if status_code < 400 else logging.WARNING
        self._log(level, "API响应", {
            "type": "api_response",
            "method": method,
            "path": path,
            "status_code": status_code,
            "duration_ms": round(duration_ms, 2)
        })
    
    def ai_extraction(
        self,
        provider: str,
        model: str,
        source_type: str,
        success: bool,
        duration_ms: float,
        confidence: Optional[float] = None,
        error: Optional[str] = None
    ):
        """AI 提取日志"""
        level = logging.INFO if success else logging.WARNING
        self._log(level, "AI提取", {
            "type": "ai_extraction",
            "provider": provider,
            "model": model,
            "source_type": source_type,
            "success": success,
            "duration_ms": round(duration_ms, 2),
            "confidence": confidence,
            "error": error
        })
    
    def auth_event(self, event: str, username: str, success: bool, client_ip: str, reason: Optional[str] = None):
        """认证事件日志"""
        level = logging.INFO if success else logging.WARNING
        self._log(level, f"认证事件: {event}", {
            "type": "auth_event",
            "event": event,
            "username": username,
            "success": success,
            "client_ip": client_ip,
            "reason": reason
        })
    
    def rate_limit_hit(self, client_ip: str, rule: str, path: str):
        """速率限制触发日志"""
        self.warning("速率限制触发", {
            "type": "rate_limit",
            "client_ip": client_ip,
            "rule": rule,
            "path": path
        })
    
    def cache_event(self, event: str, key: str, hit: bool = False):
        """缓存事件日志"""
        self.debug("缓存事件", {
            "type": "cache_event",
            "event": event,
            "key": key[:50] + "..." if len(key) > 50 else key,
            "hit": hit
        })
    
    def db_query(self, collection: str, operation: str, duration_ms: float, count: Optional[int] = None):
        """数据库查询日志"""
        self.debug("数据库查询", {
            "type": "db_query",
            "collection": collection,
            "operation": operation,
            "duration_ms": round(duration_ms, 2),
            "count": count
        })


# 全局日志实例
logger = AppLogger("ai_competition")


def setup_logging():
    """初始化日志系统"""
    log_level = os.getenv("LOG_LEVEL", "INFO")
    log_file = os.getenv("LOG_FILE")
    json_format = os.getenv("LOG_JSON", "false").lower() == "true"
    
    logger.setup(
        level=log_level,
        log_file=log_file,
        json_format=json_format
    )
    
    logger.info("日志系统初始化完成", {
        "level": log_level,
        "file": log_file,
        "json_format": json_format
    })


# 导出
__all__ = ["logger", "setup_logging", "AppLogger"]
