# Specs: SD-01 RESTful 任务管理 API


---

## 1. 概述 (Overview)

### 1.1 背景与目标
系统 SHALL 提供一个轻量级 RESTful 任务管理 API，为上层应用提供统一、规范的任务数据操作接口。通过标准化的 CRUD 接口、灵活的多条件过滤与分页排序能力，支持各类客户端对任务数据进行高效管理。

### 1.2 范围

**In Scope:**
- 任务资源的 CRUD 接口设计与实现。
- 查询接口的多条件过滤、分页、排序参数规格。
- 请求数据的输入验证与错误响应格式。
- 基于 OpenAPI 3.1 的 API 文档自动生成。

**Out of Scope:**
- 用户认证与授权（本版本为单用户/开放 API）。
- 前端界面开发。
- 文件附件上传功能。
- 任务标签/分类管理。
- 任务指派/协作功能。

---

## 2. 功能规格 (Functional Specifications)

### Requirement: FR-001 创建任务

The system SHALL 允许 API 消费者通过 HTTP POST 向 `/api/v1/tasks` 提交任务数据，校验通过后持久化并返回创建成功的任务对象。

#### Scenario: 正常创建任务
- GIVEN 客户端提供了合法的 JSON 请求体（包含必填字段 `title`）
- WHEN 客户端发送 `POST /api/v1/tasks`
- THEN 系统 SHALL 返回 HTTP 201，响应体包含完整的任务对象（含系统生成的 `id`、`created_at`、`updated_at`）

#### Scenario: 缺少必填字段
- GIVEN 客户端提交的请求体缺少 `title` 字段
- WHEN 客户端发送 `POST /api/v1/tasks`
- THEN 系统 SHALL 返回 HTTP 422，响应体 `detail` 数组中须包含 `loc` 指向缺失字段的错误项

#### Scenario: 非法枚举值
- GIVEN 客户端提交的请求体中 `status` 为 `"invalid_status"`
- WHEN 客户端发送 `POST /api/v1/tasks`
- THEN 系统 SHALL 返回 HTTP 422，响应体须指明该字段值不在允许的枚举列表中

#### Scenario: 字段长度越界（边界条件）
- GIVEN 客户端提交的 `title` 长度超过 200 字符或为空字符串
- WHEN 客户端发送 `POST /api/v1/tasks`
- THEN 系统 SHALL 返回 HTTP 422，响应体须指明 `title` 字段校验失败原因

---

### Requirement: FR-002 获取任务详情

The system SHALL 允许 API 消费者通过 HTTP GET 访问 `/api/v1/tasks/{task_id}` 获取对应任务详情。

#### Scenario: 获取已存在的任务
- GIVEN 数据库中存在 `task_id = 1` 的任务记录
- WHEN 客户端发送 `GET /api/v1/tasks/1`
- THEN 系统 SHALL 返回 HTTP 200 及该任务的完整 JSON 对象

#### Scenario: 获取不存在的任务
- GIVEN 数据库中不存在 `task_id = 9999` 的任务记录
- WHEN 客户端发送 `GET /api/v1/tasks/9999`
- THEN 系统 SHALL 返回 HTTP 404，响应体 `detail` 须包含明确的“任务未找到”描述

#### Scenario: 非法 ID 格式
- GIVEN 客户端请求路径中 `task_id` 为 `"abc"`
- WHEN 客户端发送 `GET /api/v1/tasks/abc`
- THEN 系统 SHALL 返回 HTTP 422，提示路径参数类型非法

---

### Requirement: FR-003 更新任务

The system SHALL 允许 API 消费者通过 HTTP PUT（全量替换）或 PATCH（部分更新）向 `/api/v1/tasks/{task_id}` 提交更新数据，校验后更新对应任务。

#### Scenario: 正常更新任务
- GIVEN 数据库中存在 `task_id = 1` 的任务记录
- WHEN 客户端发送 `PATCH /api/v1/tasks/1`，请求体仅包含 `"status": "done"`
- THEN 系统 SHALL 返回 HTTP 200 及更新后的完整任务对象，且 `updated_at` 字段值须晚于更新前的值

