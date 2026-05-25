from typing import Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from task_api.database import get_db_session
from task_api.schemas import TaskCreate, TaskUpdate, TaskResponse, TaskListResponse
from task_api.services import (
    create_task_service,
    get_task_service,
    update_task_service,
    delete_task_service,
    list_tasks_service,
    ListTasksQueryParams,
)

router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])


def parse_list_query_params(
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
) -> ListTasksQueryParams:
    return ListTasksQueryParams(
        status=status,
        priority=priority,
        due_date_from=due_date_from,
        due_date_to=due_date_to,
        created_at_from=created_at_from,
        created_at_to=created_at_to,
        search=search,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_create: TaskCreate,
    session: AsyncSession = Depends(get_db_session),
):
    return await create_task_service(session, task_create)


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    session: AsyncSession = Depends(get_db_session),
):
    return await get_task_service(session, task_id)


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task_put(
    task_id: int,
    task_update: TaskUpdate,
    session: AsyncSession = Depends(get_db_session),
):
    return await update_task_service(session, task_id, task_update)


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task_patch(
    task_id: int,
    task_update: TaskUpdate,
    session: AsyncSession = Depends(get_db_session),
):
    return await update_task_service(session, task_id, task_update)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    session: AsyncSession = Depends(get_db_session),
):
    await delete_task_service(session, task_id)
    return None


@router.get("", response_model=TaskListResponse)
async def list_tasks(
    query: ListTasksQueryParams = Depends(parse_list_query_params),
    session: AsyncSession = Depends(get_db_session),
):
    return await list_tasks_service(session, query)
