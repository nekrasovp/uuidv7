"""Example of batch UUID v7 generation for high-throughput scenarios."""

from uuidv7 import uuid7


def generate_batch(count: int) -> list[str]:
    """Generate a batch of UUID v7 values.

    Args:
        count: Number of UUIDs to generate

    Returns:
        List of UUID strings
    """
    return [uuid7() for _ in range(count)]


def main():
    """Demonstrate batch UUID generation."""
    print("Batch UUID v7 Generation")
    print("=" * 50)

    # Generate a small batch
    print("\n1. Generate a small batch (10 UUIDs):")
    batch = generate_batch(10)
    for i, uuid_val in enumerate(batch, 1):
        print(f"   {i:2d}. {uuid_val}")

    # Generate a larger batch and verify uniqueness
    print("\n2. Generate a large batch and verify uniqueness:")
    batch_size = 10000
    batch = generate_batch(batch_size)
    unique_count = len(set(batch))
    print(f"   Generated: {batch_size:,} UUIDs")
    print(f"   Unique: {unique_count:,} UUIDs")
    print(f"   All unique: {'✓ Yes' if unique_count == batch_size else '✗ No'}")

    # Demonstrate timestamp ordering
    print("\n3. Demonstrate timestamp ordering (first 10):")
    batch = generate_batch(10)
    for i, uuid_val in enumerate(batch, 1):
        # Extract timestamp part (first segment)
        timestamp_part = uuid_val.split("-")[0]
        print(f"   {i:2d}. {uuid_val} (timestamp: {timestamp_part})")


if __name__ == "__main__":
    main()
