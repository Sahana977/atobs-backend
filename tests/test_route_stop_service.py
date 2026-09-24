"""Service-level tests for route stops."""
import pytest

from app.errors import ConflictError, NotFoundError, ValidationError
from app.services import route_stop_service as service
from tests.factories import make_route_stop, valid_route_stop_data


def test_create_and_get_route_stop():
    item = make_route_stop()
    fetched = service.get(item.id)
    assert fetched.id == item.id
    assert fetched.route_id == item.route_id
    assert fetched.created_at and fetched.updated_at


def test_list_route_stops_returns_a_page():
    make_route_stop()
    make_route_stop()
    page = service.list_(limit=10)
    assert page["total"] >= 2
    assert len(page["items"]) >= 2
    assert page["limit"] == 10


def test_list_route_stops_pagination():
    for _ in range(3):
        make_route_stop()
    first_page = service.list_(limit=2, offset=0)
    second_page = service.list_(limit=2, offset=2)
    first_ids = {i["id"] for i in first_page["items"]}
    second_ids = {i["id"] for i in second_page["items"]}
    assert first_ids.isdisjoint(second_ids)


def test_count_route_stops():
    before = service.count()
    make_route_stop()
    assert service.count() == before + 1


def test_update_route_stop_sequence():
    item = make_route_stop()
    updated = service.update(item.id, {"sequence": 200})
    assert updated.sequence == 200


def test_update_route_stop_with_nothing_changes_nothing():
    item = make_route_stop()
    same = service.update(item.id, {})
    assert same.sequence == item.sequence


def test_update_missing_route_stop_raises():
    with pytest.raises(NotFoundError):
        service.update(999_999, {})


def test_delete_route_stop():
    item = make_route_stop()
    service.delete(item.id)
    with pytest.raises(NotFoundError):
        service.get(item.id)


def test_delete_missing_route_stop_raises():
    with pytest.raises(NotFoundError):
        service.delete(999_999)


def test_get_missing_route_stop_raises():
    with pytest.raises(NotFoundError):
        service.get(999_999)


def test_route_stop_requires_route_id():
    data = valid_route_stop_data()
    data.pop("route_id")
    with pytest.raises(ValidationError) as exc:
        service.create(data)
    assert "route_id" in exc.value.errors


def test_route_stop_unknown_route_id_rejected():
    with pytest.raises(ValidationError) as exc:
        service.create(valid_route_stop_data(route_id=999_999))
    assert "route_id" in exc.value.errors


def test_route_stop_requires_stop_id():
    data = valid_route_stop_data()
    data.pop("stop_id")
    with pytest.raises(ValidationError) as exc:
        service.create(data)
    assert "stop_id" in exc.value.errors


def test_route_stop_unknown_stop_id_rejected():
    with pytest.raises(ValidationError) as exc:
        service.create(valid_route_stop_data(stop_id=999_999))
    assert "stop_id" in exc.value.errors


def test_route_stop_requires_sequence():
    data = valid_route_stop_data()
    data.pop("sequence")
    with pytest.raises(ValidationError) as exc:
        service.create(data)
    assert "sequence" in exc.value.errors


def test_route_stop_sequence_below_minimum():
    with pytest.raises(ValidationError):
        service.create(valid_route_stop_data(sequence=0))


def test_route_stop_sequence_above_maximum():
    with pytest.raises(ValidationError):
        service.create(valid_route_stop_data(sequence=201))


def test_route_stop_sequence_rejects_text():
    with pytest.raises(ValidationError):
        service.create(valid_route_stop_data(sequence="abc"))


def test_route_stop_minutes_from_start_below_minimum():
    with pytest.raises(ValidationError):
        service.create(valid_route_stop_data(minutes_from_start=-0.5))


def test_route_stop_minutes_from_start_above_maximum():
    with pytest.raises(ValidationError):
        service.create(valid_route_stop_data(minutes_from_start=600.5))


def test_route_stop_minutes_from_start_rejects_text():
    with pytest.raises(ValidationError):
        service.create(valid_route_stop_data(minutes_from_start="abc"))


def test_export_route_stops_csv():
    make_route_stop()
    text = service.export_csv()
    header = text.splitlines()[0]
    assert header.startswith("id,")
    assert "route_id" in header
    assert len(text.splitlines()) >= 2


def test_bulk_create_route_stops():
    before = service.count()
    created = service.bulk_create([valid_route_stop_data(), valid_route_stop_data()])
    assert len(created) == 2
    assert service.count() == before + 2


def test_bulk_create_route_stops_is_all_or_nothing():
    before = service.count()
    bad = valid_route_stop_data()
    bad.pop("route_id")
    with pytest.raises(ValidationError):
        service.bulk_create([valid_route_stop_data(), bad])
    assert service.count() == before
