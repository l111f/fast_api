from math import ceil
from typing import Optional
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from task_api import crud
from task_api.schemas import (
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskListResponse,
    PaginationMeta,
)


async def create_task_service(session: AsyncSession, task_create: TaskCreate) -> TaskResponse:
    task = await crud.create_task(session, task_create)
    return TaskResponse.model_validate(task)


async def get_task_service(session: AsyncSession, task_id: int) -> TaskResponse:
    task = await crud.get_task(session, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="任务未找到")
    return TaskResponse.model_validate(task)


async def update_task_service(
    session: AsyncSession, task_id: int, task_update: TaskUpdate
) -> TaskResponse:
    task = await crud.get_task(session, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="任务未找到")
    update_data = task_update.model_dump(exclude_unset=True)
    if not update_data:
        return TaskResponse.model_validate(task)
    task = await crud.update_task(session, task, update_data)
    return TaskResponse.model_validate(task)


async def delete_task_service(session: AsyncSession, task_id: int) -> None:
    task = await crud.get_task(session, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="任务未找到")
    await crud.delete_task(session, task)


class ListTasksQueryParams:
    def __init__(
        self,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        due_date_from: Optional[str] = None,
        due_date_to: Optional[str] = None,
        created_at_from: Optional[str] = None,
        created_at_to: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ):
        self.status = status.split(",") if status else None
        self.priority = priority.split(",") if priority else None
        self.due_date_from = due_date_from
        self.due_date_to = due_date_to
        self.created_at_from = created_at_from
        self.created_at_to = created_at_to
        self.search = search
        self.page = page
        self.page_size = page_size
        self.sort_by = sort_by
        self.sort_order = sort_order


ALLOWED_SORT_FIELDS = {
    "title",
    "status",
    "priority",
    "due_date",
    "created_at",
    "updated_at",
}


async def list_tasks_service(
    session: AsyncSession, query: ListTasksQueryParams
) -> TaskListResponse:
    if query.page < 1:
        raise HTTPException(status_code=422, detail="page 参数必须大于等于 1")
    if query.page_size < 1 or query.page_size > 100:
        raise HTTPException(status_code=422, detail="page_size 参数必须在 1~100 之间")
    if query.sort_by not in ALLOWED_SORT_FIELDS:
        raise HTTPException(status_code=422, detail=f"sort_by 参数非法，允许值为: {', '.join(ALLOWED_SORT_FIELDS)}")

    from datetime import datetime

    def _parse_dt(value: Optional[str]) -> Optional[datetime]:
        if value is None:
            return None
        return datetime.fromisoformat(value.replace("Z", "+00:00"))

    tasks, total = await crud.list_tasks(
        session,
        status=query.status,
        priority=query.priority,
        due_date_from=_parse_dt(query.due_date_from),
        due_date_to=_parse_dt(query.due_date_to),
        created_at_from=_parse_dt(query.created_at_from),
        created_at_to=_parse_dt(query.created_at_to),
        search=query.search,
        page=query.page,
        page_size=query.page_size,
        sort_by=query.sort_by,
        sort_order=query.sort_order,
    )

    total_pages = ceil(total / query.page_size) if total > 0 else 1
    return TaskListResponse(
        items=[TaskResponse.model_validate(t) for t in tasks],
        pagination=PaginationMeta(
            page=query.page,
            page_size=query.page_size,
            total=total,
            total_pages=total_pages,
        ),
    )
