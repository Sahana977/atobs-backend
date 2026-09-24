"""Service-level tests for feedback."""
import pytest

from app.errors import ConflictError, NotFoundError, ValidationError
from app.services import feedback_service as service
from tests.factories import make_feedback, valid_feedback_data


def test_create_and_get_feedback():
    item = make_feedback()
    fetched = service.get(item.id)
    assert fetched.id == item.id
    assert fetched.user_id == item.user_id
    assert fetched.created_at and fetched.updated_at


def test_list_feedbacks_returns_a_page():
    make_feedback()
    make_feedback()
    page = service.list_(limit=10)
    assert page["total"] >= 2
    assert len(page["items"]) >= 2
    assert page["limit"] == 10


def test_list_feedbacks_pagination():
    for _ in range(3):
        make_feedback()
    first_page = service.list_(limit=2, offset=0)
    second_page = service.list_(limit=2, offset=2)
    first_ids = {i["id"] for i in first_page["items"]}
    second_ids = {i["id"] for i in second_page["items"]}
    assert first_ids.isdisjoint(second_ids)


def test_count_feedbacks():
    before = service.count()
    make_feedback()
    assert service.count() == before + 1


def test_update_feedback_rating():
    item = make_feedback()
    updated = service.update(item.id, {"rating": 5})
    assert updated.rating == 5


def test_update_feedback_with_nothing_changes_nothing():
    item = make_feedback()
    same = service.update(item.id, {})
    assert same.rating == item.rating


def test_update_missing_feedback_raises():
    with pytest.raises(NotFoundError):
        service.update(999_999, {})


def test_delete_feedback():
    item = make_feedback()
    service.delete(item.id)
    with pytest.raises(NotFoundError):
        service.get(item.id)


def test_delete_missing_feedback_raises():
    with pytest.raises(NotFoundError):
        service.delete(999_999)


def test_get_missing_feedback_raises():
    with pytest.raises(NotFoundError):
        service.get(999_999)


def test_feedback_unknown_user_id_rejected():
    with pytest.raises(ValidationError) as exc:
        service.create(valid_feedback_data(user_id=999_999))
    assert "user_id" in exc.value.errors


def test_feedback_unknown_trip_id_rejected():
    with pytest.raises(ValidationError) as exc:
        service.create(valid_feedback_data(trip_id=999_999))
    assert "trip_id" in exc.value.errors


def test_feedback_requires_rating():
    data = valid_feedback_data()
    data.pop("rating")
    with pytest.raises(ValidationError) as exc:
        service.create(data)
    assert "rating" in exc.value.errors


def test_feedback_rating_below_minimum():
    with pytest.raises(ValidationError):
        service.create(valid_feedback_data(rating=0))


def test_feedback_rating_above_maximum():
    with pytest.raises(ValidationError):
        service.create(valid_feedback_data(rating=6))


def test_feedback_rating_rejects_text():
    with pytest.raises(ValidationError):
        service.create(valid_feedback_data(rating="abc"))


def test_feedback_comfort_rating_below_minimum():
    with pytest.raises(ValidationError):
        service.create(valid_feedback_data(comfort_rating=0))


def test_feedback_comfort_rating_above_maximum():
    with pytest.raises(ValidationError):
        service.create(valid_feedback_data(comfort_rating=6))


def test_feedback_comfort_rating_rejects_text():
    with pytest.raises(ValidationError):
        service.create(valid_feedback_data(comfort_rating="abc"))


def test_feedback_rejects_invalid_category():
    with pytest.raises(ValidationError):
        service.create(valid_feedback_data(category="not-a-valid-choice"))


def test_feedback_comment_too_long():
    with pytest.raises(ValidationError):
        service.create(valid_feedback_data(comment="x" * 2001))


def test_search_feedbacks_by_text():
    item = make_feedback(comment="Zebra Crossing Special")
    page = service.list_({"q": "Zebra Crossing"})
    assert any(i["id"] == item.id for i in page["items"])


def test_export_feedbacks_csv():
    make_feedback()
    text = service.export_csv()
    header = text.splitlines()[0]
    assert header.startswith("id,")
    assert "user_id" in header
    assert len(text.splitlines()) >= 2


def test_bulk_create_feedbacks():
    before = service.count()
    created = service.bulk_create([valid_feedback_data(), valid_feedback_data()])
    assert len(created) == 2
    assert service.count() == before + 2


def test_bulk_create_feedbacks_is_all_or_nothing():
    before = service.count()
    bad = valid_feedback_data()
    bad.pop("rating")
    with pytest.raises(ValidationError):
        service.bulk_create([valid_feedback_data(), bad])
    assert service.count() == before
