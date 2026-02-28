"""

统一响应格式工具

"""

from fastapi import HTTPException

from typing import Any, Optional



def success(data: Any = None, message: str = "操作成功", code: int = 200):

    """成功响应"""

    return {

        "status": "success",

        "code": code,

        "message": message,

        "data": data

    }



def error(message: str = "操作失败", code: int = 400):

    """错误响应"""

    raise HTTPException(

        status_code=code,

        detail={

            "status": "error",

            "code": code,

            "message": message,

            "data": None

        }

    )



