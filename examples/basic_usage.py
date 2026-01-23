"""Basic usage example for fastuuid7 library."""

from uuidv7 import uuid7


def main():
    """Demonstrate basic UUID v7 generation."""
    print("Fast UUID v7 Generation Examples")
    print("=" * 50)

    # Generate a single UUID
    print("\n1. Generate a single UUID v7:")
    uuid = uuid7()
    print(f"   UUID: {uuid}")

    # Generate multiple UUIDs
    print("\n2. Generate multiple UUIDs:")
    uuids = [uuid7() for _ in range(5)]
    for i, uuid_val in enumerate(uuids, 1):
        print(f"   {i}. {uuid_val}")

    # Verify UUID format
    print("\n3. Verify UUID format:")
    sample_uuid = uuid7()
    print(f"   UUID: {sample_uuid}")
    print(f"   Length: {len(sample_uuid)} characters")
    print(
        f"   Format: {'✓ Valid' if len(sample_uuid) == 36 and sample_uuid.count('-') == 4 else '✗ Invalid'}"
    )
    print(f"   Version field (13th char): {sample_uuid[14]} (should be '7')")
    print(f"   Variant field (17th char): {sample_uuid[19]} (should be 8/9/a/b)")

    # Performance demonstration
    print("\n4. Performance demonstration:")
    import time

    count = 100000
    start = time.perf_counter()
    for _ in range(count):
        uuid7()
    end = time.perf_counter()

    elapsed = end - start
    rate = count / elapsed
    print(f"   Generated {count:,} UUIDs in {elapsed:.3f} seconds")
    print(f"   Rate: {rate:,.0f} UUIDs/second")


if __name__ == "__main__":
    main()
