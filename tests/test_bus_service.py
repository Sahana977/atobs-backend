"""Service-level tests for buses."""
import pytest

from app.errors import ConflictError, NotFoundError, ValidationError
from app.services import bus_service as service
from tests.factories import make_bus, valid_bus_data


def test_create_and_get_bus():
    item = make_bus()
    fetched = service.get(item.id)
    assert fetched.id == item.id
    assert fetched.registration_no == item.registration_no
    assert fetched.created_at and fetched.updated_at


def test_list_buss_returns_a_page():
    make_bus()
    make_bus()
    page = service.list_(limit=10)
    assert page["total"] >= 2
    assert len(page["items"]) >= 2
    assert page["limit"] == 10


def test_list_buss_pagination():
    for _ in range(3):
        make_bus()
    first_page = service.list_(limit=2, offset=0)
    second_page = service.list_(limit=2, offset=2)
    first_ids = {i["id"] for i in first_page["items"]}
    second_ids = {i["id"] for i in second_page["items"]}
    assert first_ids.isdisjoint(second_ids)


def test_count_buss():
    before = service.count()
    make_bus()
    assert service.count() == before + 1


def test_update_bus_capacity():
    item = make_bus()
    updated = service.update(item.id, {"capacity": 150})
    assert updated.capacity == 150


def test_update_bus_with_nothing_changes_nothing():
    item = make_bus()
    same = service.update(item.id, {})
    assert same.capacity == item.capacity


def test_update_missing_bus_raises():
    with pytest.raises(NotFoundError):
        service.update(999_999, {})


def test_delete_bus():
    item = make_bus()
    service.delete(item.id)
    with pytest.raises(NotFoundError):
        service.get(item.id)


def test_delete_missing_bus_raises():
    with pytest.raises(NotFoundError):
        service.delete(999_999)


def test_get_missing_bus_raises():
    with pytest.raises(NotFoundError):
        service.get(999_999)


def test_bus_requires_registration_no():
    data = valid_bus_data()
    data.pop("registration_no")
    with pytest.raises(ValidationError) as exc:
        service.create(data)
    assert "registration_no" in exc.value.errors


def test_bus_duplicate_registration_no_conflicts():
    item = make_bus()
    with pytest.raises(ConflictError):
        service.create(valid_bus_data(registration_no=item.registration_no))


def test_bus_registration_no_too_long():
    with pytest.raises(ValidationError):
        service.create(valid_bus_data(registration_no="x" * 21))


def test_bus_requires_depot_id():
    data = valid_bus_data()
    data.pop("depot_id")
    with pytest.raises(ValidationError) as exc:
        service.create(data)
    assert "depot_id" in exc.value.errors


def test_bus_unknown_depot_id_rejected():
    with pytest.raises(ValidationError) as exc:
        service.create(valid_bus_data(depot_id=999_999))
    assert "depot_id" in exc.value.errors


def test_bus_capacity_below_minimum():
    with pytest.raises(ValidationError):
        service.create(valid_bus_data(capacity=9))


def test_bus_capacity_above_maximum():
    with pytest.raises(ValidationError):
        service.create(valid_bus_data(capacity=151))


def test_bus_capacity_rejects_text():
    with pytest.raises(ValidationError):
        service.create(valid_bus_data(capacity="abc"))


def test_bus_rejects_invalid_bus_type():
    with pytest.raises(ValidationError):
        service.create(valid_bus_data(bus_type="not-a-valid-choice"))


def test_bus_manufacture_year_below_minimum():
    with pytest.raises(ValidationError):
        service.create(valid_bus_data(manufacture_year=1989))


def test_bus_manufacture_year_above_maximum():
    with pytest.raises(ValidationError):
        service.create(valid_bus_data(manufacture_year=2031))


def test_bus_manufacture_year_rejects_text():
    with pytest.raises(ValidationError):
        service.create(valid_bus_data(manufacture_year="abc"))


def test_bus_is_operational_must_be_boolean():
    with pytest.raises(ValidationError):
        service.create(valid_bus_data(is_operational="yes"))


def test_export_buss_csv():
    make_bus()
    text = service.export_csv()
    header = text.splitlines()[0]
    assert header.startswith("id,")
    assert "registration_no" in header
    assert len(text.splitlines()) >= 2


def test_bulk_create_buss():
    before = service.count()
    created = service.bulk_create([valid_bus_data(), valid_bus_data()])
    assert len(created) == 2
    assert service.count() == before + 2


def test_bulk_create_buss_is_all_or_nothing():
    before = service.count()
    bad = valid_bus_data()
    bad.pop("registration_no")
    with pytest.raises(ValidationError):
        service.bulk_create([valid_bus_data(), bad])
    assert service.count() == before
