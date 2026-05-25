from datetime import datetime, timezone
from typing import Any, Optional, List
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from task_api.models import Task
from task_api.schemas import TaskCreate


async def create_task(session: AsyncSession, task_data: TaskCreate) -> Task:
    task = Task(**task_data.model_dump())
    session.add(task)
    await session.commit()
    await session.refresh(task)
    return task


async def get_task(session: AsyncSession, task_id: int) -> Optional[Task]:
    result = await session.execute(select(Task).where(Task.id == task_id))
    return result.scalar_one_or_none()


async def update_task(
    session: AsyncSession, task: Task, update_data: dict
) -> Task:
    for field, value in update_data.items():
        setattr(task, field, value)
    task.updated_at = datetime.now(timezone.utc)
    await session.commit()
    await session.refresh(task)
    return task


async def delete_task(session: AsyncSession, task: Task) -> None:
    await session.delete(task)
    await session.commit()


async def list_tasks(
    session: AsyncSession,
    *,
    status: Optional[List[str]] = None,
    priority: Optional[List[str]] = None,
    due_date_from: Optional[datetime] = None,
    due_date_to: Optional[datetime] = None,
    created_at_from: Optional[datetime] = None,
    created_at_to: Optional[datetime] = None,
    search: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    sort_by: str = "created_at",
    sort_order: str = "desc",
) -> tuple[list[Task], int]:
    query = select(Task)

    if status:
        query = query.where(Task.status.in_(status))
    if priority:
        query = query.where(Task.priority.in_(priority))
    if due_date_from:
        query = query.where(Task.due_date >= due_date_from)
    if due_date_to:
        query = query.where(Task.due_date <= due_date_to)
    if created_at_from:
        query = query.where(Task.created_at >= created_at_from)
    if created_at_to:
        query = query.where(Task.created_at <= created_at_to)
    if search:
        query = query.where(
            or_(
                Task.title.ilike(f"%{search}%"),
                Task.description.ilike(f"%{search}%"),
            )
        )

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await session.execute(count_query)
    total = total_result.scalar_one()

    sort_column = getattr(Task, sort_by, Task.created_at)
    if sort_order.lower() == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    result = await session.execute(query)
    tasks = result.scalars().all()
    return list(tasks), total
