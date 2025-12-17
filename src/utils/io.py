"""Safe file reading and writing utilities."""

from pathlib import Path
from typing import Union


def read_file(path: Union[str, Path], encoding: str = "utf-8") -> str:
    """Read text file contents safely.

    Args:
        path: Path to the file
        encoding: File encoding (default UTF-8)

    Returns:
        File contents as string

    Raises:
        FileNotFoundError: If file doesn't exist
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    with open(path, "r", encoding=encoding) as f:
        return f.read()


def write_file(
    path: Union[str, Path],
    content: str,
    encoding: str = "utf-8",
    create_parents: bool = True,
) -> Path:
    """Write text content to file safely.

    Args:
        path: Path to the file
        content: Content to write
        encoding: File encoding (default UTF-8)
        create_parents: Create parent directories if needed

    Returns:
        Path to the written file
    """
    path = Path(path)

    if create_parents:
        path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding=encoding) as f:
        f.write(content)

    return path


def ensure_dir(path: Union[str, Path]) -> Path:
    """Ensure a directory exists.

    Args:
        path: Path to the directory

    Returns:
        Path to the directory
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path

