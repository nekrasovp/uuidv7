"""Example of using fastuuid7 for database primary keys."""

from uuidv7 import uuid7


class User:
    """Example User model with UUID v7 primary key."""

    def __init__(self, name: str, email: str):
        """Initialize a new user with a UUID v7 ID."""
        self.id = uuid7()
        self.name = name
        self.email = email
        self.created_at = self._extract_timestamp()

    def _extract_timestamp(self) -> int:
        """Extract timestamp from UUID v7 (approximate).

        Note: This is a simplified extraction. For accurate timestamp
        extraction, use proper UUID v7 parsing.
        """
        # UUID v7 format: timestamp_ms (48 bits) in first two segments
        parts = self.id.split("-")
        timestamp_hex = parts[0] + parts[1]
        # This is approximate - actual extraction requires proper bit manipulation
        return int(timestamp_hex, 16)

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
        print(f"   {user.id} - {user.name}")

    # Simulate database insert
    print("\n3. Simulate database insert operations:")
    print("   SQL-like insert statements:")
    for user in users:
        print(
            f"   INSERT INTO users (id, name, email) VALUES ('{user.id}', '{user.name}', '{user.email}');"
        )


if __name__ == "__main__":
    main()
