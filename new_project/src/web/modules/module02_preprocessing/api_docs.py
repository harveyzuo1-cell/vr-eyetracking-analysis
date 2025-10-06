"""
Module02 API文档 - Swagger/OpenAPI规范

提供完整的API文档，包括：
- 端点描述
- 请求/响应模型
- 参数说明
- 示例数据
"""

from flask import jsonify

# OpenAPI 3.0规范
MODULE02_API_SPEC = {
    "openapi": "3.0.0",
    "info": {
        "title": "Module02 数据预处理 API",
        "version": "2.0.0",
        "description": """
## 功能概述

Module02提供眼动数据预处理功能，包括：

### 核心功能
1. **受试者管理** - 创建、查询、更新、删除受试者信息
2. **MMSE数据管理** - 导入、验证、计算MMSE认知评分
3. **V2数据处理** - 扫描、导入V2格式眼动数据
4. **数据预处理** - 质量检测、数据清洗、平滑处理

### API端点分类
- `/subjects/*` - 受试者CRUD操作
- `/mmse/*` - MMSE数据管理
- `/preprocessing/*` - 数据预处理流程
- `/education-levels` - 基础数据接口

### 认证说明
当前版本无需认证，生产环境建议启用JWT认证。
        """,
        "contact": {
            "name": "API Support",
            "email": "support@example.com"
        }
    },
    "servers": [
        {
            "url": "http://localhost:9090/api/m02",
            "description": "开发服务器"
        },
        {
            "url": "http://localhost:9090/api/m02-new",
            "description": "新架构测试服务器"
        }
    ],
    "paths": {
        "/subjects": {
            "get": {
                "summary": "获取受试者列表",
                "description": "获取所有受试者的基本信息，支持按组别筛选",
                "tags": ["受试者管理"],
                "parameters": [
                    {
                        "name": "group",
                        "in": "query",
                        "description": "组别筛选",
                        "required": False,
                        "schema": {
                            "type": "string",
                            "enum": ["control", "mci", "ad"]
                        }
                    },
                    {
                        "name": "with_mmse",
                        "in": "query",
                        "description": "是否包含MMSE数据",
                        "required": False,
                        "schema": {
                            "type": "boolean",
                            "default": False
                        }
                    }
                ],
                "responses": {
                    "200": {
                        "description": "成功返回受试者列表",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "success": {"type": "boolean", "example": True},
                                        "count": {"type": "integer", "example": 86},
                                        "data": {
                                            "type": "array",
                                            "items": {"$ref": "#/components/schemas/Subject"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "post": {
                "summary": "创建受试者",
                "description": "创建新的受试者记录",
                "tags": ["受试者管理"],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/SubjectCreate"},
                            "example": {
                                "subject_id": "control_001",
                                "group": "control",
                                "demographics": {
                                    "gender": "male",
                                    "age": 65,
                                    "education_level": "undergraduate"
                                },
                                "mmse": {
                                    "q1_weekday": 1,
                                    "q1_month": 1,
                                    "total_score": 28
                                }
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "创建成功",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "success": {"type": "boolean"},
                                        "message": {"type": "string"},
                                        "data": {"$ref": "#/components/schemas/Subject"}
                                    }
                                }
                            }
                        }
                    },
                    "400": {
                        "description": "验证失败",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Error"}
                            }
                        }
                    }
                }
            }
        },
        "/subjects/{subject_id}": {
            "get": {
                "summary": "获取单个受试者",
                "description": "通过ID获取受试者详细信息",
                "tags": ["受试者管理"],
                "parameters": [
                    {
                        "name": "subject_id",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"},
                        "example": "control_001"
                    }
                ],
                "responses": {
                    "200": {
                        "description": "成功",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "success": {"type": "boolean"},
                                        "data": {"$ref": "#/components/schemas/Subject"}
                                    }
                                }
                            }
                        }
                    },
                    "404": {
                        "description": "受试者不存在"
                    }
                }
            },
            "put": {
                "summary": "更新受试者",
                "description": "更新受试者信息",
                "tags": ["受试者管理"],
                "parameters": [
                    {
                        "name": "subject_id",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"}
                    }
                ],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/SubjectUpdate"}
                        }
                    }
                },
                "responses": {
                    "200": {"description": "更新成功"},
                    "404": {"description": "受试者不存在"}
                }
            },
            "delete": {
                "summary": "删除受试者",
                "description": "删除指定受试者",
                "tags": ["受试者管理"],
                "parameters": [
                    {
                        "name": "subject_id",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"}
                    }
                ],
                "responses": {
                    "200": {"description": "删除成功"},
                    "404": {"description": "受试者不存在"}
                }
            }
        },
        "/subjects/statistics": {
            "get": {
                "summary": "获取统计信息",
                "description": "获取受试者的统计分析数据",
                "tags": ["受试者管理"],
                "responses": {
                    "200": {
                        "description": "成功",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Statistics"}
                            }
                        }
                    }
                }
            }
        },
        "/subjects/get-v2-subjects": {
            "get": {
                "summary": "获取V2受试者列表",
                "description": "从scan_result_v2.json获取V2格式受试者列表",
                "tags": ["V2数据管理"],
                "responses": {
                    "200": {
                        "description": "成功",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "success": {"type": "boolean"},
                                        "data": {
                                            "type": "object",
                                            "properties": {
                                                "subjects": {
                                                    "type": "array",
                                                    "items": {"$ref": "#/components/schemas/V2Subject"}
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "/subjects/import-v2-subjects": {
            "post": {
                "summary": "批量导入V2受试者",
                "description": "从V2数据批量导入受试者基础信息",
                "tags": ["V2数据管理"],
                "responses": {
                    "200": {
                        "description": "导入完成",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "success": {"type": "boolean"},
                                        "message": {"type": "string"},
                                        "data": {
                                            "type": "object",
                                            "properties": {
                                                "imported": {"type": "array", "items": {"type": "string"}},
                                                "skipped": {"type": "array"},
                                                "failed": {"type": "array"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "/mmse/clinical-data": {
            "get": {
                "summary": "获取临床MMSE数据",
                "description": "从clinical目录获取所有MMSE数据",
                "tags": ["MMSE管理"],
                "responses": {
                    "200": {
                        "description": "成功",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "success": {"type": "boolean"},
                                        "data": {"type": "object"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "/education-levels": {
            "get": {
                "summary": "获取教育程度选项",
                "description": "获取所有教育程度的枚举值和中文标签",
                "tags": ["基础数据"],
                "responses": {
                    "200": {
                        "description": "成功",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "success": {"type": "boolean"},
                                        "data": {
                                            "type": "object",
                                            "example": {
                                                "primary": "小学",
                                                "junior_high": "初中",
                                                "senior_high": "高中",
                                                "vocational": "中专/职高",
                                                "junior_college": "大专",
                                                "undergraduate": "本科",
                                                "postgraduate": "研究生及以上"
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "/preprocessing/config/default": {
            "get": {
                "summary": "获取默认预处理配置",
                "description": "获取数据预处理的默认参数配置",
                "tags": ["数据预处理"],
                "responses": {
                    "200": {
                        "description": "成功",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/PreprocessingConfig"}
                            }
                        }
                    }
                }
            }
        }
    },
    "components": {
        "schemas": {
            "Subject": {
                "type": "object",
                "properties": {
                    "subject_id": {"type": "string", "example": "control_001"},
                    "group": {"type": "string", "enum": ["control", "mci", "ad"]},
                    "demographics": {
                        "type": "object",
                        "properties": {
                            "gender": {"type": "string", "enum": ["male", "female"]},
                            "age": {"type": "integer", "minimum": 0, "maximum": 120},
                            "education_level": {
                                "type": "string",
                                "enum": ["primary", "junior_high", "senior_high", "vocational",
                                        "junior_college", "undergraduate", "postgraduate"]
                            }
                        }
                    },
                    "mmse": {
                        "type": "object",
                        "nullable": True,
                        "properties": {
                            "q1_weekday": {"type": "integer"},
                            "q1_month": {"type": "integer"},
                            "total_score": {"type": "integer", "minimum": 0, "maximum": 30}
                        }
                    },
                    "data_version": {"type": "string", "example": "v1"},
                    "task_count": {"type": "integer"},
                    "created_at": {"type": "string", "format": "date-time"},
                    "updated_at": {"type": "string", "format": "date-time"}
                }
            },
            "SubjectCreate": {
                "type": "object",
                "required": ["subject_id", "group", "demographics"],
                "properties": {
                    "subject_id": {"type": "string"},
                    "group": {"type": "string", "enum": ["control", "mci", "ad"]},
                    "demographics": {
                        "type": "object",
                        "required": ["gender", "age", "education_level"],
                        "properties": {
                            "gender": {"type": "string", "enum": ["male", "female"]},
                            "age": {"type": "integer"},
                            "education_level": {"type": "string"}
                        }
                    },
                    "mmse": {"type": "object", "nullable": True}
                }
            },
            "SubjectUpdate": {
                "type": "object",
                "properties": {
                    "demographics": {"type": "object"},
                    "mmse": {"type": "object"}
                }
            },
            "Statistics": {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "data": {
                        "type": "object",
                        "properties": {
                            "total_subjects": {"type": "integer"},
                            "by_group": {
                                "type": "object",
                                "properties": {
                                    "control": {"type": "integer"},
                                    "mci": {"type": "integer"},
                                    "ad": {"type": "integer"}
                                }
                            },
                            "by_gender": {
                                "type": "object",
                                "properties": {
                                    "male": {"type": "integer"},
                                    "female": {"type": "integer"}
                                }
                            },
                            "age_distribution": {"type": "object"},
                            "mmse_distribution": {"type": "object"}
                        }
                    }
                }
            },
            "V2Subject": {
                "type": "object",
                "properties": {
                    "subject_id": {"type": "string"},
                    "group": {"type": "string"},
                    "hospital_id": {"type": "string"},
                    "patient_name": {"type": "string", "nullable": True},
                    "timestamp": {"type": "string"},
                    "exists_in_system": {"type": "boolean"},
                    "has_mmse": {"type": "boolean"}
                }
            },
            "PreprocessingConfig": {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "data": {
                        "type": "object",
                        "properties": {
                            "quality_check": {"type": "object"},
                            "data_clean": {"type": "object"},
                            "data_smooth": {"type": "object"}
                        }
                    }
                }
            },
            "Error": {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean", "example": False},
                    "error": {"type": "string"},
                    "message": {"type": "string"}
                }
            }
        }
    },
    "tags": [
        {
            "name": "受试者管理",
            "description": "受试者CRUD操作和统计"
        },
        {
            "name": "V2数据管理",
            "description": "V2格式眼动数据导入和管理"
        },
        {
            "name": "MMSE管理",
            "description": "MMSE认知评分数据管理"
        },
        {
            "name": "数据预处理",
            "description": "数据质量检测、清洗和平滑"
        },
        {
            "name": "基础数据",
            "description": "枚举值和基础配置"
        }
    ]
}


def get_api_spec():
    """返回OpenAPI规范"""
    return jsonify(MODULE02_API_SPEC)
