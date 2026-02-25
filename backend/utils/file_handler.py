"""
文件上传处理工具
"""
import magic
import hashlib
import secrets
from pathlib import Path
from datetime import datetime
from fastapi import UploadFile, HTTPException
from typing import Optional

from database import get_database

# 允许的文件类型
ALLOWED_TYPES = {
    'application/pdf': '.pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
    'application/msword': '.doc',  # 旧版Word文档
    'text/plain': '.txt',
    'text/html': '.html'
}

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB

async def validate_upload_file(file: UploadFile):
    """验证上传文件"""
    # 读取文件内容
    content = await file.read()
    await file.seek(0)  # 重置文件指针
    
    # 检查文件大小
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="文件大小超过限制（最大20MB）")
    
    # 检查文件类型（magic number）
    try:
        mime_type = magic.from_buffer(content, mime=True)
    except:
        # 如果magic库不可用，使用文件扩展名判断
        ext = Path(file.filename).suffix.lower()
        if ext not in ['.pdf', '.docx', '.doc', '.txt', '.html']:
            raise HTTPException(status_code=400, detail="不支持的文件类型")
        return True
    
    if mime_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail=f"不支持的文件类型: {mime_type}")
    
    return True

async def save_upload_file(file: UploadFile, user_id: str, contest_id: Optional[str] = None) -> dict:
    """保存上传文件"""
    db = get_database()
    
    # 生成文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    random_str = secrets.token_hex(8)
    filename = f"{timestamp}_{random_str}_{file.filename}"
    
    # 保存文件
    upload_dir = Path("uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = upload_dir / filename
    
    content = await file.read()
    file_path.write_bytes(content)
    
    # 计算哈希
    file_hash = hashlib.sha256(content).hexdigest()
    
    # 保存元数据
    doc_meta = {
        "contest_id": contest_id,
        "filename": file.filename,
        "saved_filename": filename,
        "file_path": str(file_path),
        "file_type": file.content_type,
        "file_size": len(content),
        "file_hash": file_hash,
        "uploaded_by": user_id,
        "uploaded_at": datetime.utcnow(),
        "parse_status": "pending",
        "parsed_text": None,
        "parse_error": None
    }
    
    result = await db.documents.insert_one(doc_meta)
    doc_meta["id"] = str(result.inserted_id)
    doc_meta.pop("_id", None)
    
    return doc_meta

