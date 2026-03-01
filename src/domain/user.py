from dataclasses import dataclass


@dataclass
class User:
    """
    Domain entity representing a registered user.
    Invariants:
    - user_id must be positive
    - payment_token must be non-empty
    """

    user_id: int
    payment_token: str

    def __post_init__(self) -> None:
        if self.user_id <= 0:
            raise ValueError("user_id must be positive")

        if not self.payment_token:
            raise ValueError("payment_token must be non-empty")
