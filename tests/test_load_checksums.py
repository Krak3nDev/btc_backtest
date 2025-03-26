import os
import pytest
from pathlib import Path

from btc_backtest.core.binance.cache_manager import load_checksums


def test_load_checksums_file_does_not_exist():
    """
    If the file does not exist, load_checksums should return an empty dict.
    """
    non_existent_file = "definitely_not_existing_checksums.txt"
    # Ensure it doesn't exist in case we are re-running tests
    if os.path.exists(non_existent_file):
        os.remove(non_existent_file)

    result = load_checksums(non_existent_file)
    assert isinstance(result, dict), "Should return a dictionary regardless."
    assert len(result) == 0, "Expected empty dict when the file does not exist."


def test_load_checksums_file_empty(tmp_path: Path):
    """
    If the file is empty (or has no valid lines), we should get an empty dict.
    """
    empty_file = tmp_path / "checksums_empty.txt"
    empty_file.touch()  # Create an empty file

    result = load_checksums(str(empty_file))
    assert isinstance(result, dict), "Should return a dictionary."
    assert len(result) == 0, "Expected empty dict for an empty file."


def test_load_checksums_file_valid(tmp_path: Path):
    """
    Checks if we correctly parse the checksums file when it has valid lines.
    """
    checksums_file = tmp_path / "checksums_valid.txt"
    sample_data = """file1.zip abc123
file2.zip def456
file3.zip 789fff
"""
    checksums_file.write_text(sample_data)

    result = load_checksums(str(checksums_file))
    expected = {
        "file1.zip": "abc123",
        "file2.zip": "def456",
        "file3.zip": "789fff"
    }
    assert result == expected, "Parsed checksums do not match expected data."


def test_load_checksums_file_mixed_lines(tmp_path: Path):
    """
    If the file contains both valid and invalid lines, we skip the invalid ones.
    Valid lines are exactly "<filename> <md5hash>" with two parts.
    """
    checksums_file = tmp_path / "checksums_mixed.txt"
    sample_data = """file1.zip 123abc
INVALID_LINE
file2.zip def456 extra_part
 file3.zip 789fff  # leading space, but also more than 2 parts
file4.zip 112233
"""
    checksums_file.write_text(sample_data)

    # Only "file1.zip 123abc" and "file4.zip 112233" have exactly two parts
    result = load_checksums(str(checksums_file))
    expected = {
        "file1.zip": "123abc",
        "file4.zip": "112233",
    }
    assert result == expected, "Should ignore invalid or malformed lines."
