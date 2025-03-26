import os
from pathlib import Path

from btc_backtest.core.binance.cache_manager import CacheManager, load_checksums


def test_cache_manager_save_and_get_file(
    cache_manager: CacheManager,
    cache_dir: Path,
    checksums_file: Path
):
    """
    Test the entire workflow:
    1. Save a file => it should write the file to cache_dir + update checksums in checksums_file.
    2. Get the cached file => should return bytes if MD5 matches.
    """
    # 1) Save a file
    symbol = "BTCUSDT"
    interval = "1d"
    year = 2023
    month = 5
    test_content = b"hello world"

    cache_manager.save_file(symbol, interval, year, month, test_content)

    # Check that the file is indeed created
    local_path = cache_dir / "BTCUSDT-1d-2023-05.zip"
    assert local_path.exists(), "The ZIP file was not created in the cache directory."

    # Check that internal checksums now has an entry
    basename = os.path.basename(local_path)
    assert basename in cache_manager._checksums, "Checksums dictionary was not updated."

    # Verify checksums_file content
    written_text = checksums_file.read_text().strip()
    # Should be something like: "BTCUSDT-1d-2023-05.zip <md5hash>"
    assert basename in written_text, "checksums_file does not contain the filename."

    # 2) Get the cached file
    cached_content = cache_manager.get_cached_file(symbol, interval, year, month)
    assert cached_content is not None, "Expected to retrieve valid cached file content."
    assert cached_content == test_content, "Retrieved file content does not match the original."

def test_cache_manager_get_cached_file_missing(cache_manager: CacheManager):
    """
    If the file does not exist, get_cached_file should return None.
    """
    # We never saved anything, so it won't exist
    result = cache_manager.get_cached_file("BTCUSDT", "1d", 2023, 6)
    assert result is None, "Expected None since the file does not exist."

def test_cache_manager_get_cached_file_mismatched_md5(
    cache_manager: CacheManager,
    cache_dir: Path,
):
    """
    If the file exists but the stored MD5 does not match, get_cached_file should return None.
    """
    # Pre-populate the checksums dict with a WRONG MD5 for the target file
    cache_manager._checksums["BTCUSDT-1d-2023-07.zip"] = "wrongmd5"

    # Manually create the file in cache_dir
    local_file = cache_dir / "BTCUSDT-1d-2023-07.zip"
    content = b"some random data"
    local_file.write_bytes(content)

    # Attempt to retrieve
    result = cache_manager.get_cached_file("BTCUSDT", "1d", 2023, 7)
    assert result is None, (
        "Expected None because the stored MD5 doesn't match the actual MD5 of the file."
    )

def test_cache_manager_save_over_existing_file(cache_manager: CacheManager):
    """
    If a file already exists and we call save_file again,
    it should overwrite and update MD5 checksums accordingly.
    """
    symbol = "ETHUSDT"
    interval = "1d"
    year = 2023
    month = 1

    # First save
    original_content = b"original content"
    cache_manager.save_file(symbol, interval, year, month, original_content)

    # Overwrite with new content
    updated_content = b"updated content 123"
    cache_manager.save_file(symbol, interval, year, month, updated_content)

    # Retrieve again
    retrieved = cache_manager.get_cached_file(symbol, interval, year, month)
    assert retrieved == updated_content, "The file should have been overwritten with new content."
