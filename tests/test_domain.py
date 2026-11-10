from app.domain.user import Role, User


def test_register_normalizes_email_and_is_never_admin():
    user = User.register("  Alice@Example.COM ", "hash")
    assert user.email == "alice@example.com"
    assert user.role is Role.USER
    assert not user.is_admin


def test_change_password_updates_hashed_password():
    user = User.register("a@example.com", "old_hash")
    user.change_password("new_hash")
    assert user.hashed_password == "new_hash"
