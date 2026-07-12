"""Basic usage example for fastuuid7 library."""

import uuid as uuid_module

from fastuuid7 import uuid7


def main():
    """Demonstrate basic UUID v7 generation."""
    print("Fast UUID v7 Generation Examples")
    print("=" * 50)

    # Generate a single UUID
    print("\n1. Generate a single UUID v7:")
    value = uuid7()
    print(f"   UUID object: {value!r}")
    print(f"   UUID string: {value}")
    print(f"   Timestamp: {value.time} ms")

    # Generate multiple UUIDs
    print("\n2. Generate multiple UUIDs:")
    uuids = [uuid7() for _ in range(5)]
    for i, value in enumerate(uuids, 1):
        print(f"   {i}. {value}")

    # Verify UUID format
    print("\n3. Verify UUID format:")
    sample_uuid = uuid7()
    sample_text = str(sample_uuid)
    print(f"   UUID: {sample_uuid}")
    print(f"   Type: {type(sample_uuid).__name__}")
    print(f"   isinstance(uuid.UUID): {isinstance(sample_uuid, uuid_module.UUID)}")
    print(f"   Length: {len(sample_text)} characters")
    print(
        f"   Format: {'Valid' if len(sample_text) == 36 and sample_text.count('-') == 4 else 'Invalid'}"
    )
    print(f"   Version: {sample_uuid.version}")
    print(f"   Variant: {sample_uuid.variant}")

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
