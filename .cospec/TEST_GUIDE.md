# Task Management API — 测试指导文档

## 文档信息

| 项目 | 内容 |
|------|------|
| 项目名称 | Task Management API |
| 框架 | FastAPI + SQLAlchemy 2.0 (Async) + SQLite |
| 测试框架 | pytest + pytest-asyncio + httpx |
| 测试覆盖率 | **95%** |
| 测试数量 | **143 个**（全部通过） |
| 最后更新 | 2026-06-24 |

---

## 1. 概述

本文档为该 FastAPI 任务管理 API 项目的完整测试方案。项目采用四层分层架构（Router → Service → CRUD → Database），测试覆盖所有层级和所有 6 个 RESTful API 端点。

### 测试目标

- 验证所有 API 端点的正确性（正常流程 + 异常处理）
- 验证数据模型和 Pydantic Schema 的校验逻辑
- 验证业务层参数校验和错误处理
- 验证数据库 CRUD 操作的正确性
- 验证分页、过滤、排序、搜索等复杂查询功能
- 达到 90%+ 的代码覆盖率

---

## 2. 测试架构

```
tests/
├── __init__.py          # 空文件，标记 Python 包
├── conftest.py          # 共享 fixtures：内存数据库、HTTP 客户端、测试数据
├── test_api.py          # API 集成测试（55 个用例）
├── test_crud.py         # CRUD 层单元测试（24 个用例）
├── test_services.py     # Service 层单元测试（28 个用例）
└── test_schemas.py      # Schema 验证测试（22 个用例）
```

### 测试层次说明

| 层次 | 测试文件 | 类型 | 说明 |
|------|----------|------|------|
| Router（路由） | `test_api.py` | 集成测试 | 通过 httpx 异步客户端模拟完整 HTTP 请求 |
| Service（业务） | `test_services.py` | 单元测试 | 直接调用服务函数，注入数据库会话 |
| CRUD（数据访问） | `test_crud.py` | 单元测试 | 直接调用 crud 函数，注入数据库会话 |
| Schema（数据模型） | `test_schemas.py` | 单元测试 | 纯逻辑测试，不依赖数据库 |

---

## 3. 环境搭建

### 3.1 安装依赖

```bash
# 安装所有依赖（包括测试依赖）
pip install -r requirements.txt

# 或手动安装
pip install fastapi uvicorn[standard] sqlalchemy>=2.0 aiosqlite pydantic>=2.0
pip install pytest pytest-asyncio httpx pytest-cov
```

### 3.2 运行测试

```bash
# 运行所有测试
python -m pytest

# 运行特定文件
python -m pytest tests/test_api.py

# 运行特定测试类
python -m pytest tests/test_api.py::TestCreateTask

# 运行特定测试方法
python -m pytest tests/test_api.py::TestCreateTask::test_create_task_all_fields

# 显示详细输出
python -m pytest -v

# 带覆盖率报告
python -m pytest --cov=task_api --cov-report=term-missing

# 生成 HTML 覆盖率报告
python -m pytest --cov=task_api --cov-report=html
```

### 3.3 测试配置

[`pytest.ini`](pytest.ini) 配置：

```ini
[pytest]
asyncio_mode = auto           # 自动检测异步测试函数
testpaths = tests             # 测试目录
python_files = test_*.py      # 测试文件匹配模式
python_classes = Test*        # 测试类匹配模式
python_functions = test_*     # 测试函数匹配模式
addopts = -v --tb=short       # 详细输出 + 简短回溯
```

---

## 4. 测试数据策略

### 4.1 数据库隔离

每个测试函数使用独立的 **SQLite 内存数据库**（`sqlite+aiosqlite://`），测试结束后自动销毁，确保测试完全隔离。

### 4.2 核心 Fixtures

| Fixture | 作用域 | 说明 |
|---------|--------|------|
| `test_engine` | function | 创建/销毁内存 SQLite 引擎，自动建表和删表 |
| `db_session` | function | 提供直连数据库会话，用于 CRUD/Service 测试 |
| `client` | function | 提供 httpx 异步 HTTP 客户端，自动替换 DB 依赖 |
| `sample_task` | function | 创建一个示例任务，用于获取/更新/删除测试 |
| `multiple_tasks` | function | 创建 5 个不同状态/优先级的任务，用于列表查询测试 |

### 4.3 依赖注入覆盖

