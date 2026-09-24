"""Service-level tests for traffic readings."""
import pytest

from app.errors import ConflictError, NotFoundError, ValidationError
from app.services import traffic_reading_service as service
from tests.factories import make_traffic_reading, valid_traffic_reading_data


def test_create_and_get_traffic_reading():
    item = make_traffic_reading()
    fetched = service.get(item.id)
    assert fetched.id == item.id
    assert fetched.stop_id == item.stop_id
    assert fetched.created_at and fetched.updated_at


def test_list_traffic_readings_returns_a_page():
    make_traffic_reading()
    make_traffic_reading()
    page = service.list_(limit=10)
    assert page["total"] >= 2
    assert len(page["items"]) >= 2
    assert page["limit"] == 10


def test_list_traffic_readings_pagination():
    for _ in range(3):
        make_traffic_reading()
    first_page = service.list_(limit=2, offset=0)
    second_page = service.list_(limit=2, offset=2)
    first_ids = {i["id"] for i in first_page["items"]}
    second_ids = {i["id"] for i in second_page["items"]}
    assert first_ids.isdisjoint(second_ids)


def test_count_traffic_readings():
    before = service.count()
    make_traffic_reading()
    assert service.count() == before + 1


def test_update_traffic_reading_traffic_level():
    item = make_traffic_reading()
    updated = service.update(item.id, {"traffic_level": 'severe'})
    assert updated.traffic_level == 'severe'


def test_update_traffic_reading_with_nothing_changes_nothing():
    item = make_traffic_reading()
    same = service.update(item.id, {})
    assert same.traffic_level == item.traffic_level


def test_update_missing_traffic_reading_raises():
    with pytest.raises(NotFoundError):
        service.update(999_999, {})


def test_delete_traffic_reading():
    item = make_traffic_reading()
    service.delete(item.id)
    with pytest.raises(NotFoundError):
        service.get(item.id)


def test_delete_missing_traffic_reading_raises():
    with pytest.raises(NotFoundError):
        service.delete(999_999)


def test_get_missing_traffic_reading_raises():
    with pytest.raises(NotFoundError):
        service.get(999_999)


def test_traffic_reading_requires_stop_id():
    data = valid_traffic_reading_data()
    data.pop("stop_id")
    with pytest.raises(ValidationError) as exc:
        service.create(data)
    assert "stop_id" in exc.value.errors


def test_traffic_reading_unknown_stop_id_rejected():
    with pytest.raises(ValidationError) as exc:
        service.create(valid_traffic_reading_data(stop_id=999_999))
    assert "stop_id" in exc.value.errors


def test_traffic_reading_requires_recorded_at():
    data = valid_traffic_reading_data()
    data.pop("recorded_at")
    with pytest.raises(ValidationError) as exc:
        service.create(data)
    assert "recorded_at" in exc.value.errors


def test_traffic_reading_rejects_bad_recorded_at():
    with pytest.raises(ValidationError):
        service.create(valid_traffic_reading_data(recorded_at="not-a-date"))


def test_traffic_reading_requires_traffic_level():
    data = valid_traffic_reading_data()
    data.pop("traffic_level")
    with pytest.raises(ValidationError) as exc:
        service.create(data)
    assert "traffic_level" in exc.value.errors


def test_traffic_reading_rejects_invalid_traffic_level():
    with pytest.raises(ValidationError):
        service.create(valid_traffic_reading_data(traffic_level="not-a-valid-choice"))


def test_traffic_reading_vehicle_density_below_minimum():
    with pytest.raises(ValidationError):
        service.create(valid_traffic_reading_data(vehicle_density=-0.5))


def test_traffic_reading_vehicle_density_above_maximum():
    with pytest.raises(ValidationError):
        service.create(valid_traffic_reading_data(vehicle_density=500.5))


def test_traffic_reading_vehicle_density_rejects_text():
    with pytest.raises(ValidationError):
        service.create(valid_traffic_reading_data(vehicle_density="abc"))


def test_traffic_reading_avg_speed_below_minimum():
    with pytest.raises(ValidationError):
        service.create(valid_traffic_reading_data(avg_speed=-0.5))


def test_traffic_reading_avg_speed_above_maximum():
    with pytest.raises(ValidationError):
        service.create(valid_traffic_reading_data(avg_speed=120.5))


def test_traffic_reading_avg_speed_rejects_text():
    with pytest.raises(ValidationError):
        service.create(valid_traffic_reading_data(avg_speed="abc"))


def test_traffic_reading_road_occupancy_below_minimum():
    with pytest.raises(ValidationError):
        service.create(valid_traffic_reading_data(road_occupancy=-0.5))


def test_traffic_reading_road_occupancy_above_maximum():
    with pytest.raises(ValidationError):
        service.create(valid_traffic_reading_data(road_occupancy=1.5))


def test_traffic_reading_road_occupancy_rejects_text():
    with pytest.raises(ValidationError):
        service.create(valid_traffic_reading_data(road_occupancy="abc"))


def test_traffic_reading_traffic_flow_below_minimum():
    with pytest.raises(ValidationError):
        service.create(valid_traffic_reading_data(traffic_flow=-0.5))


def test_traffic_reading_traffic_flow_above_maximum():
    with pytest.raises(ValidationError):
        service.create(valid_traffic_reading_data(traffic_flow=5000.5))


def test_traffic_reading_traffic_flow_rejects_text():
    with pytest.raises(ValidationError):
        service.create(valid_traffic_reading_data(traffic_flow="abc"))


def test_traffic_reading_rejects_invalid_source():
    with pytest.raises(ValidationError):
        service.create(valid_traffic_reading_data(source="not-a-valid-choice"))


def test_export_traffic_readings_csv():
    make_traffic_reading()
    text = service.export_csv()
    header = text.splitlines()[0]
    assert header.startswith("id,")
    assert "stop_id" in header
    assert len(text.splitlines()) >= 2


def test_bulk_create_traffic_readings():
    before = service.count()
    created = service.bulk_create([valid_traffic_reading_data(), valid_traffic_reading_data()])
    assert len(created) == 2
    assert service.count() == before + 2


def test_bulk_create_traffic_readings_is_all_or_nothing():
    before = service.count()
    bad = valid_traffic_reading_data()
    bad.pop("stop_id")
    with pytest.raises(ValidationError):
        service.bulk_create([valid_traffic_reading_data(), bad])
    assert service.count() == before
