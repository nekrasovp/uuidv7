"""UUID v7 generation package - fastuuid7."""

from uuidv7.uuidv7_impl.uuid7_gen import generate_uuid7

# Export uuid7 function following Python standard library naming convention
# This matches uuid.uuid7() from Python 3.14+
uuid7 = generate_uuid7

__version__ = "0.1.0"
__all__ = ["uuid7", "__version__"]