[`conftest.py`](tests/conftest.py) 中通过 `app.dependency_overrides` 机制将生产环境的数据库会话替换为测试内存数据库：

```python
app.dependency_overrides[get_db_session] = override_get_db_session
```

---

## 5. 测试用例清单

### 5.1 API 端点到端测试（55 个用例）

#### POST /api/v1/tasks — 创建任务（10 个用例）

| # | 测试用例 | 预期 | 说明 |
|---|----------|------|------|
| 1 | `test_create_task_all_fields` | 201 | 提供 title, description, status, priority, due_date |
| 2 | `test_create_task_minimal` | 201 | 仅提供必填字段 title |
| 3 | `test_create_task_default_values` | 201 | 验证 status 默认为 todo，priority 默认为 medium |
| 4 | `test_create_task_empty_title` | 422 | 空字符串标题 |
| 5 | `test_create_task_title_too_long` | 422 | title > 200 字符 |
| 6 | `test_create_task_description_too_long` | 422 | description > 2000 字符 |
| 7 | `test_create_task_invalid_status` | 422 | 非法 status 枚举值 |
| 8 | `test_create_task_invalid_priority` | 422 | 非法 priority 枚举值 |
| 9 | `test_create_task_missing_body` | 422 | 不发送请求体 |
| 10 | `test_create_task_response_has_timestamps` | 201 | 响应包含 id, created_at, updated_at |

#### GET /api/v1/tasks/{task_id} — 获取单个任务（3 个用例）

| # | 测试用例 | 预期 | 说明 |
|---|----------|------|------|
| 11 | `test_get_task_success` | 200 | 获取已存在的任务 |
| 12 | `test_get_task_not_found` | 404 | 获取不存在的任务（ID=99999） |
| 13 | `test_get_task_returns_all_fields` | 200 | 响应包含所有 8 个字段 |

#### PUT /api/v1/tasks/{task_id} — 全量更新（6 个用例）

| # | 测试用例 | 预期 | 说明 |
|---|----------|------|------|
| 14 | `test_update_task_full` | 200 | 更新所有字段 |
| 15 | `test_update_task_not_found` | 404 | 更新不存在的任务 |
| 16 | `test_update_task_invalid_status` | 422 | 更新时使用非法 status |
| 17 | `test_update_task_empty_title` | 422 | 更新时使用空标题 |
| 18 | `test_update_task_updated_at_refreshes` | 200 | updated_at 自动刷新 |
| 19 | `test_update_task_created_at_immutable` | 200 | created_at 不可变 |

#### PATCH /api/v1/tasks/{task_id} — 部分更新（5 个用例）

| # | 测试用例 | 预期 | 说明 |
|---|----------|------|------|
| 20 | `test_update_task_single_field` | 200 | 仅更新 title，其他字段不变 |
| 21 | `test_update_task_status_only` | 200 | 仅更新 status |
| 22 | `test_update_task_not_found` | 404 | 部分更新不存在的任务 |
| 23 | `test_update_task_empty_body` | 200 | 空 {} 请求体，返回当前状态 |
| 24 | `test_update_task_invalid_data` | 422 | 非法字段值 |

#### DELETE /api/v1/tasks/{task_id} — 删除任务（5 个用例）

| # | 测试用例 | 预期 | 说明 |
|---|----------|------|------|
| 25 | `test_delete_task_success` | 204 | 删除成功，无响应体 |
| 26 | `test_delete_task_not_found` | 404 | 删除不存在的任务 |
| 27 | `test_delete_task_twice` | 204→404 | 重复删除 |
| 28 | `test_delete_task_then_get` | 204→404 | 删除后再查询 |
| 29 | `test_delete_task_response_body_empty` | 204 | 验证响应体为空 |

#### GET /api/v1/tasks — 获取任务列表（26 个用例）

