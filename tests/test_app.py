import pytest
from httpx import AsyncClient



@pytest.mark.asyncio
async def test_openapi_available(client: AsyncClient):
    """Проверяет доступность схемы API."""

    response = await client.get("/openapi.json")

    assert response.status_code == 200
    assert "paths" in response.json()






