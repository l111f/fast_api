"""
Service 业务层测试：参数校验、异常处理、业务逻辑
"""
import pytest
from datetime import datetime, timezone

from fastapi import HTTPException

from task_api.schemas import TaskCreate, TaskUpdate
from task_api.services import (
    create_task_service,
    get_task_service,
    update_task_service,
    delete_task_service,
    list_tasks_service,
    ListTasksQueryParams,
    ALLOWED_SORT_FIELDS,
)


# ====================================================================
# create_task_service
# ====================================================================

class TestCreateTaskService:

    async def test_create_success(self, db_session):
        task_create = TaskCreate(title="Service Task", description="Test")
        result = await create_task_service(db_session, task_create)
        assert result.title == "Service Task"
        assert result.id is not None
        assert result.status == "todo"

    async def test_create_with_all_fields(self, db_session):
        task_create = TaskCreate(
            title="Full",
            description="Desc",
            status="in_progress",
            priority="high",
        )
        result = await create_task_service(db_session, task_create)
        assert result.status == "in_progress"
        assert result.priority == "high"


# ====================================================================
# get_task_service
# ====================================================================

class TestGetTaskService:

    async def test_get_success(self, db_session):
        created = await create_task_service(db_session, TaskCreate(title="Find"))
        result = await get_task_service(db_session, created.id)
        assert result.title == "Find"

    async def test_get_not_found_raises_404(self, db_session):
        with pytest.raises(HTTPException) as exc_info:
            await get_task_service(db_session, 99999)
        assert exc_info.value.status_code == 404
        assert "任务未找到" in str(exc_info.value.detail)


# ====================================================================
# update_task_service
# ====================================================================

class TestUpdateTaskService:

    async def test_update_success(self, db_session):
        created = await create_task_service(db_session, TaskCreate(title="Old"))
        update = TaskUpdate(title="New")
        result = await update_task_service(db_session, created.id, update)
        assert result.title == "New"

    async def test_update_not_found_raises_404(self, db_session):
        update = TaskUpdate(title="X")
        with pytest.raises(HTTPException) as exc_info:
            await update_task_service(db_session, 99999, update)
        assert exc_info.value.status_code == 404

    async def test_update_empty_body_returns_current(self, db_session):
        created = await create_task_service(db_session, TaskCreate(title="Same"))
        update = TaskUpdate()  # 所有字段为 None
        result = await update_task_service(db_session, created.id, update)
        assert result.title == "Same"

    async def test_update_partial_status_only(self, db_session):
        created = await create_task_service(db_session, TaskCreate(title="T"))
        update = TaskUpdate(status="done")
        result = await update_task_service(db_session, created.id, update)
        assert result.status == "done"
        assert result.title == "T"  # 不变


# ====================================================================
# delete_task_service
# ====================================================================

class TestDeleteTaskService:

    async def test_delete_success(self, db_session):
        created = await create_task_service(db_session, TaskCreate(title="Bye"))
        await delete_task_service(db_session, created.id)
        with pytest.raises(HTTPException) as exc_info:
            await get_task_service(db_session, created.id)
        assert exc_info.value.status_code == 404

    async def test_delete_not_found_raises_404(self, db_session):
        with pytest.raises(HTTPException) as exc_info:
            await delete_task_service(db_session, 99999)
        assert exc_info.value.status_code == 404


# ====================================================================
# ListTasksQueryParams
# ====================================================================

class TestListTasksQueryParams:

    def test_default_values(self):
        params = ListTasksQueryParams()
        assert params.page == 1
        assert params.page_size == 20
        assert params.sort_by == "created_at"
        assert params.sort_order == "desc"
        assert params.status is None
        assert params.priority is None
        assert params.search is None

    def test_status_split_by_comma(self):
        params = ListTasksQueryParams(status="todo,done")
        assert params.status == ["todo", "done"]

    def test_priority_split_by_comma(self):
        params = ListTasksQueryParams(priority="high,low")
        assert params.priority == ["high", "low"]

    def test_single_status_no_comma(self):
        params = ListTasksQueryParams(status="todo")
        assert params.status == ["todo"]

    def test_none_status_stays_none(self):
        params = ListTasksQueryParams()
        assert params.status is None


# ====================================================================
# list_tasks_service - 参数校验
# ====================================================================

