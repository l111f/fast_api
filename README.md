# Task Management API

> 基于 **FastAPI** + **SQLAlchemy 2.0 异步架构**的轻量级任务管理 RESTful API

## ✨ 功能特性

- ✅ 任务 CRUD 完整操作（创建、查询、更新、删除）
- ✅ 任务状态管理：`todo` → `in_progress` → `done`
- ✅ 任务优先级：`low` / `medium` / `high`
- ✅ 多条件过滤（状态、优先级、日期范围）
- ✅ 模糊搜索（标题和描述）
- ✅ 分页查询与多字段排序
- ✅ 自动生成 Swagger UI / ReDoc API 文档
- ✅ 95%+ 测试覆盖率（143 个测试用例）

## 🛠 技术栈

| 技术 | 说明 |
|------|------|
| **FastAPI** | 现代、快速的 Web 框架 |
| **SQLAlchemy 2.0** | 异步 ORM，支持异步数据库操作 |
| **SQLite + aiosqlite** | 轻量级异步数据库，无需额外安装 |
| **Pydantic v2** | 数据验证与序列化 |
| **Uvicorn** | 高性能 ASGI 服务器 |
| **pytest + httpx** | 测试框架与异步 HTTP 客户端 |

## 📁 项目结构

```
fast_api/
├── .env                        # 环境变量配置
├── .env.example                # 环境变量模板
├── .gitignore                  # Git 忽略规则
├── README.md                   # 项目说明文档
├── requirements.txt            # Python 依赖
├── run.bat                     # Windows 启动脚本
├── pytest.ini                  # pytest 配置
├── openspec/                   # 设计文档
│   ├── design.md
│   ├── proposal.md
│   ├── specs.md
│   └── tasks.md
├── task_api/                   # 主代码包
│   ├── __init__.py
│   ├── main.py                 # FastAPI 应用入口
│   ├── database.py             # 数据库连接配置
│   ├── models.py               # SQLAlchemy 模型定义
│   ├── schemas.py              # Pydantic 请求/响应模型
│   ├── crud.py                 # 数据库 CRUD 操作
│   ├── services.py             # 业务逻辑层
│   └── routers/
│       ├── __init__.py
│       └── tasks.py            # 任务相关路由
└── tests/                      # 测试代码
    ├── __init__.py
    ├── conftest.py             # 测试 fixtures 和依赖注入
    ├── test_api.py             # API 集成测试（55 个用例）
    ├── test_crud.py            # CRUD 层单元测试（24 个用例）
    ├── test_schemas.py         # Schema 验证测试（22 个用例）
    └── test_services.py        # Service 层单元测试（28 个用例）
```

## 🚀 快速开始

### 环境要求

- Python 3.10+
- pip 包管理器

### 安装与运行

**1. 克隆/下载项目**

```bash
git clone <repository-url>
cd fast_api
```

**2. 创建虚拟环境（推荐）**

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

**3. 安装依赖**

```bash
pip install -r requirements.txt
```

**4. 配置环境变量**

复制环境变量模板文件：

```bash
copy .env.example .env
```

默认配置即可直接运行，无需额外修改。

**5. 启动服务**

```bash
# 方式一：使用启动脚本（Windows）
run.bat

# 方式二：直接使用 uvicorn
python -m uvicorn task_api.main:app --reload --host 0.0.0.0 --port 8000

# 方式三：作为 Python 模块运行
python -m task_api.main
```

服务启动后访问 http://localhost:8000 即可。

## 📖 API 文档

服务启动后访问以下地址查看交互式 API 文档：

| 文档 | 地址 |
|------|------|
| **Swagger UI** | http://localhost:8000/api/v1/docs |
| **ReDoc** | http://localhost:8000/api/v1/redoc |

### API 端点概览

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/v1/tasks` | 创建任务 |
| `GET` | `/api/v1/tasks` | 查询任务列表（支持筛选/分页/排序） |
| `GET` | `/api/v1/tasks/{task_id}` | 获取单个任务 |
| `PUT` | `/api/v1/tasks/{task_id}` | 全量更新任务 |
| `PATCH` | `/api/v1/tasks/{task_id}` | 部分更新任务 |
| `DELETE` | `/api/v1/tasks/{task_id}` | 删除任务 |

### 查询参数说明（列表接口）

| 参数 | 类型 | 说明 |
|------|------|------|
| `status` | string | 按状态筛选，逗号分隔多值（如 `todo,in_progress`） |
| `priority` | string | 按优先级筛选，逗号分隔多值 |
| `due_date_from` | datetime | 截止日期起始 |
| `due_date_to` | datetime | 截止日期截止 |
| `created_at_from` | datetime | 创建日期起始 |
| `created_at_to` | datetime | 创建日期截止 |
| `search` | string | 模糊搜索标题和描述 |
| `page` | int | 页码（默认 1） |
| `page_size` | int | 每页条数（默认 20，最大 100） |
| `sort_by` | string | 排序字段（默认 `created_at`） |
| `sort_order` | string | 排序方向：`asc` / `desc`（默认 `desc`） |

### 创建任务示例

```bash
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "title": "完成项目文档",
    "description": "编写 README 和 API 文档",
    "status": "todo",
    "priority": "high",
    "due_date": "2025-12-31T23:59:59Z"
  }'
```

## 🧪 测试

项目使用 **pytest** + **pytest-asyncio** + **httpx** 进行测试，共 **143 个**测试用例，覆盖率 **95%+**。

### 运行所有测试

```bash
python -m pytest
```

### 运行特定测试文件

```bash
python -m pytest tests/test_api.py
```

### 带覆盖率报告

```bash
# 终端显示覆盖率
python -m pytest --cov=task_api --cov-report=term-missing

# 生成 HTML 覆盖率报告
python -m pytest --cov=task_api --cov-report=html
```

### 测试架构

| 层次 | 测试文件 | 类型 | 用例数 |
|------|----------|------|--------|
| Router（路由） | `test_api.py` | 集成测试 | 55 |
| Service（业务） | `test_services.py` | 单元测试 | 28 |
| CRUD（数据访问） | `test_crud.py` | 单元测试 | 24 |
| Schema（数据模型） | `test_schemas.py` | 单元测试 | 22 |

每个测试使用独立的 **SQLite 内存数据库**，测试结束后自动销毁，确保完全隔离。

## ⚙️ 环境变量配置

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `APP_NAME` | `Task Management API` | 应用名称，显示在 API 文档标题 |
| `APP_VERSION` | `1.0.0` | 应用版本号 |
| `DEBUG` | `True` | 调试模式（`true` / `false`） |
| `HOST` | `0.0.0.0` | 服务器监听地址 |
| `PORT` | `8000` | 服务器监听端口 |
| `DATABASE_URL` | `sqlite+aiosqlite:///./tasks.db` | 数据库连接 URL |

## 📄 许可证

MIT License
