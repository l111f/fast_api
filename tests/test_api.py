"""
API 端点集成测试：通过 HTTP 客户端测试所有 6 个 RESTful 端点。
覆盖正常流程、参数校验、异常处理等场景。
"""
import pytest


# ====================================================================
# POST /api/v1/tasks — 创建任务
# ====================================================================

class TestCreateTask:

    async def test_create_task_all_fields(self, client):
        """创建任务 - 提供所有字段"""
        payload = {
            "title": "Complete Project",
            "description": "Finish the FastAPI project",
            "status": "in_progress",
            "priority": "high",
            "due_date": "2025-12-31T23:59:59Z",
        }
        resp = await client.post("/api/v1/tasks", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "Complete Project"
        assert data["description"] == "Finish the FastAPI project"
        assert data["status"] == "in_progress"
        assert data["priority"] == "high"
        assert data["due_date"] == "2025-12-31T23:59:59Z"
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    async def test_create_task_minimal(self, client):
        """创建任务 - 仅提供必填字段 title"""
        resp = await client.post("/api/v1/tasks", json={"title": "Minimal Task"})
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "Minimal Task"
        assert data["description"] is None
        assert data["status"] == "todo"
        assert data["priority"] == "medium"
        assert data["due_date"] is None

    async def test_create_task_default_values(self, client):
        """创建任务 - 验证 status 和 priority 默认值"""
        resp = await client.post("/api/v1/tasks", json={
            "title": "Defaults Test",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "todo"
        assert data["priority"] == "medium"

    async def test_create_task_empty_title(self, client):
        """创建任务 - 空标题 → 422"""
        resp = await client.post("/api/v1/tasks", json={"title": ""})
        assert resp.status_code == 422

    async def test_create_task_title_too_long(self, client):
        """创建任务 - 标题超过 200 字符 → 422"""
        resp = await client.post("/api/v1/tasks", json={"title": "x" * 201})
        assert resp.status_code == 422

    async def test_create_task_description_too_long(self, client):
        """创建任务 - 描述超过 2000 字符 → 422"""
        resp = await client.post("/api/v1/tasks", json={
            "title": "Valid Title",
            "description": "x" * 2001,
        })
        assert resp.status_code == 422

    async def test_create_task_invalid_status(self, client):
        """创建任务 - 无效 status 枚举值 → 422"""
        resp = await client.post("/api/v1/tasks", json={
            "title": "Test",
            "status": "invalid_status",
        })
        assert resp.status_code == 422

    async def test_create_task_invalid_priority(self, client):
        """创建任务 - 无效 priority 枚举值 → 422"""
        resp = await client.post("/api/v1/tasks", json={
            "title": "Test",
            "priority": "urgent",
        })
        assert resp.status_code == 422

    async def test_create_task_missing_body(self, client):
        """创建任务 - 缺少请求体 → 422"""
        resp = await client.post("/api/v1/tasks")
        assert resp.status_code == 422

    async def test_create_task_response_has_timestamps(self, client):
        """创建任务 - 响应包含 created_at 和 updated_at"""
        resp = await client.post("/api/v1/tasks", json={"title": "Timestamp Test"})
        assert resp.status_code == 201
        data = resp.json()
        assert data["created_at"] is not None
        assert data["updated_at"] is not None
        # 验证时间格式：YYYY-MM-DDTHH:MM:SSZ
        assert data["created_at"].endswith("Z")
        assert data["updated_at"].endswith("Z")


# ====================================================================
# GET /api/v1/tasks/{task_id} — 获取单个任务
# ====================================================================

class TestGetTask:

    async def test_get_task_success(self, client, sample_task):
        """获取单个任务 - 成功"""
        task_id = sample_task["id"]
        resp = await client.get(f"/api/v1/tasks/{task_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == task_id
        assert data["title"] == "Sample Task"

    async def test_get_task_not_found(self, client):
        """获取单个任务 - 不存在 → 404"""
        resp = await client.get("/api/v1/tasks/99999")
        assert resp.status_code == 404
        assert "任务未找到" in resp.json()["detail"]

    async def test_get_task_returns_all_fields(self, client, sample_task):
        """获取单个任务 - 响应包含所有字段"""
        resp = await client.get(f"/api/v1/tasks/{sample_task['id']}")
        data = resp.json()
        expected_keys = {"id", "title", "description", "status", "priority",
                         "due_date", "created_at", "updated_at"}
        assert set(data.keys()) == expected_keys


# ====================================================================
# PUT /api/v1/tasks/{task_id} — 全量更新
# ====================================================================

class TestUpdateTaskPut:

    async def test_update_task_full(self, client, sample_task):
        """全量更新 - 成功"""
        task_id = sample_task["id"]
        payload = {
            "title": "Updated Title",
            "description": "Updated description",
            "status": "done",
            "priority": "low",
        }
        resp = await client.put(f"/api/v1/tasks/{task_id}", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "Updated Title"
        assert data["description"] == "Updated description"
        assert data["status"] == "done"
        assert data["priority"] == "low"

    async def test_update_task_not_found(self, client):
        """全量更新 - 不存在 → 404"""
        resp = await client.put("/api/v1/tasks/99999", json={"title": "X"})
        assert resp.status_code == 404

    async def test_update_task_invalid_status(self, client, sample_task):
        """全量更新 - 无效 status → 422"""
        resp = await client.put(f"/api/v1/tasks/{sample_task['id']}", json={
            "title": "Test",
            "status": "invalid",
        })
        assert resp.status_code == 422

    async def test_update_task_empty_title(self, client, sample_task):
        """全量更新 - 空标题 → 422"""
        resp = await client.put(f"/api/v1/tasks/{sample_task['id']}", json={
            "title": "",
        })
        assert resp.status_code == 422

    async def test_update_task_updated_at_refreshes(self, client, sample_task):
        """全量更新 - updated_at 自动刷新"""
        original_updated_at = sample_task["updated_at"]
        resp = await client.put(
            f"/api/v1/tasks/{sample_task['id']}",
            json={"title": "Refresh Test"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["updated_at"] >= original_updated_at

    async def test_update_task_created_at_immutable(self, client, sample_task):
        """全量更新 - created_at 不可被修改"""
        original_created_at = sample_task["created_at"]
        resp = await client.put(
            f"/api/v1/tasks/{sample_task['id']}",
            json={"title": "Immutable Test"},
        )
        assert resp.status_code == 200
        assert resp.json()["created_at"] == original_created_at


# ====================================================================
# PATCH /api/v1/tasks/{task_id} — 部分更新
# ====================================================================

class TestUpdateTaskPatch:

    async def test_update_task_single_field(self, client, sample_task):
        """部分更新 - 仅更新 title"""
        resp = await client.patch(
            f"/api/v1/tasks/{sample_task['id']}",
            json={"title": "Patched Title"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "Patched Title"
        # 其他字段保持不变
        assert data["description"] == sample_task["description"]
        assert data["status"] == sample_task["status"]

    async def test_update_task_status_only(self, client, sample_task):
        """部分更新 - 仅更新 status"""
        resp = await client.patch(
            f"/api/v1/tasks/{sample_task['id']}",
            json={"status": "done"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "done"

    async def test_update_task_not_found(self, client):
        """部分更新 - 不存在 → 404"""
        resp = await client.patch("/api/v1/tasks/99999", json={"title": "X"})
        assert resp.status_code == 404

    async def test_update_task_empty_body(self, client, sample_task):
        """部分更新 - 空请求体，返回当前状态（无变更）"""
        resp = await client.patch(
            f"/api/v1/tasks/{sample_task['id']}",
            json={},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == sample_task["title"]
        assert data["status"] == sample_task["status"]

    async def test_update_task_invalid_data(self, client, sample_task):
        """部分更新 - 非法字段值 → 422"""
        resp = await client.patch(
            f"/api/v1/tasks/{sample_task['id']}",
            json={"status": "invalid"},
        )
        assert resp.status_code == 422


# ====================================================================
# DELETE /api/v1/tasks/{task_id} — 删除任务
# ====================================================================

class TestDeleteTask:

    async def test_delete_task_success(self, client, sample_task):
        """删除任务 - 成功 → 204"""
        resp = await client.delete(f"/api/v1/tasks/{sample_task['id']}")
        assert resp.status_code == 204

    async def test_delete_task_not_found(self, client):
        """删除任务 - 不存在 → 404"""
        resp = await client.delete("/api/v1/tasks/99999")
        assert resp.status_code == 404

    async def test_delete_task_twice(self, client, sample_task):
        """删除任务 - 重复删除 → 404"""
        task_id = sample_task["id"]
        resp1 = await client.delete(f"/api/v1/tasks/{task_id}")
        assert resp1.status_code == 204
        resp2 = await client.delete(f"/api/v1/tasks/{task_id}")
        assert resp2.status_code == 404

    async def test_delete_task_then_get(self, client, sample_task):
        """删除任务 - 删除后再 GET → 404"""
        task_id = sample_task["id"]
        await client.delete(f"/api/v1/tasks/{task_id}")
        resp = await client.get(f"/api/v1/tasks/{task_id}")
        assert resp.status_code == 404

    async def test_delete_task_response_body_empty(self, client, sample_task):
        """删除任务 - 响应体为空"""
        resp = await client.delete(f"/api/v1/tasks/{sample_task['id']}")
        assert resp.status_code == 204
        assert resp.text == "" or resp.content == b""


# ====================================================================
# GET /api/v1/tasks — 获取任务列表
# ====================================================================

class TestListTasks:

    async def test_list_tasks_empty(self, client):
        """获取列表 - 空数据库"""
        resp = await client.get("/api/v1/tasks")
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []
        assert data["pagination"]["total"] == 0
        assert data["pagination"]["page"] == 1
        assert data["pagination"]["page_size"] == 20
        assert data["pagination"]["total_pages"] == 1

    async def test_list_tasks_with_data(self, client, multiple_tasks):
        """获取列表 - 有数据"""
        resp = await client.get("/api/v1/tasks")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 5
        assert data["pagination"]["total"] == 5

    async def test_list_tasks_filter_by_status(self, client, multiple_tasks):
        """获取列表 - 按单个状态筛选"""
        resp = await client.get("/api/v1/tasks?status=todo")
        assert resp.status_code == 200
        data = resp.json()
        assert data["pagination"]["total"] == 2
        for item in data["items"]:
            assert item["status"] == "todo"

    async def test_list_tasks_filter_by_multiple_status(self, client, multiple_tasks):
        """获取列表 - 按多个状态筛选（逗号分隔）"""
        resp = await client.get("/api/v1/tasks?status=todo,done")
        assert resp.status_code == 200
        data = resp.json()
        assert data["pagination"]["total"] == 3
        for item in data["items"]:
            assert item["status"] in ("todo", "done")

    async def test_list_tasks_filter_by_priority(self, client, multiple_tasks):
        """获取列表 - 按优先级筛选"""
        resp = await client.get("/api/v1/tasks?priority=high")
        assert resp.status_code == 200
        data = resp.json()
        assert data["pagination"]["total"] == 2
        for item in data["items"]:
            assert item["priority"] == "high"

    async def test_list_tasks_filter_by_multiple_priority(self, client, multiple_tasks):
        """获取列表 - 按多个优先级筛选"""
        resp = await client.get("/api/v1/tasks?priority=high,low")
        assert resp.status_code == 200
        data = resp.json()
        # high: Alpha, Epsilon (2) + low: Gamma, Delta (2) = 4
        assert data["pagination"]["total"] == 4

    async def test_list_tasks_search_in_title(self, client, multiple_tasks):
        """获取列表 - 模糊搜索标题"""
        resp = await client.get("/api/v1/tasks?search=Alpha")
        assert resp.status_code == 200
        data = resp.json()
        assert data["pagination"]["total"] == 1
        assert data["items"][0]["title"] == "Alpha Task"

    async def test_list_tasks_search_in_description(self, client, multiple_tasks):
        """获取列表 - 模糊搜索描述"""
        resp = await client.get("/api/v1/tasks?search=Python")
        assert resp.status_code == 200
        data = resp.json()
        assert data["pagination"]["total"] == 1
        assert "Python" in data["items"][0]["description"]

    async def test_list_tasks_search_case_insensitive(self, client, multiple_tasks):
        """获取列表 - 搜索不区分大小写"""
        resp = await client.get("/api/v1/tasks?search=python")
        assert resp.status_code == 200
        data = resp.json()
        assert data["pagination"]["total"] == 1

    async def test_list_tasks_pagination_page1(self, client, multiple_tasks):
        """获取列表 - 分页：第 1 页"""
        resp = await client.get("/api/v1/tasks?page=1&page_size=2")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 2
        assert data["pagination"]["page"] == 1
        assert data["pagination"]["page_size"] == 2
        assert data["pagination"]["total"] == 5
        assert data["pagination"]["total_pages"] == 3

    async def test_list_tasks_pagination_page2(self, client, multiple_tasks):
        """获取列表 - 分页：第 2 页"""
        resp = await client.get("/api/v1/tasks?page=2&page_size=2")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 2
        assert data["pagination"]["page"] == 2

    async def test_list_tasks_pagination_last_page(self, client, multiple_tasks):
        """获取列表 - 分页：最后一页（不满页）"""
        resp = await client.get("/api/v1/tasks?page=3&page_size=2")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 1

    async def test_list_tasks_pagination_beyond_range(self, client, multiple_tasks):
        """获取列表 - 分页：超出范围返回空列表"""
        resp = await client.get("/api/v1/tasks?page=100&page_size=2")
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []
        assert data["pagination"]["total"] == 5

    async def test_list_tasks_sort_by_title_asc(self, client, multiple_tasks):
        """获取列表 - 按标题升序排序"""
        resp = await client.get("/api/v1/tasks?sort_by=title&sort_order=asc")
        assert resp.status_code == 200
        data = resp.json()
        titles = [item["title"] for item in data["items"]]
        assert titles == sorted(titles)

    async def test_list_tasks_sort_by_title_desc(self, client, multiple_tasks):
        """获取列表 - 按标题降序排序"""
        resp = await client.get("/api/v1/tasks?sort_by=title&sort_order=desc")
        assert resp.status_code == 200
        data = resp.json()
        titles = [item["title"] for item in data["items"]]
        assert titles == sorted(titles, reverse=True)

    async def test_list_tasks_sort_by_status(self, client, multiple_tasks):
        """获取列表 - 按 status 排序"""
        resp = await client.get("/api/v1/tasks?sort_by=status&sort_order=asc")
        assert resp.status_code == 200
        data = resp.json()
        statuses = [item["status"] for item in data["items"]]
        assert statuses == sorted(statuses)

    async def test_list_tasks_default_sort_created_at_desc(self, client, multiple_tasks):
        """获取列表 - 默认按 created_at 降序"""
        resp = await client.get("/api/v1/tasks")
        assert resp.status_code == 200
        data = resp.json()
        # 最后创建的应该在前面
        assert data["items"][0]["title"] == "Epsilon Task"

    async def test_list_tasks_invalid_page_zero(self, client):
        """获取列表 - page=0 → 422"""
        resp = await client.get("/api/v1/tasks?page=0")
        assert resp.status_code == 422

    async def test_list_tasks_invalid_page_negative(self, client):
        """获取列表 - page=-1 → 422"""
        resp = await client.get("/api/v1/tasks?page=-1")
        assert resp.status_code == 422

    async def test_list_tasks_invalid_page_size_zero(self, client):
        """获取列表 - page_size=0 → 422"""
        resp = await client.get("/api/v1/tasks?page_size=0")
        assert resp.status_code == 422

    async def test_list_tasks_invalid_page_size_too_large(self, client):
        """获取列表 - page_size=101 → 422"""
        resp = await client.get("/api/v1/tasks?page_size=101")
        assert resp.status_code == 422

    async def test_list_tasks_invalid_sort_by(self, client):
        """获取列表 - sort_by 非法字段 → 422"""
        resp = await client.get("/api/v1/tasks?sort_by=nonexistent")
        assert resp.status_code == 422

    async def test_list_tasks_combined_filters(self, client, multiple_tasks):
        """获取列表 - 组合筛选：status + priority"""
        resp = await client.get("/api/v1/tasks?status=todo&priority=high")
        assert resp.status_code == 200
        data = resp.json()
        assert data["pagination"]["total"] == 1
        assert data["items"][0]["title"] == "Alpha Task"

    async def test_list_tasks_filter_no_match(self, client, multiple_tasks):
        """获取列表 - 筛选无匹配结果"""
        resp = await client.get("/api/v1/tasks?status=done&priority=high")
        assert resp.status_code == 200
        data = resp.json()
        assert data["pagination"]["total"] == 0
        assert data["items"] == []

    async def test_list_tasks_response_structure(self, client, multiple_tasks):
        """获取列表 - 验证响应结构包含 items 和 pagination"""
        resp = await client.get("/api/v1/tasks")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "pagination" in data
        pagination = data["pagination"]
        assert "page" in pagination
        assert "page_size" in pagination
        assert "total" in pagination
        assert "total_pages" in pagination

    async def test_list_tasks_date_filter(self, client):
        """获取列表 - 按截止日期范围筛选"""
        # 创建两个带 due_date 的任务
        await client.post("/api/v1/tasks", json={
            "title": "Early", "due_date": "2025-01-15T00:00:00Z",
        })
        await client.post("/api/v1/tasks", json={
            "title": "Late", "due_date": "2025-12-15T00:00:00Z",
        })
        resp = await client.get(
            "/api/v1/tasks?due_date_from=2025-06-01T00:00:00Z"
            "&due_date_to=2025-12-31T23:59:59Z"
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["pagination"]["total"] == 1
        assert data["items"][0]["title"] == "Late"
