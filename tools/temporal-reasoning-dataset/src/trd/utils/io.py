"""I/O utilities for saving and loading datasets."""

import csv
import json
from pathlib import Path
from typing import List, Tuple, Union


def save_to_csv(data: List[Tuple[str, str]], filepath: Union[str, Path]) -> None:
    """Save dataset to a CSV file.
    
    Args:
        data: List of (question, answer) tuples, with first tuple being header
        filepath: Path to the output CSV file
    """
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, quoting=csv.QUOTE_ALL)
        for row in data:
            writer.writerow(row)


def load_from_csv(filepath: Union[str, Path]) -> List[Tuple[str, str]]:
    """Load dataset from a CSV file.
    
    Args:
        filepath: Path to the CSV file
        
    Returns:
        List of (question, answer) tuples, including header
    """
    filepath = Path(filepath)
    data = []
    
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            data.append(tuple(row))
    
    return data


def save_to_json(data: List[dict], filepath: Union[str, Path]) -> None:
    """Save dataset to a JSON file.
    
    Args:
        data: List of dictionaries with question/answer keys
        filepath: Path to the output JSON file
    """
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_from_json(filepath: Union[str, Path]) -> List[dict]:
    """Load dataset from a JSON file.
    
    Args:
        filepath: Path to the JSON file
        
    Returns:
        List of dictionaries with question/answer keys
    """
    filepath = Path(filepath)
    
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def save_dataset(
    data: List[Tuple[str, str]],
    output_dir: Union[str, Path],
    task_name: str,
    difficulty: str,
    language: str,
    prefix: str = "",
    format: str = "csv",
) -> Path:
    """Save a dataset with standardized naming.
    
    Args:
        data: List of (question, answer) tuples
        output_dir: Output directory
        task_name: Name of the task (e.g., "date_addition")
        difficulty: Difficulty level (e.g., "medium")
        language: Language code (e.g., "en_US")
        prefix: Optional prefix for filename (e.g., "2025" for memorization)
        format: Output format ("csv" or "json")
        
    Returns:
        Path to the saved file
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Build filename
    if prefix:
        filename = f"{prefix}_{task_name}_{difficulty}_{language}.{format}"
    else:
        filename = f"{task_name}_{difficulty}_{language}.{format}"
    
    filepath = output_dir / filename
    
    if format == "csv":
        save_to_csv(data, filepath)
    elif format == "json":
        # Convert tuples to dicts for JSON
        json_data = []
        for i, row in enumerate(data):
            if i == 0:  # Skip header
                continue
            json_data.append({"question": row[0], "answer": row[1]})
        save_to_json(json_data, filepath)
    else:
        raise ValueError(f"Unsupported format: {format}. Use 'csv' or 'json'")
    
    return filepath


def ensure_directory(path: Union[str, Path]) -> Path:
    """Ensure a directory exists, creating it if necessary.
    
    Args:
        path: Directory path
        
    Returns:
        Path object for the directory
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path
