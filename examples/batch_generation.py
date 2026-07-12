"""Example of batch UUID v7 generation for high-throughput scenarios."""

from __future__ import annotations

import uuid

from fastuuid7 import uuid7_bytes_many, uuid7_many


def main():
    """Demonstrate batch UUID generation."""
    print("Batch UUID v7 Generation")
    print("=" * 50)

    # Generate a small batch
    print("\n1. Generate a small batch (10 UUIDs):")
    batch = uuid7_many(10)
    for i, uuid_val in enumerate(batch, 1):
        print(f"   {i:2d}. {uuid_val}")

    # Generate a larger batch and verify uniqueness
    print("\n2. Generate a large batch and verify uniqueness:")
    batch_size = 10000
    batch = uuid7_many(batch_size)
    unique_count = len(set(batch))
    print(f"   Generated: {batch_size:,} UUIDs")
    print(f"   Unique: {unique_count:,} UUIDs")
    print(f"   All unique: {'✓ Yes' if unique_count == batch_size else '✗ No'}")

    # Demonstrate timestamp ordering
    print("\n3. Demonstrate timestamp ordering (first 10):")
    batch = uuid7_many(10)
    for i, uuid_val in enumerate(batch, 1):
        print(f"   {i:2d}. {uuid_val} (timestamp_ms: {uuid_val.time})")

    print("\n4. Generate one contiguous bytes buffer:")
    raw = uuid7_bytes_many(10)
    parsed = [uuid.UUID(bytes=raw[index : index + 16]) for index in range(0, len(raw), 16)]
    print(f"   Packed {len(parsed)} UUIDs into {len(raw)} bytes")


if __name__ == "__main__":
    main()
