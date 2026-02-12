"""
CSV loader for metadata (titles, captions, hashtags).

Allows loading randomized metadata from CSV files for more variety in uploads.
"""

import csv
import logging
from pathlib import Path
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


def load_csv_metadata(csv_path: str) -> Dict[str, List[str]]:
    """
    Load metadata from CSV file with robust validation.
    
    Expected CSV format:
    - Column headers: title, caption, description, tags (or hashtags)
    - Each row represents one set of metadata
    - tags/hashtags should be comma-separated within the cell
    
    Args:
        csv_path: Path to CSV file
        
    Returns:
        Dictionary with lists of titles, captions, descriptions, and tags
        
    Raises:
        FileNotFoundError: If CSV file doesn't exist
        ValueError: If CSV is invalid or missing required columns
    """
    if not Path(csv_path).exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    
    if not csv_path.endswith('.csv'):
        raise ValueError(f"File must be CSV format: {csv_path}")
    
    metadata = {
        "titles": [],
        "captions": [],
        "descriptions": [],
        "tags": []
    }
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            # Validate headers
            if not reader.fieldnames:
                raise ValueError("CSV file is empty or has no headers")
            
            # Normalize header names (case-insensitive)
            headers = {h.lower().strip(): h for h in reader.fieldnames}
            
            # Map common column name variations
            title_col = headers.get('title') or headers.get('titles')
            caption_col = headers.get('caption') or headers.get('captions')
            desc_col = headers.get('description') or headers.get('descriptions')
            tags_col = headers.get('tags') or headers.get('hashtags') or headers.get('tag')
            
            # Check for at least one recognized column
            if not any([title_col, caption_col, desc_col, tags_col]):
                available_cols = ', '.join(reader.fieldnames)
                raise ValueError(
                    f"CSV missing required columns. "
                    f"Required at least one of: title, caption, description, tags. "
                    f"Found: {available_cols}"
                )
            
            row_count = 0
            empty_row_count = 0
            
            for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
                row_count += 1
                has_data = False
                
                # Extract title
                if title_col and row.get(title_col):
                    title_val = row[title_col].strip()
                    if title_val:
                        metadata["titles"].append(title_val)
                        has_data = True
                
                # Extract caption
                if caption_col and row.get(caption_col):
                    caption_val = row[caption_col].strip()
                    if caption_val:
                        metadata["captions"].append(caption_val)
                        has_data = True
                
                # Extract description
                if desc_col and row.get(desc_col):
                    desc_val = row[desc_col].strip()
                    if desc_val:
                        metadata["descriptions"].append(desc_val)
                        has_data = True
                
                # Extract tags (split by comma)
                if tags_col and row.get(tags_col):
                    tags_str = row[tags_col].strip()
                    if tags_str:
                        # Split tags and clean them
                        row_tags = [t.strip() for t in tags_str.split(',') if t.strip()]
                        if row_tags:
                            metadata["tags"].extend(row_tags)
                            has_data = True
                
                # Warn about empty rows
                if not has_data:
                    empty_row_count += 1
                    logger.warning(f"Row {row_num}: Empty or all whitespace, skipping")
            
            # Remove duplicates from tags while preserving order
            seen = set()
            unique_tags = []
            for tag in metadata["tags"]:
                if tag not in seen:
                    seen.add(tag)
                    unique_tags.append(tag)
            metadata["tags"] = unique_tags
            
            logger.info(f"Loaded CSV metadata: {row_count} rows processed, "
                       f"{empty_row_count} empty rows skipped, "
                       f"{len(metadata['titles'])} titles, "
                       f"{len(metadata['captions'])} captions, "
                       f"{len(metadata['descriptions'])} descriptions, "
                       f"{len(metadata['tags'])} unique tags")
            
            # Error if no metadata was found
            if not any([metadata['titles'], metadata['captions'], metadata['descriptions'], metadata['tags']]):
                raise ValueError(f"CSV file contains no valid data rows: {csv_path}")
            
            return metadata
            
    except UnicodeDecodeError as e:
        raise ValueError(f"CSV file encoding error. Please save as UTF-8: {csv_path}. Error: {e}")
    except csv.Error as e:
        raise ValueError(f"CSV parsing error at row {reader.line_num if 'reader' in locals() else 'unknown'}: {e}")
    except Exception as e:
        if isinstance(e, (FileNotFoundError, ValueError)):
            raise
        logger.error(f"Error loading CSV metadata from {csv_path}: {e}")
        raise ValueError(f"Failed to load CSV metadata: {e}")


def merge_csv_with_ui_metadata(
    csv_data: Dict[str, List[str]],
    ui_titles: List[str],
    ui_captions: List[str],
    ui_descriptions: List[str],
    ui_tags: List[str]
) -> Dict[str, List[str]]:
    """
    Merge CSV metadata with UI-provided metadata.
    
    CSV values take precedence and are added to UI values.
    
    Args:
        csv_data: Metadata loaded from CSV
        ui_titles: Titles from UI
        ui_captions: Captions from UI
        ui_descriptions: Descriptions from UI
        ui_tags: Tags from UI
        
    Returns:
        Combined metadata dictionary
    """
    merged = {
        "titles": csv_data.get("titles", []) + ui_titles,
        "captions": csv_data.get("captions", []) + ui_captions,
        "descriptions": csv_data.get("descriptions", []) + ui_descriptions,
        "tags": csv_data.get("tags", []) + ui_tags
    }
    
    # Remove empty strings
    merged["titles"] = [t for t in merged["titles"] if t]
    merged["captions"] = [c for c in merged["captions"] if c]
    merged["descriptions"] = [d for d in merged["descriptions"] if d]
    merged["tags"] = [t for t in merged["tags"] if t]
    
    # Remove tag duplicates while preserving order
    seen = set()
    unique_tags = []
    for tag in merged["tags"]:
        if tag not in seen:
            seen.add(tag)
            unique_tags.append(tag)
    merged["tags"] = unique_tags
    
    return merged


def validate_csv_format(csv_path: str) -> tuple[bool, str]:
    """
    Validate CSV file format without loading all data.
    
    Args:
        csv_path: Path to CSV file
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not Path(csv_path).exists():
        return False, f"File not found: {csv_path}"
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            if not reader.fieldnames:
                return False, "CSV file is empty or has no headers"
            
            # Check for at least one recognized column
            headers_lower = [h.lower().strip() for h in reader.fieldnames]
            recognized = ['title', 'titles', 'caption', 'captions', 
                         'description', 'descriptions', 'tags', 'hashtags', 'tag']
            
            if not any(h in recognized for h in headers_lower):
                return False, f"CSV must have at least one of these columns: {', '.join(recognized)}"
            
            return True, "Valid CSV format"
            
    except Exception as e:
        return False, f"Error reading CSV: {e}"
