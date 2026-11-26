
from dataclasses import dataclass
from typing import Optional


@dataclass
class User:
    id: Optional[int]
    name: str
    email: str
    role: str = "Analyst"
    is_active: bool = True
    created_at: Optional[str] = None

    @classmethod
    def from_database_row(cls, row):
        """Convert a SQLite row into a User object."""

        if row is None:
            return None

        return cls(
            id=row["id"],
            name=row["name"],
            email=row["email"],
            role=row["role"],
            is_active=bool(row["is_active"]),
            created_at=row["created_at"]
        )

    def to_dict(self):
        """Convert the user model into a dictionary."""

        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "is_active": self.is_active,
            "created_at": self.created_at
        }
