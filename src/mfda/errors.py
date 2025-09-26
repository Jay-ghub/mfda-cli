"""
Error Taxonomy (design only)

This module defines the error categories used across the project.
No classes are implemented at this stage; this is a contract docstring.

- MfdaError: root for all project errors.
- FileFormatError: bad/unsupported format, corrupt file, extension/signature mismatch.
- SchemaError: invalid schema definition (unknown dtype) or schema check failure
               (duplicate keys, missing required columns).
- ValidationError: data failed a validation rule (e.g., above allowed missingness).
- DataIntegrityError: general data problems outside schema checks
                      (e.g., mixed types in a column).
- ConfigurationError: CLI/config problems (bad flags, impossible combination).
- NotImplementedFormatError: format recognized but reader not implemented yet.
"""


class FileFormatError(Exception):
    """Raised when a file does not match the expected format."""

    pass


class ConfigurationError(Exception):
    """Raised with config problems"""

    pass
