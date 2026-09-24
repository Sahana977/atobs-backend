"""Service-level tests for trips."""
import pytest

from app.errors import ConflictError, NotFoundError, ValidationError
from app.services import trip_service as service
from tests.factories import make_trip, valid_trip_data


def test_create_and_get_trip():
    item = make_trip()
    fetched = service.get(item.id)
    assert fetched.id == item.id
    assert fetched.trip_code == item.trip_code
    assert fetched.created_at and fetched.updated_at


def test_list_trips_returns_a_page():
    make_trip()
    make_trip()
    page = service.list_(limit=10)
    assert page["total"] >= 2
    assert len(page["items"]) >= 2
    assert page["limit"] == 10


def test_list_trips_pagination():
    for _ in range(3):
        make_trip()
    first_page = service.list_(limit=2, offset=0)
    second_page = service.list_(limit=2, offset=2)
    first_ids = {i["id"] for i in first_page["items"]}
    second_ids = {i["id"] for i in second_page["items"]}
    assert first_ids.isdisjoint(second_ids)


def test_count_trips():
    before = service.count()
    make_trip()
    assert service.count() == before + 1


def test_update_trip_status():
    item = make_trip()
    updated = service.update(item.id, {"status": 'cancelled'})
    assert updated.status == 'cancelled'


def test_update_trip_with_nothing_changes_nothing():
    item = make_trip()
    same = service.update(item.id, {})
    assert same.status == item.status


def test_update_missing_trip_raises():
    with pytest.raises(NotFoundError):
        service.update(999_999, {})


def test_delete_trip():
    item = make_trip()
    service.delete(item.id)
    with pytest.raises(NotFoundError):
        service.get(item.id)


def test_delete_missing_trip_raises():
    with pytest.raises(NotFoundError):
        service.delete(999_999)


def test_get_missing_trip_raises():
    with pytest.raises(NotFoundError):
        service.get(999_999)


def test_trip_requires_trip_code():
    data = valid_trip_data()
    data.pop("trip_code")
    with pytest.raises(ValidationError) as exc:
        service.create(data)
    assert "trip_code" in exc.value.errors


def test_trip_duplicate_trip_code_conflicts():
    item = make_trip()
    with pytest.raises(ConflictError):
        service.create(valid_trip_data(trip_code=item.trip_code))


def test_trip_trip_code_too_long():
    with pytest.raises(ValidationError):
        service.create(valid_trip_data(trip_code="x" * 31))


def test_trip_requires_route_id():
    data = valid_trip_data()
    data.pop("route_id")
    with pytest.raises(ValidationError) as exc:
        service.create(data)
    assert "route_id" in exc.value.errors


def test_trip_unknown_route_id_rejected():
    with pytest.raises(ValidationError) as exc:
        service.create(valid_trip_data(route_id=999_999))
    assert "route_id" in exc.value.errors


def test_trip_requires_bus_id():
    data = valid_trip_data()
    data.pop("bus_id")
    with pytest.raises(ValidationError) as exc:
        service.create(data)
    assert "bus_id" in exc.value.errors


def test_trip_unknown_bus_id_rejected():
    with pytest.raises(ValidationError) as exc:
        service.create(valid_trip_data(bus_id=999_999))
    assert "bus_id" in exc.value.errors


def test_trip_requires_scheduled_start():
    data = valid_trip_data()
    data.pop("scheduled_start")
    with pytest.raises(ValidationError) as exc:
        service.create(data)
    assert "scheduled_start" in exc.value.errors


def test_trip_rejects_bad_scheduled_start():
    with pytest.raises(ValidationError):
        service.create(valid_trip_data(scheduled_start="not-a-date"))


def test_trip_rejects_bad_scheduled_end():
    with pytest.raises(ValidationError):
        service.create(valid_trip_data(scheduled_end="not-a-date"))


def test_trip_rejects_invalid_status():
    with pytest.raises(ValidationError):
        service.create(valid_trip_data(status="not-a-valid-choice"))


def test_export_trips_csv():
    make_trip()
    text = service.export_csv()
    header = text.splitlines()[0]
    assert header.startswith("id,")
    assert "trip_code" in header
    assert len(text.splitlines()) >= 2


def test_bulk_create_trips():
    before = service.count()
    created = service.bulk_create([valid_trip_data(), valid_trip_data()])
    assert len(created) == 2
    assert service.count() == before + 2


def test_bulk_create_trips_is_all_or_nothing():
    before = service.count()
    bad = valid_trip_data()
    bad.pop("trip_code")
    with pytest.raises(ValidationError):
        service.bulk_create([valid_trip_data(), bad])
    assert service.count() == before


def test_trip_end_must_be_after_start():
    data = valid_trip_data(scheduled_start="2026-10-01T09:00:00", scheduled_end="2026-10-01T08:00:00")
    with pytest.raises(ValidationError):
        service.create(data)
