"""
Input Validators

This module provides functions for validating inputs and handling errors
for Ceph RGW bucket statistics scripts.
"""

import sys
import json
from pathlib import Path
from typing import Optional


def validate_file_exists(filepath: str, file_description: str = "File") -> bool:
    """
    Validate that a file exists.
    
    Args:
        filepath: Path to the file
        file_description: Description of the file for error messages
        
    Returns:
        True if file exists
        
    Raises:
        FileNotFoundError: If file doesn't exist
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"{file_description} not found: {filepath}")
    if not path.is_file():
        raise ValueError(f"{file_description} is not a file: {filepath}")
    return True


def validate_json_file(filepath: str) -> bool:
    """
    Validate that a file contains valid JSON.
    
    Args:
        filepath: Path to the JSON file
        
    Returns:
        True if file contains valid JSON
        
    Raises:
        json.JSONDecodeError: If file doesn't contain valid JSON
    """
    try:
        with open(filepath, 'r') as f:
            json.load(f)
        return True
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(
            f"Invalid JSON in file '{filepath}': {e.msg}",
            e.doc,
            e.pos
        )


def validate_percentile(value: float) -> bool:
    """
    Validate that a percentile value is between 0.0 and 1.0.
    
    Args:
        value: Percentile value to validate
        
    Returns:
        True if valid
        
    Raises:
        ValueError: If value is not between 0.0 and 1.0
    """
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"Percentile must be between 0.0 and 1.0, got {value}")
    return True


def validate_threshold(value: int, min_value: int = 0) -> bool:
    """
    Validate that a threshold value is non-negative.
    
    Args:
        value: Threshold value to validate
        min_value: Minimum allowed value (default: 0)
        
    Returns:
        True if valid
        
    Raises:
        ValueError: If value is less than min_value
    """
    if value < min_value:
        raise ValueError(f"Threshold must be >= {min_value}, got {value}")
    return True


def validate_sort_order(value: str, valid_orders: Optional[list] = None) -> bool:
    """
    Validate that a sort order is valid.
    
    Args:
        value: Sort order to validate
        valid_orders: List of valid sort orders (default: ['asc', 'desc'])
        
    Returns:
        True if valid
        
    Raises:
        ValueError: If value is not in valid_orders
    """
    if valid_orders is None:
        valid_orders = ['asc', 'desc']
    
    if value not in valid_orders:
        raise ValueError(
            f"Sort order must be one of {valid_orders}, got '{value}'"
        )
    return True


def validate_output_format(value: str, valid_formats: Optional[list] = None) -> bool:
    """
    Validate that an output format is valid.
    
    Args:
        value: Output format to validate
        valid_formats: List of valid formats (default: ['table', 'json', 'csv'])
        
    Returns:
        True if valid
        
    Raises:
        ValueError: If value is not in valid_formats
    """
    if valid_formats is None:
        valid_formats = ['table', 'json', 'csv']
    
    if value not in valid_formats:
        raise ValueError(
            f"Output format must be one of {valid_formats}, got '{value}'"
        )
    return True


def validate_positive_integer(value: int, name: str = "Value") -> bool:
    """
    Validate that a value is a positive integer.
    
    Args:
        value: Value to validate
        name: Name of the value for error messages
        
    Returns:
        True if valid
        
    Raises:
        ValueError: If value is not positive
    """
    if value <= 0:
        raise ValueError(f"{name} must be positive, got {value}")
    return True


def handle_error(error: Exception, 
                 exit_code: int = 1,
                 show_traceback: bool = False) -> None:
    """
    Handle an error by printing a message and exiting.
    
    Args:
        error: The exception to handle
        exit_code: Exit code to use (default: 1)
        show_traceback: Whether to show full traceback (default: False)
    """
    error_type = type(error).__name__
    print(f"Error ({error_type}): {error}", file=sys.stderr)
    
    if show_traceback:
        import traceback
        traceback.print_exc(file=sys.stderr)
    
    sys.exit(exit_code)


def validate_bucket_data_structure(data: dict) -> bool:
    """
    Validate that bucket data has the expected structure.
    
    Args:
        data: Bucket data dictionary to validate
        
    Returns:
        True if valid
        
    Raises:
        ValueError: If structure is invalid
    """
    required_fields = ['bucket', 'num_shards']
    
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing required field: {field}")
    
    # Validate types
    if not isinstance(data['bucket'], str):
        raise ValueError("Field 'bucket' must be a string")
    
    if not isinstance(data['num_shards'], int):
        raise ValueError("Field 'num_shards' must be an integer")
    
    return True


def get_error_exit_code(error: Exception) -> int:
    """
    Get appropriate exit code for an error type.
    
    Args:
        error: The exception
        
    Returns:
        Exit code (1-99)
    """
    error_codes = {
        FileNotFoundError: 1,
        json.JSONDecodeError: 2,
        ValueError: 3,
        PermissionError: 4,
        KeyboardInterrupt: 130,
    }
    
    return error_codes.get(type(error), 99)

# Made with Bob
