"""Service-level tests for users."""
import pytest

from app.errors import ConflictError, NotFoundError, ValidationError
from app.services import app_user_service as service
from tests.factories import make_app_user, valid_app_user_data


def test_create_and_get_app_user():
    item = make_app_user()
    fetched = service.get(item.id)
    assert fetched.id == item.id
    assert fetched.email == item.email
    assert fetched.created_at and fetched.updated_at


def test_list_app_users_returns_a_page():
    make_app_user()
    make_app_user()
    page = service.list_(limit=10)
    assert page["total"] >= 2
    assert len(page["items"]) >= 2
    assert page["limit"] == 10


def test_list_app_users_pagination():
    for _ in range(3):
        make_app_user()
    first_page = service.list_(limit=2, offset=0)
    second_page = service.list_(limit=2, offset=2)
    first_ids = {i["id"] for i in first_page["items"]}
    second_ids = {i["id"] for i in second_page["items"]}
    assert first_ids.isdisjoint(second_ids)


def test_count_app_users():
    before = service.count()
    make_app_user()
    assert service.count() == before + 1


def test_update_app_user_full_name():
    item = make_app_user()
    updated = service.update(item.id, {"full_name": "Updated value"})
    assert updated.full_name == "Updated value"


def test_update_app_user_with_nothing_changes_nothing():
    item = make_app_user()
    same = service.update(item.id, {})
    assert same.full_name == item.full_name


def test_update_missing_app_user_raises():
    with pytest.raises(NotFoundError):
        service.update(999_999, {})


def test_delete_app_user():
    item = make_app_user()
    service.delete(item.id)
    with pytest.raises(NotFoundError):
        service.get(item.id)


def test_delete_missing_app_user_raises():
    with pytest.raises(NotFoundError):
        service.delete(999_999)


def test_get_missing_app_user_raises():
    with pytest.raises(NotFoundError):
        service.get(999_999)


def test_app_user_requires_email():
    data = valid_app_user_data()
    data.pop("email")
    with pytest.raises(ValidationError) as exc:
        service.create(data)
    assert "email" in exc.value.errors


def test_app_user_duplicate_email_conflicts():
    item = make_app_user()
    with pytest.raises(ConflictError):
        service.create(valid_app_user_data(email=item.email))


def test_app_user_email_too_long():
    with pytest.raises(ValidationError):
        service.create(valid_app_user_data(email="x" * 121))


def test_app_user_requires_full_name():
    data = valid_app_user_data()
    data.pop("full_name")
    with pytest.raises(ValidationError) as exc:
        service.create(data)
    assert "full_name" in exc.value.errors


def test_app_user_full_name_too_long():
    with pytest.raises(ValidationError):
        service.create(valid_app_user_data(full_name="x" * 201))


def test_app_user_rejects_invalid_role():
    with pytest.raises(ValidationError):
        service.create(valid_app_user_data(role="not-a-valid-choice"))


def test_app_user_unknown_home_stop_id_rejected():
    with pytest.raises(ValidationError) as exc:
        service.create(valid_app_user_data(home_stop_id=999_999))
    assert "home_stop_id" in exc.value.errors


def test_app_user_is_active_must_be_boolean():
    with pytest.raises(ValidationError):
        service.create(valid_app_user_data(is_active="yes"))


def test_search_app_users_by_text():
    item = make_app_user(full_name="Zebra Crossing Special")
    page = service.list_({"q": "Zebra Crossing"})
    assert any(i["id"] == item.id for i in page["items"])


def test_export_app_users_csv():
    make_app_user()
    text = service.export_csv()
    header = text.splitlines()[0]
    assert header.startswith("id,")
    assert "email" in header
    assert len(text.splitlines()) >= 2


def test_bulk_create_app_users():
    before = service.count()
    created = service.bulk_create([valid_app_user_data(), valid_app_user_data()])
    assert len(created) == 2
    assert service.count() == before + 2


def test_bulk_create_app_users_is_all_or_nothing():
    before = service.count()
    bad = valid_app_user_data()
    bad.pop("email")
    with pytest.raises(ValidationError):
        service.bulk_create([valid_app_user_data(), bad])
    assert service.count() == before


def test_user_email_must_be_valid():
    with pytest.raises(ValidationError):
        service.create(valid_app_user_data(email="not-an-email"))


def test_user_email_is_lowercased():
    user = service.create(valid_app_user_data(email="Mixed.Case@Example.com"))
    assert user.email == "mixed.case@example.com"
