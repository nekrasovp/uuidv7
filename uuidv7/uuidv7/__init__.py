"""UUID v7 generation package (internal module)."""

# This module is kept for backward compatibility
# Use 'from uuidv7 import uuid7' instead
from uuidv7 import uuid7, uuid7_bytes, uuid7_str
from uuidv7.uuidv7_impl.uuid7_gen import generate_uuid7

__version__ = "0.2.0"
__all__ = ["uuid7", "uuid7_bytes", "uuid7_str", "generate_uuid7"]
