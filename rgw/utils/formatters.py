"""
Output Formatters

This module provides functions for formatting output in different formats
(table, JSON, CSV) for Ceph RGW bucket statistics.
"""

import json
import csv
import io
from typing import List, Dict, Any, Optional


def format_table_output(data: List[Dict[str, Any]], 
                        headers: List[str], 
                        padding: int = 3) -> str:
    """
    Format data as a table with dynamic column widths.
    
    Args:
        data: List of dictionaries containing row data
        headers: List of column headers
        padding: Extra padding for columns (default: 3)
        
    Returns:
        Formatted table string
    """
    if not data:
        return "No data to display."
    
    # Calculate column widths
    widths = calculate_column_widths(data, headers, padding)
    
    # Build format string
    format_str = " | ".join(f"{{:<{w}}}" for w in widths)
    
    # Build output
    lines = []
    
    # Header
    lines.append(format_str.format(*headers))
    
    # Separator
    lines.append(create_separator_line(widths))
    
    # Data rows
    for row in data:
        row_values = [str(row.get(h, '')) for h in headers]
        lines.append(format_str.format(*row_values))
    
    return '\n'.join(lines)


def format_json_output(data: List[Dict[str, Any]], 
                       pretty: bool = True) -> str:
    """
    Format data as JSON.
    
    Args:
        data: List of dictionaries containing data
        pretty: Whether to pretty-print (default: True)
        
    Returns:
        JSON string
    """
    if pretty:
        return json.dumps(data, indent=2, sort_keys=False)
    return json.dumps(data)


def format_csv_output(data: List[Dict[str, Any]], 
                      headers: List[str]) -> str:
    """
    Format data as CSV.
    
    Args:
        data: List of dictionaries containing data
        headers: List of column headers
        
    Returns:
        CSV string
    """
    if not data:
        return ""
    
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=headers, extrasaction='ignore')
    
    writer.writeheader()
    writer.writerows(data)
    
    return output.getvalue()


def calculate_column_widths(data: List[Dict[str, Any]], 
                            headers: List[str], 
                            padding: int = 3,
                            max_width: Optional[int] = None) -> List[int]:
    """
    Calculate optimal column widths for table display.
    
    Args:
        data: List of dictionaries containing data
        headers: List of column headers
        padding: Extra padding for columns
        max_width: Maximum width for any column (optional)
        
    Returns:
        List of column widths
    """
    widths = [len(h) for h in headers]
    
    for row in data:
        for i, header in enumerate(headers):
            value_len = len(str(row.get(header, '')))
            widths[i] = max(widths[i], value_len)
    
    # Add padding
    widths = [w + padding for w in widths]
    
    # Apply max width if specified
    if max_width:
        widths = [min(w, max_width) for w in widths]
    
    return widths


def create_separator_line(widths: List[int], 
                          separator: str = '-',
                          junction: str = '-+-') -> str:
    """
    Create a separator line for table display.
    
    Args:
        widths: List of column widths
        separator: Character to use for separation (default: '-')
        junction: String to use at column junctions (default: '-+-')
        
    Returns:
        Separator line string
    """
    parts = [separator * w for w in widths]
    return junction.join(parts)


def format_number(value: int, use_separator: bool = True) -> str:
    """
    Format a number with thousand separators.
    
    Args:
        value: Number to format
        use_separator: Whether to use thousand separator (default: True)
        
    Returns:
        Formatted number string
    """
    if use_separator:
        return f"{value:,}"
    return str(value)


def truncate_string(text: str, max_length: int, suffix: str = '...') -> str:
    """
    Truncate a string to maximum length.
    
    Args:
        text: String to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated (default: '...')
        
    Returns:
        Truncated string
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def format_comparison_table(data: List[Dict[str, Any]], 
                            site1_label: str = "Site 1",
                            site2_label: str = "Site 2") -> str:
    """
    Format a comparison table for two-site bucket comparison.
    
    Args:
        data: List of comparison data dictionaries
        site1_label: Label for first site
        site2_label: Label for second site
        
    Returns:
        Formatted comparison table
    """
    if not data:
        return "No differences found."
    
    headers = [
        'bucket',
        f'{site1_label}_shards',
        f'{site2_label}_shards',
        f'{site1_label}_objects',
        f'{site2_label}_objects'
    ]
    
    return format_table_output(data, headers)


def format_delta_table(data: List[Dict[str, Any]],
                       old_label: str = "Old",
                       new_label: str = "New") -> str:
    """
    Format a delta comparison table.
    
    Args:
        data: List of delta data dictionaries
        old_label: Label for old/previous data
        new_label: Label for new/current data
        
    Returns:
        Formatted delta table
    """
    if not data:
        return "No changes found."
    
    headers = [
        'bucket',
        f'{old_label}_objects',
        f'{new_label}_objects',
        'delta'
    ]
    
    return format_table_output(data, headers)

# Made with Bob