#### Scenario: 更新不存在的任务
- GIVEN 数据库中不存在 `task_id = 9999` 的任务记录
- WHEN 客户端发送 `PUT /api/v1/tasks/9999`
- THEN 系统 SHALL 返回 HTTP 404，提示对应任务未找到

#### Scenario: 更新时传入非法字段值
- GIVEN 数据库中存在 `task_id = 1` 的任务记录
- WHEN 客户端发送 `PUT /api/v1/tasks/1`，请求体中 `priority` 为 `"urgent"`
- THEN 系统 SHALL 返回 HTTP 422，响应体须指明 `priority` 字段值非法

---

### Requirement: FR-004 删除任务

The system SHALL 允许 API 消费者通过 HTTP DELETE 访问 `/api/v1/tasks/{task_id}` 删除对应任务。

#### Scenario: 正常删除任务
- GIVEN 数据库中存在 `task_id = 1` 的任务记录
- WHEN 客户端发送 `DELETE /api/v1/tasks/1`
- THEN 系统 SHALL 返回 HTTP 204，响应体为空；再次请求 `GET /api/v1/tasks/1` 时须返回 HTTP 404

#### Scenario: 删除不存在的任务
- GIVEN 数据库中不存在 `task_id = 9999` 的任务记录
- WHEN 客户端发送 `DELETE /api/v1/tasks/9999`
- THEN 系统 SHALL 返回 HTTP 404，提示对应任务未找到

---

### Requirement: FR-005 获取任务列表（支持过滤、分页、排序）

The system SHALL 允许 API 消费者通过 HTTP GET 访问 `/api/v1/tasks` 获取符合条件的任务列表，支持多条件组合过滤、分页与单字段排序。

#### Scenario: 无过滤条件查询
- GIVEN 数据库中存在 150 条任务记录
- WHEN 客户端发送 `GET /api/v1/tasks`（无查询参数）
- THEN 系统 SHALL 返回 HTTP 200，响应体 `items` 包含第 1 页数据（默认 20 条），`pagination.total` 等于 150，`pagination.total_pages` 等于 8

#### Scenario: 多条件组合过滤
- GIVEN 数据库中存在多种状态与优先级的任务
- WHEN 客户端发送 `GET /api/v1/tasks?status=todo&priority=high`
- THEN 系统 SHALL 返回 HTTP 200，且 `items` 中所有任务须同时满足 `status = "todo"` 且 `priority = "high"`

#### Scenario: 同字段多值过滤（OR 关系）
- GIVEN 数据库中存在不同状态的任务
- WHEN 客户端发送 `GET /api/v1/tasks?status=todo,in_progress`
- THEN 系统 SHALL 返回 HTTP 200，且 `items` 中所有任务的状态须为 `todo` 或 `in_progress`

#### Scenario: 分页参数越界（边界条件）
- GIVEN 客户端请求参数中 `page = 0`
- WHEN 客户端发送 `GET /api/v1/tasks?page=0`
- THEN 系统 SHALL 返回 HTTP 422，提示 `page` 参数范围非法

#### Scenario: 非法排序字段
- GIVEN 客户端请求参数中 `sort_by = "deleted_at"`
- WHEN 客户端发送 `GET /api/v1/tasks?sort_by=deleted_at`
- THEN 系统 SHALL 返回 HTTP 422，提示 `sort_by` 字段不在允许列表中

#### Scenario: 时间范围过滤（边界条件）
- GIVEN 数据库中存在截止时间为 2026-06-01 的任务
- WHEN 客户端发送 `GET /api/v1/tasks?due_date_from=2026-06-01T00:00:00&due_date_to=2026-06-01T23:59:59`
- THEN 系统 SHALL 返回 HTTP 200，且结果中须包含该日期内的任务记录

---

### Requirement: FR-006 统一的数据验证与错误响应

The system SHALL 对所有入参请求进行数据校验，并在校验失败或业务异常时返回结构统一、语义清晰的错误响应。

#### Scenario: 请求体 JSON 格式错误
- GIVEN 客户端发送的请求体不是合法 JSON
- WHEN 客户端发送任意 POST/PUT/PATCH 请求
- THEN 系统 SHALL 返回 HTTP 400，响应体 `detail` 须提示请求体无法解析

