"""
测试公共 fixtures：异步 SQLite 内存数据库 + HTTP 测试客户端
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from task_api.database import Base, get_db_session
from task_api.main import app


# ──────────────────────────────────────────────
# 引擎 & 数据库会话
# ──────────────────────────────────────────────

@pytest_asyncio.fixture
async def test_engine():
    """每个测试函数创建独立的内存 SQLite 引擎，测试结束后销毁。"""
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine):
    """提供直连数据库会话，用于 CRUD / Service 层单元测试。"""
    TestSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False)
    async with TestSessionLocal() as session:
        yield session


# ──────────────────────────────────────────────
# HTTP 测试客户端（集成测试用）
# ──────────────────────────────────────────────

@pytest_asyncio.fixture
async def client(test_engine):
    """提供异步 HTTP 测试客户端，自动替换数据库依赖。"""
    TestSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False)

    async def override_get_db_session():
        async with TestSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db_session] = override_get_db_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


# ──────────────────────────────────────────────
# 测试数据辅助
# ──────────────────────────────────────────────

@pytest_asyncio.fixture
async def sample_task(client):
    """创建一个示例任务，返回其 JSON 响应数据。"""
    response = await client.post("/api/v1/tasks", json={
        "title": "Sample Task",
        "description": "A sample task for testing",
        "status": "todo",
        "priority": "medium",
    })
    assert response.status_code == 201
    return response.json()


@pytest_asyncio.fixture
async def multiple_tasks(client):
    """创建 5 个不同状态/优先级的任务，用于列表查询测试。"""
    tasks_data = [
        {"title": "Alpha Task", "status": "todo", "priority": "high",
         "description": "First task"},
        {"title": "Beta Task", "status": "in_progress", "priority": "medium",
         "description": "Second task"},
        {"title": "Gamma Task", "status": "done", "priority": "low",
         "description": "Third task"},
        {"title": "Delta Task", "status": "todo", "priority": "low",
         "description": "Python programming task"},
        {"title": "Epsilon Task", "status": "in_progress", "priority": "high",
         "description": "Fifth task", "due_date": "2025-12-31T23:59:59Z"},
    ]
    created = []
    for data in tasks_data:
        resp = await client.post("/api/v1/tasks", json=data)
        assert resp.status_code == 201
        created.append(resp.json())
    return created
