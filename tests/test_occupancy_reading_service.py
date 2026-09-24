"""Service-level tests for occupancy readings."""
import pytest

from app.errors import ConflictError, NotFoundError, ValidationError
from app.services import occupancy_reading_service as service
from tests.factories import make_occupancy_reading, valid_occupancy_reading_data


def test_create_and_get_occupancy_reading():
    item = make_occupancy_reading()
    fetched = service.get(item.id)
    assert fetched.id == item.id
    assert fetched.trip_id == item.trip_id
    assert fetched.created_at and fetched.updated_at


def test_list_occupancy_readings_returns_a_page():
    make_occupancy_reading()
    make_occupancy_reading()
    page = service.list_(limit=10)
    assert page["total"] >= 2
    assert len(page["items"]) >= 2
    assert page["limit"] == 10


def test_list_occupancy_readings_pagination():
    for _ in range(3):
        make_occupancy_reading()
    first_page = service.list_(limit=2, offset=0)
    second_page = service.list_(limit=2, offset=2)
    first_ids = {i["id"] for i in first_page["items"]}
    second_ids = {i["id"] for i in second_page["items"]}
    assert first_ids.isdisjoint(second_ids)


def test_count_occupancy_readings():
    before = service.count()
    make_occupancy_reading()
    assert service.count() == before + 1


def test_update_occupancy_reading_passengers_on_board():
    item = make_occupancy_reading()
    updated = service.update(item.id, {"passengers_on_board": 300})
    assert updated.passengers_on_board == 300


def test_update_occupancy_reading_with_nothing_changes_nothing():
    item = make_occupancy_reading()
    same = service.update(item.id, {})
    assert same.passengers_on_board == item.passengers_on_board


def test_update_missing_occupancy_reading_raises():
    with pytest.raises(NotFoundError):
        service.update(999_999, {})


def test_delete_occupancy_reading():
    item = make_occupancy_reading()
    service.delete(item.id)
    with pytest.raises(NotFoundError):
        service.get(item.id)


def test_delete_missing_occupancy_reading_raises():
    with pytest.raises(NotFoundError):
        service.delete(999_999)


def test_get_missing_occupancy_reading_raises():
    with pytest.raises(NotFoundError):
        service.get(999_999)


def test_occupancy_reading_requires_trip_id():
    data = valid_occupancy_reading_data()
    data.pop("trip_id")
    with pytest.raises(ValidationError) as exc:
        service.create(data)
    assert "trip_id" in exc.value.errors


def test_occupancy_reading_unknown_trip_id_rejected():
    with pytest.raises(ValidationError) as exc:
        service.create(valid_occupancy_reading_data(trip_id=999_999))
    assert "trip_id" in exc.value.errors


def test_occupancy_reading_requires_stop_id():
    data = valid_occupancy_reading_data()
    data.pop("stop_id")
    with pytest.raises(ValidationError) as exc:
        service.create(data)
    assert "stop_id" in exc.value.errors


def test_occupancy_reading_unknown_stop_id_rejected():
    with pytest.raises(ValidationError) as exc:
        service.create(valid_occupancy_reading_data(stop_id=999_999))
    assert "stop_id" in exc.value.errors


def test_occupancy_reading_requires_recorded_at():
    data = valid_occupancy_reading_data()
    data.pop("recorded_at")
    with pytest.raises(ValidationError) as exc:
        service.create(data)
    assert "recorded_at" in exc.value.errors


def test_occupancy_reading_rejects_bad_recorded_at():
    with pytest.raises(ValidationError):
        service.create(valid_occupancy_reading_data(recorded_at="not-a-date"))


def test_occupancy_reading_requires_passengers_on_board():
    data = valid_occupancy_reading_data()
    data.pop("passengers_on_board")
    with pytest.raises(ValidationError) as exc:
        service.create(data)
    assert "passengers_on_board" in exc.value.errors


def test_occupancy_reading_passengers_on_board_below_minimum():
    with pytest.raises(ValidationError):
        service.create(valid_occupancy_reading_data(passengers_on_board=-1))


def test_occupancy_reading_passengers_on_board_above_maximum():
    with pytest.raises(ValidationError):
        service.create(valid_occupancy_reading_data(passengers_on_board=301))


def test_occupancy_reading_passengers_on_board_rejects_text():
    with pytest.raises(ValidationError):
        service.create(valid_occupancy_reading_data(passengers_on_board="abc"))


def test_occupancy_reading_requires_occupancy_pct():
    data = valid_occupancy_reading_data()
    data.pop("occupancy_pct")
    with pytest.raises(ValidationError) as exc:
        service.create(data)
    assert "occupancy_pct" in exc.value.errors


def test_occupancy_reading_occupancy_pct_below_minimum():
    with pytest.raises(ValidationError):
        service.create(valid_occupancy_reading_data(occupancy_pct=-0.5))


def test_occupancy_reading_occupancy_pct_above_maximum():
    with pytest.raises(ValidationError):
        service.create(valid_occupancy_reading_data(occupancy_pct=200.5))


def test_occupancy_reading_occupancy_pct_rejects_text():
    with pytest.raises(ValidationError):
        service.create(valid_occupancy_reading_data(occupancy_pct="abc"))


def test_occupancy_reading_delay_min_below_minimum():
    with pytest.raises(ValidationError):
        service.create(valid_occupancy_reading_data(delay_min=-0.5))


def test_occupancy_reading_delay_min_above_maximum():
    with pytest.raises(ValidationError):
        service.create(valid_occupancy_reading_data(delay_min=180.5))


def test_occupancy_reading_delay_min_rejects_text():
    with pytest.raises(ValidationError):
        service.create(valid_occupancy_reading_data(delay_min="abc"))


def test_occupancy_reading_rejects_invalid_source():
    with pytest.raises(ValidationError):
        service.create(valid_occupancy_reading_data(source="not-a-valid-choice"))


def test_export_occupancy_readings_csv():
    make_occupancy_reading()
    text = service.export_csv()
    header = text.splitlines()[0]
    assert header.startswith("id,")
    assert "trip_id" in header
    assert len(text.splitlines()) >= 2


def test_bulk_create_occupancy_readings():
    before = service.count()
    created = service.bulk_create([valid_occupancy_reading_data(), valid_occupancy_reading_data()])
    assert len(created) == 2
    assert service.count() == before + 2


def test_bulk_create_occupancy_readings_is_all_or_nothing():
    before = service.count()
    bad = valid_occupancy_reading_data()
    bad.pop("trip_id")
    with pytest.raises(ValidationError):
        service.bulk_create([valid_occupancy_reading_data(), bad])
    assert service.count() == before
