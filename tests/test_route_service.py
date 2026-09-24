"""Service-level tests for routes."""
import pytest

from app.errors import ConflictError, NotFoundError, ValidationError
from app.services import route_service as service
from tests.factories import make_route, make_stop, valid_route_data


def test_create_and_get_route():
    item = make_route()
    fetched = service.get(item.id)
    assert fetched.id == item.id
    assert fetched.route_number == item.route_number
    assert fetched.created_at and fetched.updated_at


def test_list_routes_returns_a_page():
    make_route()
    make_route()
    page = service.list_(limit=10)
    assert page["total"] >= 2
    assert len(page["items"]) >= 2
    assert page["limit"] == 10


def test_list_routes_pagination():
    for _ in range(3):
        make_route()
    first_page = service.list_(limit=2, offset=0)
    second_page = service.list_(limit=2, offset=2)
    first_ids = {i["id"] for i in first_page["items"]}
    second_ids = {i["id"] for i in second_page["items"]}
    assert first_ids.isdisjoint(second_ids)


def test_count_routes():
    before = service.count()
    make_route()
    assert service.count() == before + 1


def test_update_route_name():
    item = make_route()
    updated = service.update(item.id, {"name": "Updated value"})
    assert updated.name == "Updated value"


def test_update_route_with_nothing_changes_nothing():
    item = make_route()
    same = service.update(item.id, {})
    assert same.name == item.name


def test_update_missing_route_raises():
    with pytest.raises(NotFoundError):
        service.update(999_999, {})


def test_delete_route():
    item = make_route()
    service.delete(item.id)
    with pytest.raises(NotFoundError):
        service.get(item.id)


def test_delete_missing_route_raises():
    with pytest.raises(NotFoundError):
        service.delete(999_999)


def test_get_missing_route_raises():
    with pytest.raises(NotFoundError):
        service.get(999_999)


def test_route_requires_route_number():
    data = valid_route_data()
    data.pop("route_number")
    with pytest.raises(ValidationError) as exc:
        service.create(data)
    assert "route_number" in exc.value.errors


def test_route_duplicate_route_number_conflicts():
    item = make_route()
    with pytest.raises(ConflictError):
        service.create(valid_route_data(route_number=item.route_number))


def test_route_route_number_too_long():
    with pytest.raises(ValidationError):
        service.create(valid_route_data(route_number="x" * 21))


def test_route_requires_name():
    data = valid_route_data()
    data.pop("name")
    with pytest.raises(ValidationError) as exc:
        service.create(data)
    assert "name" in exc.value.errors


def test_route_name_too_long():
    with pytest.raises(ValidationError):
        service.create(valid_route_data(name="x" * 201))


def test_route_requires_origin_stop_id():
    data = valid_route_data()
    data.pop("origin_stop_id")
    with pytest.raises(ValidationError) as exc:
        service.create(data)
    assert "origin_stop_id" in exc.value.errors


def test_route_unknown_origin_stop_id_rejected():
    with pytest.raises(ValidationError) as exc:
        service.create(valid_route_data(origin_stop_id=999_999))
    assert "origin_stop_id" in exc.value.errors


def test_route_requires_destination_stop_id():
    data = valid_route_data()
    data.pop("destination_stop_id")
    with pytest.raises(ValidationError) as exc:
        service.create(data)
    assert "destination_stop_id" in exc.value.errors


def test_route_unknown_destination_stop_id_rejected():
    with pytest.raises(ValidationError) as exc:
        service.create(valid_route_data(destination_stop_id=999_999))
    assert "destination_stop_id" in exc.value.errors


def test_route_requires_distance_km():
    data = valid_route_data()
    data.pop("distance_km")
    with pytest.raises(ValidationError) as exc:
        service.create(data)
    assert "distance_km" in exc.value.errors


def test_route_distance_km_below_minimum():
    with pytest.raises(ValidationError):
        service.create(valid_route_data(distance_km=-0.4))


def test_route_distance_km_above_maximum():
    with pytest.raises(ValidationError):
        service.create(valid_route_data(distance_km=200.5))


def test_route_distance_km_rejects_text():
    with pytest.raises(ValidationError):
        service.create(valid_route_data(distance_km="abc"))


def test_route_rejects_invalid_service_type():
    with pytest.raises(ValidationError):
        service.create(valid_route_data(service_type="not-a-valid-choice"))


def test_route_avg_headway_min_below_minimum():
    with pytest.raises(ValidationError):
        service.create(valid_route_data(avg_headway_min=0))


def test_route_avg_headway_min_above_maximum():
    with pytest.raises(ValidationError):
        service.create(valid_route_data(avg_headway_min=181))


def test_route_avg_headway_min_rejects_text():
    with pytest.raises(ValidationError):
        service.create(valid_route_data(avg_headway_min="abc"))


def test_route_is_active_must_be_boolean():
    with pytest.raises(ValidationError):
        service.create(valid_route_data(is_active="yes"))


def test_search_routes_by_text():
    item = make_route(name="Zebra Crossing Special")
    page = service.list_({"q": "Zebra Crossing"})
    assert any(i["id"] == item.id for i in page["items"])


def test_export_routes_csv():
    make_route()
    text = service.export_csv()
    header = text.splitlines()[0]
    assert header.startswith("id,")
    assert "route_number" in header
    assert len(text.splitlines()) >= 2


def test_bulk_create_routes():
    before = service.count()
    created = service.bulk_create([valid_route_data(), valid_route_data()])
    assert len(created) == 2
    assert service.count() == before + 2


def test_bulk_create_routes_is_all_or_nothing():
    before = service.count()
    bad = valid_route_data()
    bad.pop("route_number")
    with pytest.raises(ValidationError):
        service.bulk_create([valid_route_data(), bad])
    assert service.count() == before


def test_route_origin_and_destination_must_differ():
    stop = make_stop()
    data = valid_route_data(origin_stop_id=stop.id, destination_stop_id=stop.id)
    with pytest.raises(ValidationError):
        service.create(data)
