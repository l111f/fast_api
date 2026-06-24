"""
Pydantic Schema 验证测试：TaskCreate / TaskUpdate / TaskResponse / 枚举类
"""
import pytest
from datetime import datetime, timezone
from pydantic import ValidationError

from task_api.schemas import (
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskStatus,
    TaskPriority,
    PaginationMeta,
    TaskListResponse,
)


# ====================================================================
# 枚举类测试
# ====================================================================

class TestTaskStatusEnum:

    def test_valid_values(self):
        assert TaskStatus.todo == "todo"
        assert TaskStatus.in_progress == "in_progress"
        assert TaskStatus.done == "done"

    def test_invalid_value(self):
        with pytest.raises(ValueError):
            TaskStatus("invalid")

    def test_is_string(self):
        assert isinstance(TaskStatus.todo, str)


class TestTaskPriorityEnum:

    def test_valid_values(self):
        assert TaskPriority.low == "low"
        assert TaskPriority.medium == "medium"
        assert TaskPriority.high == "high"

    def test_invalid_value(self):
        with pytest.raises(ValueError):
            TaskPriority("urgent")


# ====================================================================
# TaskCreate 测试
# ====================================================================

class TestTaskCreate:

    def test_valid_minimal(self):
        task = TaskCreate(title="Test")
        assert task.title == "Test"
        assert task.description is None
        assert task.status == TaskStatus.todo
        assert task.priority == TaskPriority.medium
        assert task.due_date is None

    def test_valid_all_fields(self):
        task = TaskCreate(
            title="Full Task",
            description="Desc",
            status=TaskStatus.in_progress,
            priority=TaskPriority.high,
            due_date=datetime(2025, 12, 31, tzinfo=timezone.utc),
        )
        assert task.title == "Full Task"
        assert task.status == TaskStatus.in_progress

    def test_title_empty_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            TaskCreate(title="")
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("title",) for e in errors)

    def test_title_too_long_raises(self):
        with pytest.raises(ValidationError):
            TaskCreate(title="x" * 201)

    def test_title_at_max_length(self):
        task = TaskCreate(title="x" * 200)
        assert len(task.title) == 200

    def test_description_too_long_raises(self):
        with pytest.raises(ValidationError):
            TaskCreate(title="OK", description="x" * 2001)

    def test_description_at_max_length(self):
        task = TaskCreate(title="OK", description="x" * 2000)
        assert len(task.description) == 2000

    def test_status_string_coercion(self):
        task = TaskCreate(title="T", status="todo")
        assert task.status == TaskStatus.todo

    def test_invalid_status_raises(self):
        with pytest.raises(ValidationError):
            TaskCreate(title="T", status="unknown")

    def test_invalid_priority_raises(self):
        with pytest.raises(ValidationError):
            TaskCreate(title="T", priority="critical")


# ====================================================================
# TaskUpdate 测试
# ====================================================================

class TestTaskUpdate:

    def test_all_fields_optional(self):
        update = TaskUpdate()
        assert update.title is None
        assert update.description is None
        assert update.status is None
        assert update.priority is None
        assert update.due_date is None

    def test_partial_update_title(self):
        update = TaskUpdate(title="New Title")
        dumped = update.model_dump(exclude_unset=True)
        assert dumped == {"title": "New Title"}

    def test_partial_update_status(self):
        update = TaskUpdate(status=TaskStatus.done)
        dumped = update.model_dump(exclude_unset=True)
        assert "status" in dumped

    def test_empty_update_excludes_all(self):
        update = TaskUpdate()
        dumped = update.model_dump(exclude_unset=True)
        assert dumped == {}

    def test_title_validation_still_applies(self):
        with pytest.raises(ValidationError):
            TaskUpdate(title="")

    def test_title_max_length(self):
        with pytest.raises(ValidationError):
            TaskUpdate(title="x" * 201)


# ====================================================================
# TaskResponse 测试
# ====================================================================

class TestTaskResponse:

    def test_from_attributes_serialization(self):
        """模拟 ORM 对象序列化"""
        class FakeORM:
            id = 1
            title = "Test"
            description = "Desc"
            status = "todo"
            priority = "medium"
            due_date = None
            created_at = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
            updated_at = datetime(2025, 1, 2, 12, 0, 0, tzinfo=timezone.utc)

        resp = TaskResponse.model_validate(FakeORM())
        assert resp.id == 1
        assert resp.title == "Test"
        # 验证 datetime 序列化格式
        data = resp.model_dump()
        assert data["created_at"] == "2025-01-01T12:00:00Z"
        assert data["updated_at"] == "2025-01-02T12:00:00Z"
        assert data["due_date"] is None

    def test_naive_datetime_gets_utc(self):
        """无时区信息的 datetime 自动加 UTC"""
        class FakeORM:
            id = 1
            title = "Test"
            description = None
            status = "todo"
            priority = "medium"
            due_date = None
            created_at = datetime(2025, 6, 15, 10, 30, 0)  # 无时区
            updated_at = datetime(2025, 6, 15, 10, 30, 0)  # 无时区

        resp = TaskResponse.model_validate(FakeORM())
        data = resp.model_dump()
        assert data["created_at"] == "2025-06-15T10:30:00Z"
        assert data["updated_at"] == "2025-06-15T10:30:00Z"

    def test_due_date_serialization(self):
        """due_date 正确序列化"""
        class FakeORM:
            id = 1
            title = "Test"
            description = None
            status = "todo"
            priority = "medium"
            due_date = datetime(2025, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
            created_at = datetime(2025, 1, 1, tzinfo=timezone.utc)
            updated_at = datetime(2025, 1, 1, tzinfo=timezone.utc)

        resp = TaskResponse.model_validate(FakeORM())
        data = resp.model_dump()
        assert data["due_date"] == "2025-12-31T23:59:59Z"


# ====================================================================
# PaginationMeta / TaskListResponse 测试
# ====================================================================

class TestPaginationMeta:

    def test_valid_meta(self):
        meta = PaginationMeta(page=1, page_size=20, total=50, total_pages=3)
        assert meta.page == 1
        assert meta.total_pages == 3

    def test_zero_total(self):
        meta = PaginationMeta(page=1, page_size=20, total=0, total_pages=1)
        assert meta.total == 0


class TestTaskListResponse:

    def test_valid_response(self):
        resp = TaskListResponse(
            items=[],
            pagination=PaginationMeta(page=1, page_size=20, total=0, total_pages=1),
        )
        assert resp.items == []
        assert resp.pagination.total == 0