| # | 测试用例 | 预期 | 说明 |
|---|----------|------|------|
| 30 | `test_list_tasks_empty` | 200 | 空数据库，验证响应结构 |
| 31 | `test_list_tasks_with_data` | 200 | 5 条数据，默认分页 |
| 32 | `test_list_tasks_filter_by_status` | 200 | 按单个 status 筛选 |
| 33 | `test_list_tasks_filter_by_multiple_status` | 200 | status=todo,done 多值筛选 |
| 34 | `test_list_tasks_filter_by_priority` | 200 | 按单个 priority 筛选 |
| 35 | `test_list_tasks_filter_by_multiple_priority` | 200 | priority=high,low 多值筛选 |
| 36 | `test_list_tasks_search_in_title` | 200 | 模糊搜索标题 |
| 37 | `test_list_tasks_search_in_description` | 200 | 模糊搜索描述 |
| 38 | `test_list_tasks_search_case_insensitive` | 200 | 搜索不区分大小写 |
| 39 | `test_list_tasks_pagination_page1` | 200 | page=1, page_size=2 |
| 40 | `test_list_tasks_pagination_page2` | 200 | page=2, page_size=2 |
| 41 | `test_list_tasks_pagination_last_page` | 200 | 最后一页不满 |
| 42 | `test_list_tasks_pagination_beyond_range` | 200 | 超出范围返回空列表 |
| 43 | `test_list_tasks_sort_by_title_asc` | 200 | 按 title 升序 |
| 44 | `test_list_tasks_sort_by_title_desc` | 200 | 按 title 降序 |
| 45 | `test_list_tasks_sort_by_status` | 200 | 按 status 排序 |
| 46 | `test_list_tasks_default_sort_created_at_desc` | 200 | 默认按 created_at 降序 |
| 47 | `test_list_tasks_invalid_page_zero` | 422 | page=0 |
| 48 | `test_list_tasks_invalid_page_negative` | 422 | page=-1 |
| 49 | `test_list_tasks_invalid_page_size_zero` | 422 | page_size=0 |
| 50 | `test_list_tasks_invalid_page_size_too_large` | 422 | page_size=101 |
| 51 | `test_list_tasks_invalid_sort_by` | 422 | sort_by=不存在字段 |
| 52 | `test_list_tasks_combined_filters` | 200 | status + priority 组合筛选 |
| 53 | `test_list_tasks_filter_no_match` | 200 | 筛选无匹配结果 |
| 54 | `test_list_tasks_response_structure` | 200 | 验证 items 和 pagination 结构 |
| 55 | `test_list_tasks_date_filter` | 200 | 按 due_date 范围筛选 |

### 5.2 CRUD 层测试（24 个用例）

#### create_task（3 个用例）

| # | 测试用例 | 说明 |
|---|----------|------|
| 1 | `test_create_task_success` | 创建任务，验证所有字段 |
| 2 | `test_create_task_with_all_fields` | 包含所有可选字段 |
| 3 | `test_create_multiple_tasks` | 创建多个任务 |

#### get_task（3 个用例）

| # | 测试用例 | 说明 |
|---|----------|------|
| 4 | `test_get_task_found` | 查询存在任务 |
| 5 | `test_get_task_not_found` | 查询不存在任务 |
| 6 | `test_get_task_returns_all_fields` | 验证返回全部字段 |

#### update_task（4 个用例）

| # | 测试用例 | 说明 |
|---|----------|------|
| 7 | `test_update_task_success` | 更新成功 |
| 8 | `test_update_task_refreshes_updated_at` | updated_at 刷新 |
| 9 | `test_update_task_multiple_fields` | 同时更新多个字段 |
| 10 | `test_update_task_preserves_created_at` | created_at 不变 |

#### delete_task（2 个用例）

| # | 测试用例 | 说明 |
|---|----------|------|
| 11 | `test_delete_task_success` | 删除成功 |
| 12 | `test_delete_task_only_target` | 只删除目标，不影响其他 |

#### list_tasks（12 个用例）

| # | 测试用例 | 说明 |
|---|----------|------|
| 13 | `test_list_tasks_empty` | 空列表 |
| 14 | `test_list_tasks_default_pagination` | 默认分页 |
| 15 | `test_list_tasks_filter_status` | 按状态筛选 |
| 16 | `test_list_tasks_filter_multiple_status` | 多状态筛选 |
| 17 | `test_list_tasks_filter_priority` | 按优先级筛选 |
| 18 | `test_list_tasks_search_title` | 搜索标题 |
| 19 | `test_list_tasks_search_description` | 搜索描述 |
| 20 | `test_list_tasks_search_case_insensitive` | 不区分大小写 |
| 21 | `test_list_tasks_pagination` | 分页 |
| 22 | `test_list_tasks_pagination_page2` | 第2页 |
| 23 | `test_list_tasks_sort_by_title_asc` | 升序排序 |
| 24 | `test_list_tasks_sort_by_title_desc` | 降序排序 |
| 25 | `test_list_tasks_default_sort_desc` | 默认降序 |
| 26 | `test_list_tasks_date_range_filter` | 日期范围筛选 |
| 27 | `test_list_tasks_created_at_range_filter` | 创建时间范围筛选 |
| 28 | `test_list_tasks_sort_by_priority` | 按优先级排序 |
| 29 | `test_list_tasks_invalid_sort_field_defaults` | 非法排序字段回退 |
| 30 | `test_list_tasks_combined_filters` | 组合筛选 |

