"""Example of using fastuuid7 for database primary keys."""

import uuid

from uuidv7 import uuid7


class User:
    """Example User model with UUID v7 primary key."""

    def __init__(self, name: str, email: str):
        """Initialize a new user with a UUID v7 ID."""
        self.id = uuid7()
        self.name = name
        self.email = email
        self.created_at = self.id.time

    id: uuid.UUID

    def __repr__(self) -> str:
        """String representation of User."""
        return f"User(id={self.id}, name={self.name}, email={self.email})"


def main():
    """Demonstrate database usage patterns."""
    print("Database Usage Example")
    print("=" * 50)

    # Create users with UUID v7 IDs
    print("\n1. Create users with UUID v7 primary keys:")
    users = [
        User("Alice", "alice@example.com"),
        User("Bob", "bob@example.com"),
        User("Charlie", "charlie@example.com"),
    ]

    for user in users:
        print(f"   {user}")

    # Demonstrate sorting by creation time (UUID v7 is time-ordered)
    print("\n2. Users sorted by creation time (UUID v7 is time-ordered):")
    sorted_users = sorted(users, key=lambda u: u.id)
    for user in sorted_users:
        print(f"   {user.id} - {user.name} ({user.created_at})")

    # Simulate database insert
    print("\n3. Simulate database insert operations:")
    print("   SQL-like insert statements:")
    for user in users:
        print(
            f"   INSERT INTO users (id, name, email) VALUES ('{user.id}', '{user.name}', '{user.email}');"
        )


if __name__ == "__main__":
    main()