#### Scenario: 字段级校验失败
- GIVEN 客户端提交的请求体中包含多个非法字段
- WHEN 客户端发送 `POST /api/v1/tasks`
- THEN 系统 SHALL 返回 HTTP 422，响应体 `detail` 为数组，每个元素须包含 `loc`、`msg`、`type`，且覆盖所有非法字段

---

### Requirement: FR-007 OpenAPI/Swagger 文档自动生成

The system SHALL 基于接口定义自动生成符合 OpenAPI 3.1 规范的 API 文档，并提供可交互的 Swagger UI。

#### Scenario: 访问 Swagger UI
- GIVEN 应用服务已正常启动
- WHEN 客户端通过浏览器访问 `/api/v1/docs`
- THEN 系统 SHALL 返回可交互的 Swagger UI 页面，且页面中须包含所有端点、请求/响应模型、字段类型、必填标记及枚举值说明

#### Scenario: 获取原始 OpenAPI JSON
- GIVEN 应用服务已正常启动
- WHEN 客户端发送 `GET /api/v1/openapi.json`
- THEN 系统 SHALL 返回 HTTP 200 及符合 OpenAPI 3.1 规范的 JSON 文档，且文档内容须与当前代码定义保持一致

---

## 3. 数据规格 (Data Specifications)

### 3.1 任务模型字段定义

| 字段名 | 数据类型 | 必填 | 默认值 | 约束与说明 |
|--------|---------|------|--------|-----------|
| `id` | Integer (主键) | 系统自动生成 | 自增 | 唯一标识，不可修改 |
| `title` | String | MUST | — | 长度 1~200 字符 |
| `description` | String | MAY | `null` | 最大长度 2000 字符 |
| `status` | String (枚举) | MUST | `"todo"` | 枚举值：`todo`、`in_progress`、`done` |
| `priority` | String (枚举) | MUST | `"medium"` | 枚举值：`low`、`medium`、`high` |
| `due_date` | DateTime (ISO 8601) | MAY | `null` | 格式：`YYYY-MM-DDTHH:MM:SS` |
| `created_at` | DateTime | 系统自动生成 | 当前时间 | 不可修改 |
| `updated_at` | DateTime | 系统自动生成 | 当前时间 | 每次更新自动刷新 |

### 3.2 过滤参数规格

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `status` | String | 否 | 支持单一值或逗号分隔多值（OR 关系） |
| `priority` | String | 否 | 支持单一值或逗号分隔多值（OR 关系） |
| `due_date_from` | DateTime | 否 | 截止时间起始范围（包含） |
| `due_date_to` | DateTime | 否 | 截止时间结束范围（包含） |
| `created_at_from` | DateTime | 否 | 创建时间起始范围（包含） |
| `created_at_to` | DateTime | 否 | 创建时间结束范围（包含） |
| `search` | String | 否 | 对 `title` 与 `description` 模糊匹配 |

### 3.3 分页参数规格

| 参数名 | 类型 | 必填 | 默认值 | 约束 |
|--------|------|------|--------|------|
| `page` | Integer | 否 | `1` | 最小值 `1` |
| `page_size` | Integer | 否 | `20` | 最大值 `100` |

**分页响应元数据结构:**

```json
{
  "items": [...],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total": 150,
    "total_pages": 8
  }
}
```

### 3.4 排序参数规格

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `sort_by` | String | 否 | `"created_at"` | 允许：`title`、`status`、`priority`、`due_date`、`created_at`、`updated_at` |
| `sort_order` | String | 否 | `"desc"` | 允许：`asc`、`desc` |

---

## 4. 假设与依赖 (Assumptions & Dependencies)

### 4.1 假设
- 当前版本为单用户系统，不考虑多租户或用户隔离。
- 所有日期时间字段在接口层面统一采用 ISO 8601 格式字符串交互。
- API 版本通过 URL 路径 `/api/v1/` 进行硬编码管理，不存在版本协商机制。

### 4.2 技术依赖
- FastAPI（请求校验、依赖注入、自动文档生成）。
- SQLAlchemy 2.0 异步会话（SQLite 数据库操作）。
- Pydantic v2（请求/响应模型的序列化与反序列化）。

---

> **文档版本**: v1.0  
> **更新时间**: 2026-05-17