### 5.3 Service 层测试（28 个用例）

#### create_task_service（2 个用例）

| # | 测试用例 | 说明 |
|---|----------|------|
| 1 | `test_create_success` | 创建成功 |
| 2 | `test_create_with_all_fields` | 所有字段 |

#### get_task_service（2 个用例）

| # | 测试用例 | 说明 |
|---|----------|------|
| 3 | `test_get_success` | 获取成功 |
| 4 | `test_get_not_found_raises_404` | 获取不存在 → 404 |

#### update_task_service（4 个用例）

| # | 测试用例 | 说明 |
|---|----------|------|
| 5 | `test_update_success` | 更新成功 |
| 6 | `test_update_not_found_raises_404` | 更新不存在 → 404 |
| 7 | `test_update_empty_body_returns_current` | 空更新体 |
| 8 | `test_update_partial_status_only` | 部分更新 status |

#### delete_task_service（2 个用例）

| # | 测试用例 | 说明 |
|---|----------|------|
| 9 | `test_delete_success` | 删除成功 |
| 10 | `test_delete_not_found_raises_404` | 删除不存在 → 404 |

#### ListTasksQueryParams（5 个用例）

| # | 测试用例 | 说明 |
|---|----------|------|
| 11 | `test_default_values` | 默认参数值 |
| 12 | `test_status_split_by_comma` | 逗号分隔状态 |
| 13 | `test_priority_split_by_comma` | 逗号分隔优先级 |
| 14 | `test_single_status_no_comma` | 单值状态 |
| 15 | `test_none_status_stays_none` | 空状态为 None |

#### list_tasks_service — 校验（8 个用例）

| # | 测试用例 | 说明 |
|---|----------|------|
| 16 | `test_page_less_than_1_raises_422` | page < 1 |
| 17 | `test_page_negative_raises_422` | page 负数 |
| 18 | `test_page_size_zero_raises_422` | page_size = 0 |
| 19 | `test_page_size_over_100_raises_422` | page_size > 100 |
| 20 | `test_page_size_negative_raises_422` | page_size 负数 |
| 21 | `test_invalid_sort_by_raises_422` | 非法排序字段 |
| 22 | `test_page_size_100_is_valid` | 边界值 100 |
| 23 | `test_page_size_1_is_valid` | 边界值 1 |

#### list_tasks_service — 正常（6 个用例）

| # | 测试用例 | 说明 |
|---|----------|------|
| 24 | `test_empty_result` | 空结果 |
| 25 | `test_with_data` | 有数据 |
| 26 | `test_pagination_calculation` | 分页计算 |
| 27 | `test_filter_by_status` | 状态筛选 |
| 28 | `test_search` | 搜索 |

#### ALLOWED_SORT_FIELDS（2 个用例）

| # | 测试用例 | 说明 |
|---|----------|------|
| 29 | `test_contains_all_expected_fields` | 包含所有可用排序字段 |
| 30 | `test_is_frozen_set` | 验证类型 |

### 5.4 Schema 验证测试（22 个用例）

#### 枚举类（5 个用例）

| # | 测试用例 | 说明 |
|---|----------|------|
| 1 | `TaskStatus::test_valid_values` | 合法状态值 |
| 2 | `TaskStatus::test_invalid_value` | 非法状态值 |
| 3 | `TaskStatus::test_is_string` | 继承 str |
| 4 | `TaskPriority::test_valid_values` | 合法优先级值 |
| 5 | `TaskPriority::test_invalid_value` | 非法优先级值 |

#### TaskCreate（9 个用例）

| # | 测试用例 | 说明 |
|---|----------|------|
| 6 | `test_valid_minimal` | 仅 title |
| 7 | `test_valid_all_fields` | 所有字段 |
| 8 | `test_title_empty_raises` | 空标题校验失败 |
| 9 | `test_title_too_long_raises` | 标题超长校验失败 |
| 10 | `test_title_at_max_length` | 标题 200 边界 |
| 11 | `test_description_too_long_raises` | 描述超长校验失败 |
| 12 | `test_description_at_max_length` | 描述 2000 边界 |
| 13 | `test_status_string_coercion` | 字符串到枚举转换 |
| 14 | `test_invalid_status_raises` | 非法状态值 |
| 15 | `test_invalid_priority_raises` | 非法优先级值 |

