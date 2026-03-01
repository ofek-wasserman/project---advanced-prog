import pytest

from src.domain.user import User


def test_user_creation_valid():
    user = User(user_id=1, payment_token="tok_123")
    assert user.user_id == 1
    assert user.payment_token == "tok_123"


def test_user_id_must_be_positive():
    with pytest.raises(ValueError):
        User(user_id=0, payment_token="tok_123")

    with pytest.raises(ValueError):
        User(user_id=-5, payment_token="tok_123")


def test_payment_token_must_not_be_empty():
    with pytest.raises(ValueError):
        User(user_id=1, payment_token="") # empty string

    with pytest.raises(ValueError):
        User(user_id=1, payment_token=None)  # if type hints are bypassed