class TestListTasksServiceValidation:

    async def test_page_less_than_1_raises_422(self, db_session):
        query = ListTasksQueryParams(page=0)
        with pytest.raises(HTTPException) as exc_info:
            await list_tasks_service(db_session, query)
        assert exc_info.value.status_code == 422

    async def test_page_negative_raises_422(self, db_session):
        query = ListTasksQueryParams(page=-1)
        with pytest.raises(HTTPException) as exc_info:
            await list_tasks_service(db_session, query)
        assert exc_info.value.status_code == 422

    async def test_page_size_zero_raises_422(self, db_session):
        query = ListTasksQueryParams(page_size=0)
        with pytest.raises(HTTPException) as exc_info:
            await list_tasks_service(db_session, query)
        assert exc_info.value.status_code == 422

    async def test_page_size_over_100_raises_422(self, db_session):
        query = ListTasksQueryParams(page_size=101)
        with pytest.raises(HTTPException) as exc_info:
            await list_tasks_service(db_session, query)
        assert exc_info.value.status_code == 422

    async def test_page_size_negative_raises_422(self, db_session):
        query = ListTasksQueryParams(page_size=-1)
        with pytest.raises(HTTPException) as exc_info:
            await list_tasks_service(db_session, query)
        assert exc_info.value.status_code == 422

    async def test_invalid_sort_by_raises_422(self, db_session):
        query = ListTasksQueryParams(sort_by="invalid_column")
        with pytest.raises(HTTPException) as exc_info:
            await list_tasks_service(db_session, query)
        assert exc_info.value.status_code == 422

    async def test_page_size_100_is_valid(self, db_session):
        """page_size=100 是合法的边界值"""
        query = ListTasksQueryParams(page_size=100)
        result = await list_tasks_service(db_session, query)
        assert result.pagination.page_size == 100

    async def test_page_size_1_is_valid(self, db_session):
        """page_size=1 是合法的边界值"""
        query = ListTasksQueryParams(page_size=1)
        result = await list_tasks_service(db_session, query)
        assert result.pagination.page_size == 1


# ====================================================================
# list_tasks_service - 正常流程
# ====================================================================

class TestListTasksServiceNormal:

    async def test_empty_result(self, db_session):
        query = ListTasksQueryParams()
        result = await list_tasks_service(db_session, query)
        assert result.items == []
        assert result.pagination.total == 0
        assert result.pagination.total_pages == 1

    async def test_with_data(self, db_session):
        await create_task_service(db_session, TaskCreate(title="A"))
        await create_task_service(db_session, TaskCreate(title="B"))
        query = ListTasksQueryParams()
        result = await list_tasks_service(db_session, query)
        assert len(result.items) == 2
        assert result.pagination.total == 2
        assert result.pagination.total_pages == 1

    async def test_pagination_calculation(self, db_session):
        for i in range(5):
            await create_task_service(db_session, TaskCreate(title=f"T{i}"))
        query = ListTasksQueryParams(page=1, page_size=2)
        result = await list_tasks_service(db_session, query)
        assert len(result.items) == 2
        assert result.pagination.total == 5
        assert result.pagination.total_pages == 3

    async def test_filter_by_status(self, db_session):
        await create_task_service(db_session, TaskCreate(title="A", status="todo"))
        await create_task_service(db_session, TaskCreate(title="B", status="done"))
        query = ListTasksQueryParams(status="done")
        result = await list_tasks_service(db_session, query)
        assert result.pagination.total == 1

    async def test_search(self, db_session):
        await create_task_service(db_session, TaskCreate(title="Python"))
        await create_task_service(db_session, TaskCreate(title="Java"))
        query = ListTasksQueryParams(search="Python")
        result = await list_tasks_service(db_session, query)
        assert result.pagination.total == 1

    async def test_response_structure(self, db_session):
        query = ListTasksQueryParams()
        result = await list_tasks_service(db_session, query)
        assert hasattr(result, "items")
        assert hasattr(result, "pagination")
        assert result.pagination.page == 1
        assert result.pagination.page_size == 20


# ====================================================================
# ALLOWED_SORT_FIELDS 常量
# ====================================================================

class TestAllowedSortFields:

    def test_contains_all_expected_fields(self):
        expected = {"title", "status", "priority", "due_date", "created_at", "updated_at"}
        assert ALLOWED_SORT_FIELDS == expected

    def test_is_frozen_set(self):
        assert isinstance(ALLOWED_SORT_FIELDS, set)
