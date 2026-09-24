"""Service-level tests for depots."""
import pytest

from app.errors import ConflictError, NotFoundError, ValidationError
from app.services import depot_service as service
from tests.factories import make_depot, valid_depot_data


def test_create_and_get_depot():
    item = make_depot()
    fetched = service.get(item.id)
    assert fetched.id == item.id
    assert fetched.depot_code == item.depot_code
    assert fetched.created_at and fetched.updated_at


def test_list_depots_returns_a_page():
    make_depot()
    make_depot()
    page = service.list_(limit=10)
    assert page["total"] >= 2
    assert len(page["items"]) >= 2
    assert page["limit"] == 10


def test_list_depots_pagination():
    for _ in range(3):
        make_depot()
    first_page = service.list_(limit=2, offset=0)
    second_page = service.list_(limit=2, offset=2)
    first_ids = {i["id"] for i in first_page["items"]}
    second_ids = {i["id"] for i in second_page["items"]}
    assert first_ids.isdisjoint(second_ids)


def test_count_depots():
    before = service.count()
    make_depot()
    assert service.count() == before + 1


def test_update_depot_name():
    item = make_depot()
    updated = service.update(item.id, {"name": "Updated value"})
    assert updated.name == "Updated value"


def test_update_depot_with_nothing_changes_nothing():
    item = make_depot()
    same = service.update(item.id, {})
    assert same.name == item.name


def test_update_missing_depot_raises():
    with pytest.raises(NotFoundError):
        service.update(999_999, {})


def test_delete_depot():
    item = make_depot()
    service.delete(item.id)
    with pytest.raises(NotFoundError):
        service.get(item.id)


def test_delete_missing_depot_raises():
    with pytest.raises(NotFoundError):
        service.delete(999_999)


def test_get_missing_depot_raises():
    with pytest.raises(NotFoundError):
        service.get(999_999)


def test_depot_requires_depot_code():
    data = valid_depot_data()
    data.pop("depot_code")
    with pytest.raises(ValidationError) as exc:
        service.create(data)
    assert "depot_code" in exc.value.errors


def test_depot_duplicate_depot_code_conflicts():
    item = make_depot()
    with pytest.raises(ConflictError):
        service.create(valid_depot_data(depot_code=item.depot_code))


def test_depot_depot_code_too_long():
    with pytest.raises(ValidationError):
        service.create(valid_depot_data(depot_code="x" * 21))


def test_depot_requires_name():
    data = valid_depot_data()
    data.pop("name")
    with pytest.raises(ValidationError) as exc:
        service.create(data)
    assert "name" in exc.value.errors


def test_depot_name_too_long():
    with pytest.raises(ValidationError):
        service.create(valid_depot_data(name="x" * 201))


def test_depot_area_too_long():
    with pytest.raises(ValidationError):
        service.create(valid_depot_data(area="x" * 201))


def test_depot_capacity_below_minimum():
    with pytest.raises(ValidationError):
        service.create(valid_depot_data(capacity=0))


def test_depot_capacity_above_maximum():
    with pytest.raises(ValidationError):
        service.create(valid_depot_data(capacity=1001))


def test_depot_capacity_rejects_text():
    with pytest.raises(ValidationError):
        service.create(valid_depot_data(capacity="abc"))


def test_depot_latitude_below_minimum():
    with pytest.raises(ValidationError):
        service.create(valid_depot_data(latitude=-90.5))


def test_depot_latitude_above_maximum():
    with pytest.raises(ValidationError):
        service.create(valid_depot_data(latitude=90.5))


def test_depot_latitude_rejects_text():
    with pytest.raises(ValidationError):
        service.create(valid_depot_data(latitude="abc"))


def test_depot_longitude_below_minimum():
    with pytest.raises(ValidationError):
        service.create(valid_depot_data(longitude=-180.5))


def test_depot_longitude_above_maximum():
    with pytest.raises(ValidationError):
        service.create(valid_depot_data(longitude=180.5))


def test_depot_longitude_rejects_text():
    with pytest.raises(ValidationError):
        service.create(valid_depot_data(longitude="abc"))


def test_depot_is_active_must_be_boolean():
    with pytest.raises(ValidationError):
        service.create(valid_depot_data(is_active="yes"))


def test_search_depots_by_text():
    item = make_depot(name="Zebra Crossing Special")
    page = service.list_({"q": "Zebra Crossing"})
    assert any(i["id"] == item.id for i in page["items"])


def test_export_depots_csv():
    make_depot()
    text = service.export_csv()
    header = text.splitlines()[0]
    assert header.startswith("id,")
    assert "depot_code" in header
    assert len(text.splitlines()) >= 2


def test_bulk_create_depots():
    before = service.count()
    created = service.bulk_create([valid_depot_data(), valid_depot_data()])
    assert len(created) == 2
    assert service.count() == before + 2


def test_bulk_create_depots_is_all_or_nothing():
    before = service.count()
    bad = valid_depot_data()
    bad.pop("depot_code")
    with pytest.raises(ValidationError):
        service.bulk_create([valid_depot_data(), bad])
    assert service.count() == before
