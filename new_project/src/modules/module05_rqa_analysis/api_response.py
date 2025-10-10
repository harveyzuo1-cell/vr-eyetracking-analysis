"""
Module05: 统一API响应格式

提供标准化的API响应包装器，确保所有端点返回一致的响应格式
"""

from flask import jsonify, Response
from typing import Any, Dict, Optional, Tuple, Union


def success_response(
    data: Any = None,
    message: Optional[str] = None,
    status_code: int = 200
) -> Union[Response, Tuple[Response, int]]:
    """
    成功响应包装器

    Args:
        data: 响应数据（可以是dict、list等任何可JSON序列化的数据）
        message: 成功消息（可选）
        status_code: HTTP状态码，默认200

    Returns:
        Flask Response对象或(Response, status_code)元组

    Example:
        >>> success_response({'total': 100}, '查询成功')
        {
            "success": true,
            "data": {"total": 100},
            "message": "查询成功"
        }
    """
    response = {
        "success": True
    }

    if data is not None:
        response["data"] = data

    if message:
        response["message"] = message

    if status_code == 200:
        return jsonify(response)
    else:
        return jsonify(response), status_code


def error_response(
    error: Union[str, Exception],
    code: Optional[str] = None,
    status_code: int = 500,
    details: Optional[Dict] = None
) -> Tuple[Response, int]:
    """
    错误响应包装器

    Args:
        error: 错误信息或异常对象
        code: 错误代码（可选），如'INVALID_PARAMS'
        status_code: HTTP状态码，默认500
        details: 额外的错误详情（可选）

    Returns:
        (Response, status_code)元组

    Example:
        >>> error_response('参数无效', 'INVALID_PARAMS', 400)
        {
            "success": false,
            "error": "参数无效",
            "code": "INVALID_PARAMS"
        }
    """
    response = {
        "success": False,
        "error": str(error)
    }

    if code:
        response["code"] = code

    if details:
        response["details"] = details

    return jsonify(response), status_code


def paginated_response(
    items: list,
    page: int,
    page_size: int,
    total: int,
    message: Optional[str] = None
) -> Response:
    """
    分页响应包装器

    Args:
        items: 当前页的数据列表
        page: 当前页码（从1开始）
        page_size: 每页数量
        total: 总记录数
        message: 成功消息（可选）

    Returns:
        Flask Response对象

    Example:
        >>> paginated_response([...], 1, 20, 100, '查询成功')
        {
            "success": true,
            "data": {
                "items": [...],
                "pagination": {
                    "page": 1,
                    "page_size": 20,
                    "total": 100,
                    "total_pages": 5,
                    "has_next": true,
                    "has_prev": false
                }
            },
            "message": "查询成功"
        }
    """
    total_pages = (total + page_size - 1) // page_size

    data = {
        "items": items,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    }

    return success_response(data, message)


def progress_response(
    current: int,
    total: int,
    status: str = "processing",
    message: Optional[str] = None,
    eta: Optional[float] = None,
    details: Optional[Dict] = None
) -> Response:
    """
    进度响应包装器

    Args:
        current: 当前进度
        total: 总数
        status: 状态，如'processing', 'completed', 'failed'
        message: 消息
        eta: 预计剩余时间（秒）
        details: 额外详情

    Returns:
        Flask Response对象

    Example:
        >>> progress_response(50, 100, 'processing', '处理中...', 30.5)
        {
            "success": true,
            "data": {
                "progress": {
                    "current": 50,
                    "total": 100,
                    "percentage": 50.0,
                    "status": "processing"
                },
                "eta_seconds": 30.5
            },
            "message": "处理中..."
        }
    """
    percentage = (current / total * 100) if total > 0 else 0

    data = {
        "progress": {
            "current": current,
            "total": total,
            "percentage": round(percentage, 2),
            "status": status
        }
    }

    if eta is not None:
        data["eta_seconds"] = eta

    if details:
        data.update(details)

    return success_response(data, message)
