"""Service-level tests for alerts."""
import pytest

from app.errors import ConflictError, NotFoundError, ValidationError
from app.services import alert_service as service
from tests.factories import make_alert, valid_alert_data


def test_create_and_get_alert():
    item = make_alert()
    fetched = service.get(item.id)
    assert fetched.id == item.id
    assert fetched.title == item.title
    assert fetched.created_at and fetched.updated_at


def test_list_alerts_returns_a_page():
    make_alert()
    make_alert()
    page = service.list_(limit=10)
    assert page["total"] >= 2
    assert len(page["items"]) >= 2
    assert page["limit"] == 10


def test_list_alerts_pagination():
    for _ in range(3):
        make_alert()
    first_page = service.list_(limit=2, offset=0)
    second_page = service.list_(limit=2, offset=2)
    first_ids = {i["id"] for i in first_page["items"]}
    second_ids = {i["id"] for i in second_page["items"]}
    assert first_ids.isdisjoint(second_ids)


def test_count_alerts():
    before = service.count()
    make_alert()
    assert service.count() == before + 1


def test_update_alert_title():
    item = make_alert()
    updated = service.update(item.id, {"title": "Updated value"})
    assert updated.title == "Updated value"


def test_update_alert_with_nothing_changes_nothing():
    item = make_alert()
    same = service.update(item.id, {})
    assert same.title == item.title


def test_update_missing_alert_raises():
    with pytest.raises(NotFoundError):
        service.update(999_999, {})


def test_delete_alert():
    item = make_alert()
    service.delete(item.id)
    with pytest.raises(NotFoundError):
        service.get(item.id)


def test_delete_missing_alert_raises():
    with pytest.raises(NotFoundError):
        service.delete(999_999)


def test_get_missing_alert_raises():
    with pytest.raises(NotFoundError):
        service.get(999_999)


def test_alert_requires_title():
    data = valid_alert_data()
    data.pop("title")
    with pytest.raises(ValidationError) as exc:
        service.create(data)
    assert "title" in exc.value.errors


def test_alert_title_too_long():
    with pytest.raises(ValidationError):
        service.create(valid_alert_data(title="x" * 201))


def test_alert_requires_message():
    data = valid_alert_data()
    data.pop("message")
    with pytest.raises(ValidationError) as exc:
        service.create(data)
    assert "message" in exc.value.errors


def test_alert_message_too_long():
    with pytest.raises(ValidationError):
        service.create(valid_alert_data(message="x" * 2001))


def test_alert_rejects_invalid_severity():
    with pytest.raises(ValidationError):
        service.create(valid_alert_data(severity="not-a-valid-choice"))


def test_alert_unknown_stop_id_rejected():
    with pytest.raises(ValidationError) as exc:
        service.create(valid_alert_data(stop_id=999_999))
    assert "stop_id" in exc.value.errors


def test_alert_unknown_route_id_rejected():
    with pytest.raises(ValidationError) as exc:
        service.create(valid_alert_data(route_id=999_999))
    assert "route_id" in exc.value.errors


def test_alert_requires_starts_at():
    data = valid_alert_data()
    data.pop("starts_at")
    with pytest.raises(ValidationError) as exc:
        service.create(data)
    assert "starts_at" in exc.value.errors


def test_alert_rejects_bad_starts_at():
    with pytest.raises(ValidationError):
        service.create(valid_alert_data(starts_at="not-a-date"))


def test_alert_rejects_bad_ends_at():
    with pytest.raises(ValidationError):
        service.create(valid_alert_data(ends_at="not-a-date"))


def test_alert_is_active_must_be_boolean():
    with pytest.raises(ValidationError):
        service.create(valid_alert_data(is_active="yes"))


def test_search_alerts_by_text():
    item = make_alert(title="Zebra Crossing Special")
    page = service.list_({"q": "Zebra Crossing"})
    assert any(i["id"] == item.id for i in page["items"])


def test_export_alerts_csv():
    make_alert()
    text = service.export_csv()
    header = text.splitlines()[0]
    assert header.startswith("id,")
    assert "title" in header
    assert len(text.splitlines()) >= 2


def test_bulk_create_alerts():
    before = service.count()
    created = service.bulk_create([valid_alert_data(), valid_alert_data()])
    assert len(created) == 2
    assert service.count() == before + 2


def test_bulk_create_alerts_is_all_or_nothing():
    before = service.count()
    bad = valid_alert_data()
    bad.pop("title")
    with pytest.raises(ValidationError):
        service.bulk_create([valid_alert_data(), bad])
    assert service.count() == before


def test_alert_end_must_be_after_start():
    data = valid_alert_data(starts_at="2026-10-02T10:00:00", ends_at="2026-10-02T09:00:00")
    with pytest.raises(ValidationError):
        service.create(data)
