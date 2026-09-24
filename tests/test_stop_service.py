"""Service-level tests for stops."""
import pytest

from app.errors import ConflictError, NotFoundError, ValidationError
from app.services import stop_service as service
from tests.factories import make_stop, valid_stop_data


def test_create_and_get_stop():
    item = make_stop()
    fetched = service.get(item.id)
    assert fetched.id == item.id
    assert fetched.stop_code == item.stop_code
    assert fetched.created_at and fetched.updated_at


def test_list_stops_returns_a_page():
    make_stop()
    make_stop()
    page = service.list_(limit=10)
    assert page["total"] >= 2
    assert len(page["items"]) >= 2
    assert page["limit"] == 10


def test_list_stops_pagination():
    for _ in range(3):
        make_stop()
    first_page = service.list_(limit=2, offset=0)
    second_page = service.list_(limit=2, offset=2)
    first_ids = {i["id"] for i in first_page["items"]}
    second_ids = {i["id"] for i in second_page["items"]}
    assert first_ids.isdisjoint(second_ids)


def test_count_stops():
    before = service.count()
    make_stop()
    assert service.count() == before + 1


def test_update_stop_name():
    item = make_stop()
    updated = service.update(item.id, {"name": "Updated value"})
    assert updated.name == "Updated value"


def test_update_stop_with_nothing_changes_nothing():
    item = make_stop()
    same = service.update(item.id, {})
    assert same.name == item.name


def test_update_missing_stop_raises():
    with pytest.raises(NotFoundError):
        service.update(999_999, {})


def test_delete_stop():
    item = make_stop()
    service.delete(item.id)
    with pytest.raises(NotFoundError):
        service.get(item.id)


def test_delete_missing_stop_raises():
    with pytest.raises(NotFoundError):
        service.delete(999_999)


def test_get_missing_stop_raises():
    with pytest.raises(NotFoundError):
        service.get(999_999)


def test_stop_requires_stop_code():
    data = valid_stop_data()
    data.pop("stop_code")
    with pytest.raises(ValidationError) as exc:
        service.create(data)
    assert "stop_code" in exc.value.errors


def test_stop_duplicate_stop_code_conflicts():
    item = make_stop()
    with pytest.raises(ConflictError):
        service.create(valid_stop_data(stop_code=item.stop_code))


def test_stop_stop_code_too_long():
    with pytest.raises(ValidationError):
        service.create(valid_stop_data(stop_code="x" * 21))


def test_stop_requires_name():
    data = valid_stop_data()
    data.pop("name")
    with pytest.raises(ValidationError) as exc:
        service.create(data)
    assert "name" in exc.value.errors


def test_stop_name_too_long():
    with pytest.raises(ValidationError):
        service.create(valid_stop_data(name="x" * 201))


def test_stop_area_too_long():
    with pytest.raises(ValidationError):
        service.create(valid_stop_data(area="x" * 201))


def test_stop_requires_latitude():
    data = valid_stop_data()
    data.pop("latitude")
    with pytest.raises(ValidationError) as exc:
        service.create(data)
    assert "latitude" in exc.value.errors


def test_stop_latitude_below_minimum():
    with pytest.raises(ValidationError):
        service.create(valid_stop_data(latitude=-90.5))


def test_stop_latitude_above_maximum():
    with pytest.raises(ValidationError):
        service.create(valid_stop_data(latitude=90.5))


def test_stop_latitude_rejects_text():
    with pytest.raises(ValidationError):
        service.create(valid_stop_data(latitude="abc"))


def test_stop_requires_longitude():
    data = valid_stop_data()
    data.pop("longitude")
    with pytest.raises(ValidationError) as exc:
        service.create(data)
    assert "longitude" in exc.value.errors


def test_stop_longitude_below_minimum():
    with pytest.raises(ValidationError):
        service.create(valid_stop_data(longitude=-180.5))


def test_stop_longitude_above_maximum():
    with pytest.raises(ValidationError):
        service.create(valid_stop_data(longitude=180.5))


def test_stop_longitude_rejects_text():
    with pytest.raises(ValidationError):
        service.create(valid_stop_data(longitude="abc"))


def test_stop_rejects_invalid_zone():
    with pytest.raises(ValidationError):
        service.create(valid_stop_data(zone="not-a-valid-choice"))


def test_stop_has_shelter_must_be_boolean():
    with pytest.raises(ValidationError):
        service.create(valid_stop_data(has_shelter="yes"))


def test_stop_is_accessible_must_be_boolean():
    with pytest.raises(ValidationError):
        service.create(valid_stop_data(is_accessible="yes"))


def test_search_stops_by_text():
    item = make_stop(name="Zebra Crossing Special")
    page = service.list_({"q": "Zebra Crossing"})
    assert any(i["id"] == item.id for i in page["items"])


def test_export_stops_csv():
    make_stop()
    text = service.export_csv()
    header = text.splitlines()[0]
    assert header.startswith("id,")
    assert "stop_code" in header
    assert len(text.splitlines()) >= 2


def test_bulk_create_stops():
    before = service.count()
    created = service.bulk_create([valid_stop_data(), valid_stop_data()])
    assert len(created) == 2
    assert service.count() == before + 2


def test_bulk_create_stops_is_all_or_nothing():
    before = service.count()
    bad = valid_stop_data()
    bad.pop("stop_code")
    with pytest.raises(ValidationError):
        service.bulk_create([valid_stop_data(), bad])
    assert service.count() == before