#### TaskUpdate（5 个用例）

| # | 测试用例 | 说明 |
|---|----------|------|
| 16 | `test_all_fields_optional` | 所有字段可选 |
| 17 | `test_partial_update_title` | 部分更新 title |
| 18 | `test_partial_update_status` | 部分更新 status |
| 19 | `test_empty_update_excludes_all` | 空更新 |
| 20 | `test_title_validation_still_applies` | 更新时标题仍校验 |
| 21 | `test_title_max_length` | 更新时标题长度校验 |

#### TaskResponse（3 个用例）

| # | 测试用例 | 说明 |
|---|----------|------|
| 22 | `test_from_attributes_serialization` | ORM 对象序列化 |
| 23 | `test_naive_datetime_gets_utc` | 无时区 datetime 自动 UTC |
| 24 | `test_due_date_serialization` | due_date 序列化 |

#### Pagination / TaskListResponse（2 个用例）

| # | 测试用例 | 说明 |
|---|----------|------|
| 25 | `test_valid_meta` | 有效分页元数据 |
| 26 | `test_zero_total` | 总数为 0 |
| 27 | `test_valid_response` | 有效列表响应结构 |

---

## 6. 覆盖率分析

### 当前覆盖率：95%

```
Name                           Stmts   Miss  Cover
--------------------------------------------------
task_api/crud.py                  53      0   100%
task_api/models.py                18      0   100%
task_api/schemas.py               48      0   100%
task_api/routers/tasks.py         28      1    96%
task_api/services.py              57      2    96%
task_api/main.py                  10      2    80%
task_api/database.py              15      6    60%
--------------------------------------------------
TOTAL                            229     11    95%
```

### 未覆盖代码分析

| 文件 | 行号 | 原因 | 说明 |
|------|------|------|------|
| `database.py:14-18` | `get_db_session` | 生产依赖注入函数 | 测试中使用 `dependency_overrides` 替代 |
| `database.py:22-23` | `init_db` | 生产数据库初始化 | 测试引擎在 fixture 中手动建表 |
| `main.py:9-10` | `lifespan` | 应用生命周期 | ASGITransport 可能未触发 |
| `routers/tasks.py:86` | `return None` | delete 端点 | 204 响应不需要验证 None 返回 |
| `services.py:32,43` | 404 detail 字符串 | HTTPException 路径 | 已经验证了 404 状态码和中文 detail |

---

## 7. CI/CD 集成建议

### GitHub Actions

```yaml
name: Test
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: "3.11"
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests with coverage
        run: pytest --cov=task_api --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

### 本地预提交钩子

```bash
# pre-commit 配置（.pre-commit-config.yaml）
- repo: local
  hooks:
    - id: pytest
      name: pytest
      entry: python -m pytest
      language: system
      pass_filenames: false
      always_run: true
```

---

## 8. 命名规范

| 规则 | 示例 |
|------|------|
| 测试函数：`test_<测试目标>_<场景>` | `test_create_task_empty_title` |
| 测试类：`Test<被测类/端点>` | `TestCreateTask`, `TestListTasks` |
| Fixture：`<snake_case>` 描述性名称 | `sample_task`, `multiple_tasks` |
| 文件：`test_<被测模块>.py` | `test_api.py`, `test_crud.py` |

---

## 9. 故障排除

### 常见问题

| 问题 | 排查方法 |
|------|----------|
| `ModuleNotFoundError: No module named 'sqlalchemy'` | 运行 `pip install -r requirements.txt` |
| `ImportError: cannot import name 'ASGITransport'` | 升级 httpx: `pip install httpx>=0.24` |
| 测试数据库冲突 | 每个 fixture 使用 function 作用域，确保隔离 |
| 异步测试超时 | 检查 pytest-asyncio 版本 >= 0.21 |
| 中文编码问题 | 在 conftest.py 开头添加 `# -*- coding: utf-8 -*-` |

### 调试技巧

```bash
# 打印更多调试信息
python -m pytest -v --tb=long --log-cli-level=DEBUG

# 只运行失败的测试
python -m pytest --lf

# 在失败处停止
python -m pytest -x
```
