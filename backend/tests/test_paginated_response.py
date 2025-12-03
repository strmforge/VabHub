from app.core.schemas import PaginatedResponse


def test_paginated_response_meta():
    payload = PaginatedResponse.create(
        items=[{"id": 1}],
        total=1,
        page=1,
        page_size=10,
        meta={"simulation_mode": True},
    )

    assert payload.meta == {"simulation_mode": True}
    assert payload.total_pages == 1

