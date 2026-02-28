"""
文档上传和管理API
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from datetime import datetime
from pathlib import Path
import hashlib
import secrets
# from bson import ObjectId  # MongoDB 专用，SQLite 不需要

from database import get_database
from utils.response import success, error
from utils.security import get_current_user

router = APIRouter(tags=["文档管理"])

# 文件上传配置
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB
ALLOWED_EXTENSIONS = {'.pdf', '.txt', '.html', '.docx', '.doc'}
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
CHUNK_SIZE = 1024 * 1024  # 1MB


def validate_file(file: UploadFile) -> bool:
    """验证上传文件"""
    # 检查文件扩展名
    if file.filename:
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail=f"不支持的文件类型: {file_ext}")
    
    return True


async def save_upload_file(file: UploadFile) -> dict:
    """保存上传文件"""
    database = get_database()
    if database is None:
        error("数据库未就绪，请稍后重试", code=503)
    
    # 生成文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    random_str = secrets.token_hex(8)
    file_ext = Path(file.filename).suffix.lower()
    filename = f"{timestamp}_{random_str}{file_ext}"
    
    # 保存文件
    file_path = UPLOAD_DIR / filename

    total_size = 0
    hasher = hashlib.sha256()
    try:
        with open(file_path, "wb") as f:
            while True:
                chunk = await file.read(CHUNK_SIZE)
                if not chunk:
                    break
                total_size += len(chunk)
                if total_size > MAX_FILE_SIZE:
                    try:
                        f.close()
                    except Exception:
                        pass
                    try:
                        if file_path.exists():
                            file_path.unlink()
                    except Exception:
                        pass
                    raise HTTPException(status_code=400, detail="文件大小超过限制（最大20MB）")
                hasher.update(chunk)
                f.write(chunk)
    except HTTPException:
        raise
    except Exception as e:
        try:
            if file_path.exists():
                file_path.unlink()
        except Exception:
            pass
        error(f"保存文件失败: {str(e)}", code=500)

    file_hash = hasher.hexdigest()
    
    # 保存元数据到数据库
    doc_meta = {
        "filename": file.filename,
        "saved_filename": filename,
        "file_path": str(file_path),
        "file_type": file.content_type,
        "file_size": total_size,
        "file_hash": file_hash,
        "uploaded_at": datetime.utcnow().isoformat(),
        "parse_status": "pending"
    }

    try:
        result = await database.documents.insert_one(doc_meta)
    except Exception as e:
        try:
            if file_path.exists():
                file_path.unlink()
        except Exception:
            pass
        error(f"保存文档元数据失败: {str(e)}", code=500)

    doc_meta["_id"] = str(result.inserted_id)
    
    return doc_meta


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """上传文档"""
    try:
        # 验证文件
        validate_file(file)
        
        # 保存文件
        doc_meta = await save_upload_file(file)
        
        # 添加用户信息
        doc_meta["uploaded_by"] = current_user["user_id"]
        
        return success(doc_meta, message="文件上传成功")
        
    except HTTPException:
        raise
    except Exception as e:
        error(f"文件上传失败: {str(e)}", code=500)


@router.post("/upload-test")
async def upload_document_test(file: UploadFile = File(...)):
    """测试文件上传（无需认证）"""
    try:
        # 验证文件
        validate_file(file)
        
        # 保存文件
        doc_meta = await save_upload_file(file)
        
        return success(doc_meta, message="文件上传成功")
        
    except HTTPException:
        raise
    except Exception as e:
        error(f"文件上传失败: {str(e)}", code=500)


@router.get("/{document_id}")
async def get_document(document_id: str):
    """获取文档信息"""
    try:
        database = get_database()
        if database is None:
            error("数据库未就绪，请稍后重试", code=503)

        try:
            doc_id = int(document_id)
        except Exception:
            error("无效的文档ID", code=400)

        doc = await database.documents.find_one({"_id": doc_id})
        
        if not doc:
            error("文档不存在", code=404)
        
        # 转换ID为字符串
        doc["_id"] = str(doc["_id"])
        
        return success(doc)
        
    except Exception as e:
        error(f"获取文档失败: {str(e)}", code=500)


@router.delete("/{document_id}")
async def delete_document(document_id: str):
    """删除文档"""
    try:
        database = get_database()
        if database is None:
            error("数据库未就绪，请稍后重试", code=503)

        try:
            doc_id = int(document_id)
        except Exception:
            error("无效的文档ID", code=400)

        doc = await database.documents.find_one({"_id": doc_id})
        
        if not doc:
            error("文档不存在", code=404)
        
        # 删除文件
        file_path = Path(doc.get("file_path", ""))
        if file_path.exists():
            file_path.unlink()
        
        # 删除数据库记录
        await database.documents.delete_one({"_id": doc_id})
        
        return success(None, message="文档删除成功")
        
    except Exception as e:
        error(f"删除文档失败: {str(e)}", code=500)
