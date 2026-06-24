"""
CRUD 数据访问层测试：直接测试数据库操作
"""
import pytest
from datetime import datetime, timezone

from task_api.crud import create_task, get_task, update_task, delete_task, list_tasks
from task_api.schemas import TaskCreate


# ====================================================================
# create_task
# ====================================================================

class TestCreateTaskCRUD:

    async def test_create_task_success(self, db_session):
        task_data = TaskCreate(title="CRUD Task", description="Test")
        task = await create_task(db_session, task_data)
        assert task.id is not None
        assert task.title == "CRUD Task"
        assert task.description == "Test"
        assert task.status == "todo"
        assert task.priority == "medium"
        assert task.due_date is None
        assert task.created_at is not None
        assert task.updated_at is not None

    async def test_create_task_with_all_fields(self, db_session):
        task_data = TaskCreate(
            title="Full Task",
            description="Full description",
            status="in_progress",
            priority="high",
            due_date=datetime(2025, 12, 31, 23, 59, 59, tzinfo=timezone.utc),
        )
        task = await create_task(db_session, task_data)
        assert task.status == "in_progress"
        assert task.priority == "high"
        assert task.due_date is not None

    async def test_create_multiple_tasks(self, db_session):
        for i in range(3):
            await create_task(db_session, TaskCreate(title=f"Task {i}"))
        tasks, total = await list_tasks(db_session)
        assert total == 3


# ====================================================================
# get_task
# ====================================================================

class TestGetTaskCRUD:

    async def test_get_task_found(self, db_session):
        created = await create_task(db_session, TaskCreate(title="Find Me"))
        found = await get_task(db_session, created.id)
        assert found is not None
        assert found.id == created.id
        assert found.title == "Find Me"

    async def test_get_task_not_found(self, db_session):
        found = await get_task(db_session, 99999)
        assert found is None

    async def test_get_task_returns_all_fields(self, db_session):
        created = await create_task(db_session, TaskCreate(
            title="Full",
            description="Desc",
            status="in_progress",
            priority="high",
        ))
        found = await get_task(db_session, created.id)
        assert found.title == "Full"
        assert found.description == "Desc"
        assert found.status == "in_progress"
        assert found.priority == "high"
        assert found.created_at is not None
        assert found.updated_at is not None


# ====================================================================
# update_task
# ====================================================================

class TestUpdateTaskCRUD:

    async def test_update_task_success(self, db_session):
        created = await create_task(db_session, TaskCreate(title="Before"))
        updated = await update_task(db_session, created, {"title": "After"})
        assert updated.title == "After"
        assert updated.id == created.id

    async def test_update_task_refreshes_updated_at(self, db_session):
        created = await create_task(db_session, TaskCreate(title="Time Test"))
        original_updated_at = created.updated_at
        updated = await update_task(db_session, created, {"title": "Updated"})
        assert updated.updated_at >= original_updated_at

    async def test_update_task_multiple_fields(self, db_session):
        created = await create_task(db_session, TaskCreate(title="Old"))
        updated = await update_task(db_session, created, {
            "title": "New",
            "status": "done",
            "priority": "high",
        })
        assert updated.title == "New"
        assert updated.status == "done"
        assert updated.priority == "high"

    async def test_update_task_preserves_created_at(self, db_session):
        created = await create_task(db_session, TaskCreate(title="Immutable"))
        original_created_at = created.created_at
        await update_task(db_session, created, {"title": "Changed"})
        assert created.created_at == original_created_at


# ====================================================================
# delete_task
# ====================================================================

class TestDeleteTaskCRUD:

    async def test_delete_task_success(self, db_session):
        created = await create_task(db_session, TaskCreate(title="Delete Me"))
        await delete_task(db_session, created)
        found = await get_task(db_session, created.id)
        assert found is None

    async def test_delete_task_only_target(self, db_session):
        t1 = await create_task(db_session, TaskCreate(title="Keep"))
        t2 = await create_task(db_session, TaskCreate(title="Delete"))
        await delete_task(db_session, t2)
        assert await get_task(db_session, t1.id) is not None
        assert await get_task(db_session, t2.id) is None


# ====================================================================
# list_tasks
# ====================================================================

