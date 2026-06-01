# Task Management API

基于 **FastAPI** + **SQLAlchemy 2.0 (async)** + **SQLite** 构建的任务管理 RESTful API。

## 功能特性

- ✅ 任务的增删改查（CRUD）
- ✅ 任务状态管理：`todo` → `in_progress` → `done`
- ✅ 任务优先级：`low` / `medium` / `high`
- ✅ 分页查询，支持多字段排序
- ✅ 多条件筛选：状态、优先级、截止日期范围、创建日期范围
- ✅ 模糊搜索（标题 + 描述）
- ✅ 自动生成交互式 API 文档（Swagger UI）

## 技术栈

| 组件 | 技术 |
|------|------|
| Web 框架 | FastAPI |
| ASGI 服务器 | Uvicorn |
| ORM | SQLAlchemy 2.0 (async) |
| 数据库 | SQLite (aiosqlite) |
| 数据校验 | Pydantic v2 |

## 项目结构

```
fast_api/
├── task_api/
│   ├── __init__.py
│   ├── main.py          # FastAPI 应用入口
│   ├── database.py      # 数据库连接配置
│   ├── models.py        # SQLAlchemy 模型定义
│   ├── schemas.py       # Pydantic 请求/响应模型
│   ├── crud.py          # 数据库 CRUD 操作
│   ├── services.py      # 业务逻辑层
│   └── routers/
│       ├── __init__.py
│       └── tasks.py     # 任务相关路由
├── requirements.txt     # Python 依赖
└── README.md
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动服务

```bash
venv\Scripts\python.exe -m uvicorn task_api.main:app --reload --host 127.0.0.1 --port 8000
```

服务默认运行在 `http://127.0.0.1:8000`。

### 3. 查看 API 文档

启动后访问交互式文档：

- **Swagger UI**: http://127.0.0.1:8000/api/v1/docs

## API 接口一览

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/v1/tasks` | 创建任务 |
| `GET` | `/api/v1/tasks` | 查询任务列表（支持筛选/分页/排序） |
| `GET` | `/api/v1/tasks/{task_id}` | 获取单个任务 |
| `PUT` | `/api/v1/tasks/{task_id}` | 全量更新任务 |
| `PATCH` | `/api/v1/tasks/{task_id}` | 部分更新任务 |
| `DELETE` | `/api/v1/tasks/{task_id}` | 删除任务 |

### 查询参数（列表接口）

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
curl -X POST http://127.0.0.1:8000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "title": "完成项目文档",
    "description": "编写 README 和 API 文档",
    "status": "todo",
    "priority": "high",
    "due_date": "2025-12-31T23:59:59Z"
  }'
```

## License

MIT
