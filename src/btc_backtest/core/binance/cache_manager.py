import hashlib
import os
from typing import Dict, Optional


def load_checksums(checksums_file: str) -> dict[str, str]:
    """
    Loads checksums from a local file if it exists.
    File format: <filename> <md5hash>

    :param checksums_file: path to the file with checksums
    :return: a dictionary where the key is the filename and the value is its MD5 hash
    """
    checksums = {}
    if os.path.exists(checksums_file):
        with open(checksums_file, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split()
                if len(parts) == 2:
                    checksums[parts[0]] = parts[1]
    return checksums


class CacheManager:
    """
    Handles caching:
    - Stores downloaded ZIP files
    - Verifies MD5 checksums
    - Returns/updates content from local files
    """

    def __init__(
        self,
        checksums: Dict[str, str],
        cache_dir: str,
        checksums_file: str,
    ) -> None:
        """
        Initializes the cache manager.

        :param checksums: dictionary of filenames and their MD5 hashes
        :param cache_dir: path to the cache directory
        :param checksums_file: path to the file for storing checksums
        """
        self._cache_dir = cache_dir
        os.makedirs(self._cache_dir, exist_ok=True)
        self._checksums_file = checksums_file
        self._checksums = checksums

    def _save_checksums(self) -> None:
        """
        Saves the current state of checksums to self._checksums_file.
        """
        with open(self._checksums_file, "w") as f:
            for filename, md5hash in self._checksums.items():
                f.write(f"{filename} {md5hash}\n")

    def _compute_md5(self, content: bytes) -> str:
        """
        Computes the MD5 hash of the given content.

        :param content: bytes to hash
        :return: MD5 hash string
        """
        return hashlib.md5(content).hexdigest()

    def _get_local_zip_path(self, symbol: str, interval: str, year: int, month: int) -> str:
        """
        Generates the local path for the ZIP file in the format:
        <cache_dir>/<symbol>-<interval>-<year>-<month>.zip

        :param symbol: trading symbol
        :param interval: interval (e.g. 1d, 1m, etc.)
        :param year: year
        :param month: month
        :return: path to the ZIP file
        """
        filename = f"{symbol}-{interval}-{year}-{month:02d}.zip"
        return os.path.join(self._cache_dir, filename)

    def get_cached_file(
        self,
        symbol: str,
        interval: str,
        year: int,
        month: int
    ) -> bytes | None:
        """
        Checks if the local ZIP file exists and if its MD5 hash matches.
        Returns the file bytes if valid, otherwise None.

        :param symbol: trading symbol
        :param interval: interval (e.g. 1d, 1m, etc.)
        :param year: year
        :param month: month
        :return: file bytes or None if missing or invalid
        """
        local_path = self._get_local_zip_path(symbol, interval, year, month)
        if not os.path.exists(local_path):
            return None

        with open(local_path, "rb") as f:
            content = f.read()

        local_md5 = self._compute_md5(content)
        filename_only = os.path.basename(local_path)
        stored_md5 = self._checksums.get(filename_only)

        if stored_md5 and stored_md5 == local_md5:
            return content
        else:
            return None

    def save_file(
        self,
        symbol: str,
        interval: str,
        year: int,
        month: int,
        content: bytes
    ) -> None:
        """
        Saves the file to the local cache and updates the MD5 checksum.

        :param symbol: trading symbol
        :param interval: interval (e.g. 1d, 1m, etc.)
        :param year: year
        :param month: month
        :param content: file bytes (ZIP) to save
        """
        local_path = self._get_local_zip_path(symbol, interval, year, month)
        with open(local_path, "wb") as f:
            f.write(content)

        md5hash = self._compute_md5(content)
        self._checksums[os.path.basename(local_path)] = md5hash
        self._save_checksums()