class TestListTasksCRUD:

    async def test_list_tasks_empty(self, db_session):
        tasks, total = await list_tasks(db_session)
        assert tasks == []
        assert total == 0

    async def test_list_tasks_default_pagination(self, db_session):
        for i in range(5):
            await create_task(db_session, TaskCreate(title=f"T{i}"))
        tasks, total = await list_tasks(db_session)
        assert total == 5
        assert len(tasks) == 5

    async def test_list_tasks_filter_status(self, db_session):
        await create_task(db_session, TaskCreate(title="A", status="todo"))
        await create_task(db_session, TaskCreate(title="B", status="done"))
        tasks, total = await list_tasks(db_session, status=["done"])
        assert total == 1
        assert tasks[0].status == "done"

    async def test_list_tasks_filter_multiple_status(self, db_session):
        await create_task(db_session, TaskCreate(title="A", status="todo"))
        await create_task(db_session, TaskCreate(title="B", status="in_progress"))
        await create_task(db_session, TaskCreate(title="C", status="done"))
        tasks, total = await list_tasks(db_session, status=["todo", "done"])
        assert total == 2

    async def test_list_tasks_filter_priority(self, db_session):
        await create_task(db_session, TaskCreate(title="A", priority="high"))
        await create_task(db_session, TaskCreate(title="B", priority="low"))
        tasks, total = await list_tasks(db_session, priority=["high"])
        assert total == 1

    async def test_list_tasks_search_title(self, db_session):
        await create_task(db_session, TaskCreate(title="Python Task"))
        await create_task(db_session, TaskCreate(title="Java Task"))
        tasks, total = await list_tasks(db_session, search="Python")
        assert total == 1
        assert tasks[0].title == "Python Task"

    async def test_list_tasks_search_description(self, db_session):
        await create_task(db_session, TaskCreate(
            title="X", description="Learn Python",
        ))
        await create_task(db_session, TaskCreate(
            title="Y", description="Learn Java",
        ))
        tasks, total = await list_tasks(db_session, search="Python")
        assert total == 1

    async def test_list_tasks_search_case_insensitive(self, db_session):
        await create_task(db_session, TaskCreate(title="PYTHON"))
        tasks, total = await list_tasks(db_session, search="python")
        assert total == 1

    async def test_list_tasks_pagination(self, db_session):
        for i in range(10):
            await create_task(db_session, TaskCreate(title=f"T{i}"))
        tasks, total = await list_tasks(db_session, page=1, page_size=3)
        assert total == 10
        assert len(tasks) == 3

    async def test_list_tasks_pagination_page2(self, db_session):
        for i in range(5):
            await create_task(db_session, TaskCreate(title=f"T{i}"))
        tasks, total = await list_tasks(db_session, page=2, page_size=3)
        assert len(tasks) == 2  # 5 total, page_size=3, page 2 has 2

    async def test_list_tasks_sort_by_title_asc(self, db_session):
        await create_task(db_session, TaskCreate(title="C"))
        await create_task(db_session, TaskCreate(title="A"))
        await create_task(db_session, TaskCreate(title="B"))
        tasks, _ = await list_tasks(db_session, sort_by="title", sort_order="asc")
        titles = [t.title for t in tasks]
        assert titles == ["A", "B", "C"]

    async def test_list_tasks_sort_by_title_desc(self, db_session):
        await create_task(db_session, TaskCreate(title="C"))
        await create_task(db_session, TaskCreate(title="A"))
        await create_task(db_session, TaskCreate(title="B"))
        tasks, _ = await list_tasks(db_session, sort_by="title", sort_order="desc")
        titles = [t.title for t in tasks]
        assert titles == ["C", "B", "A"]

    async def test_list_tasks_default_sort_desc(self, db_session):
        t1 = await create_task(db_session, TaskCreate(title="First"))
        t2 = await create_task(db_session, TaskCreate(title="Second"))
        tasks, _ = await list_tasks(db_session)
        # 默认 created_at desc，最后创建的排前面
        assert tasks[0].id == t2.id
        assert tasks[1].id == t1.id

    async def test_list_tasks_date_range_filter(self, db_session):
        await create_task(db_session, TaskCreate(
            title="Early",
            due_date=datetime(2025, 1, 15, tzinfo=timezone.utc),
        ))
        await create_task(db_session, TaskCreate(
            title="Late",
            due_date=datetime(2025, 12, 15, tzinfo=timezone.utc),
        ))
        tasks, total = await list_tasks(
            db_session,
            due_date_from=datetime(2025, 6, 1, tzinfo=timezone.utc),
            due_date_to=datetime(2025, 12, 31, tzinfo=timezone.utc),
        )
        assert total == 1
        assert tasks[0].title == "Late"

    async def test_list_tasks_created_at_range_filter(self, db_session):
        # 创建任务后使用其 created_at 进行范围查询
        t1 = await create_task(db_session, TaskCreate(title="T1"))
        from datetime import timedelta
        past = t1.created_at - timedelta(days=1)
        future = t1.created_at + timedelta(days=1)
        tasks, total = await list_tasks(
            db_session,
            created_at_from=past,
            created_at_to=future,
        )
        assert total == 1

    async def test_list_tasks_sort_by_priority(self, db_session):
        await create_task(db_session, TaskCreate(title="L", priority="low"))
        await create_task(db_session, TaskCreate(title="H", priority="high"))
        await create_task(db_session, TaskCreate(title="M", priority="medium"))
        tasks, _ = await list_tasks(db_session, sort_by="priority", sort_order="asc")
        priorities = [t.priority for t in tasks]
        assert priorities == sorted(priorities)

    async def test_list_tasks_invalid_sort_field_defaults(self, db_session):
        """sort_by 不存在时，getattr 默认回退到 created_at"""
        await create_task(db_session, TaskCreate(title="T"))
        tasks, total = await list_tasks(db_session, sort_by="nonexistent")
        # 不会报错，但使用 created_at 列
        assert total == 1

    async def test_list_tasks_combined_filters(self, db_session):
        await create_task(db_session, TaskCreate(
            title="Match", status="todo", priority="high",
        ))
        await create_task(db_session, TaskCreate(
            title="Nope", status="done", priority="high",
        ))
        tasks, total = await list_tasks(
            db_session, status=["todo"], priority=["high"],
        )
        assert total == 1
        assert tasks[0].title == "Match"
