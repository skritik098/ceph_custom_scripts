"""
Bucket Parser Utilities

This module provides functions for parsing Ceph RGW bucket statistics JSON files
and extracting relevant information.
"""

import json
import sys
import math
from typing import Dict, Any, Optional
from pathlib import Path


def parse_bucket_json(filepath: str) -> Dict[str, Dict[str, Any]]:
    """
    Parse a Ceph RGW bucket stats JSON file and return bucket data.
    
    Args:
        filepath: Path to the JSON file
        
    Returns:
        Dictionary mapping bucket names to their data:
        {
            'bucket_name': {
                'num_shards': int,
                'num_objects': int,
                'size_kb': int,
                'objects_per_shard': float
            }
        }
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        json.JSONDecodeError: If the file contains invalid JSON
    """
    try:
        with open(filepath, 'r') as f:
            raw_data = f.read()
            
            if not raw_data.strip():
                print(f"Warning: File '{filepath}' is empty or contains only whitespace.", file=sys.stderr)
                return {}
            
            parsed_json = json.loads(raw_data)
            
            if not isinstance(parsed_json, list):
                print(f"Warning: Expected JSON array in '{filepath}', got {type(parsed_json).__name__}", file=sys.stderr)
                return {}
            
            bucket_data = {}
            for item in parsed_json:
                bucket_info = extract_bucket_info(item)
                if bucket_info and bucket_info.get('bucket'):
                    bucket_name = bucket_info['bucket']
                    bucket_data[bucket_name] = bucket_info
                    
            return bucket_data
            
    except FileNotFoundError:
        print(f"Error: File '{filepath}' not found.", file=sys.stderr)
        raise
    except json.JSONDecodeError as e:
        print(f"Error: Could not decode JSON from '{filepath}': {e}", file=sys.stderr)
        raise
    except Exception as e:
        print(f"An unexpected error occurred while processing '{filepath}': {e}", file=sys.stderr)
        raise


def extract_bucket_info(bucket_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Extract relevant information from a bucket stats entry.
    
    Args:
        bucket_data: Raw bucket data dictionary from JSON
        
    Returns:
        Dictionary with extracted information or None if invalid
    """
    bucket_name = bucket_data.get('bucket')
    num_shards = bucket_data.get('num_shards')
    
    if bucket_name is None or num_shards is None:
        return None
    
    # Extract usage data
    usage_main = bucket_data.get('usage', {}).get('rgw.main', {})
    num_objects = usage_main.get('num_objects', 0)
    size_kb = usage_main.get('size_kb', 0)
    
    # Calculate objects per shard
    objects_per_shard = calculate_objects_per_shard(num_objects, num_shards)
    
    return {
        'bucket': bucket_name,
        'num_shards': num_shards,
        'num_objects': num_objects,
        'size_kb': size_kb,
        'objects_per_shard': objects_per_shard
    }


def get_bucket_objects(bucket_data: Dict[str, Any]) -> int:
    """
    Get the number of objects in a bucket.
    
    Args:
        bucket_data: Bucket data dictionary
        
    Returns:
        Number of objects (0 if not found)
    """
    return bucket_data.get('num_objects', 0)


def get_bucket_shards(bucket_data: Dict[str, Any]) -> int:
    """
    Get the number of shards for a bucket.
    
    Args:
        bucket_data: Bucket data dictionary
        
    Returns:
        Number of shards (0 if not found)
    """
    return bucket_data.get('num_shards', 0)


def calculate_objects_per_shard(num_objects: int, num_shards: int) -> float:
    """
    Calculate objects per shard ratio.
    
    Args:
        num_objects: Total number of objects
        num_shards: Number of shards
        
    Returns:
        Objects per shard (0.0 if num_shards is 0)
    """
    if num_shards == 0:
        return 0.0
    return math.floor(num_objects / num_shards)


def validate_json_structure(data: Any) -> bool:
    """
    Validate that the JSON data has the expected structure.
    
    Args:
        data: Parsed JSON data
        
    Returns:
        True if valid, False otherwise
    """
    if not isinstance(data, list):
        return False
    
    if len(data) == 0:
        return True  # Empty list is valid
    
    # Check first item has expected fields
    first_item = data[0]
    if not isinstance(first_item, dict):
        return False
    
    required_fields = ['bucket', 'num_shards']
    return all(field in first_item for field in required_fields)


def filter_by_objects_per_shard(bucket_data: Dict[str, Dict[str, Any]], 
                                 threshold: int) -> Dict[str, Dict[str, Any]]:
    """
    Filter buckets by objects per shard threshold.
    
    Args:
        bucket_data: Dictionary of bucket data
        threshold: Minimum objects per shard
        
    Returns:
        Filtered dictionary of bucket data
    """
    return {
        name: data 
        for name, data in bucket_data.items() 
        if data.get('objects_per_shard', 0) > threshold
    }

# Made with Bob
