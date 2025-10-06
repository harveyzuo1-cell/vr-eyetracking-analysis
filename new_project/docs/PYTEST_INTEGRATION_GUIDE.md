# Pytest测试框架集成指南
# Pytest Integration Guide

**文档版本**: 1.0.0
**创建时间**: 2025-10-03
**状态**: 实施规范

---

## 📋 目录

1. [集成目标](#1-集成目标)
2. [Pytest配置](#2-pytest配置)
3. [测试目录结构](#3-测试目录结构)
4. [测试编写规范](#4-测试编写规范)
5. [Fixtures设计](#5-fixtures设计)
6. [测试执行](#6-测试执行)
7. [CI/CD集成](#7-cicd集成)

---

## 1. 集成目标

### 1.1 为什么选择Pytest

- ✅ **简洁语法**: 使用assert而非unittest的assertEqual
- ✅ **强大的fixtures**: 依赖注入,自动资源管理
- ✅ **插件生态**: pytest-cov, pytest-mock, pytest-flask等
- ✅ **详细报告**: 清晰的错误信息和测试报告
- ✅ **参数化测试**: 轻松进行数据驱动测试

### 1.2 测试目标

| 测试类型 | 覆盖率目标 | 优先级 |
|---------|-----------|--------|
| 单元测试 | 80%+ | 高 |
| 集成测试 | 60%+ | 中 |
| API测试 | 90%+ | 高 |
| 端到端测试 | 50%+ | 低 |

---

## 2. Pytest配置

### 2.1 安装依赖

创建 `requirements-test.txt`:

```txt
# 核心测试框架
pytest==7.4.3
pytest-cov==4.1.0
pytest-mock==3.12.0
pytest-flask==1.3.0

# 测试辅助工具
pytest-xdist==3.5.0          # 并行测试
pytest-timeout==2.2.0        # 超时控制
pytest-html==4.1.1           # HTML报告

# 代码质量
pytest-flake8==1.1.1
pytest-pylint==0.21.0

# 覆盖率工具
coverage==7.3.4
