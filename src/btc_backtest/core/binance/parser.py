import io
import zipfile
from typing import Optional
import pandas as pd


def parse_kline_zip(zip_content: bytes) -> pd.DataFrame:
    """
    Unzips and parses a CSV kline file, returning it as a pandas DataFrame.
    If the content is b"404_NOT_FOUND", an empty DataFrame is returned.

    Expected columns in the CSV (in order, no header):
        0:  open_time (timestamp)
        1:  open (float)
        2:  high (float)
        3:  low (float)
        4:  close (float)
        5:  volume (float)
        6:  close_time (timestamp)
        7:  quote_asset_volume (float)
        8:  number_of_trades (int)
        9:  taker_buy_base_volume (float)
        10: taker_buy_quote_volume (float)
        11: ignore (float or unknown)

    The function:
      - Checks if zip_content equals b"404_NOT_FOUND" (early return with empty DataFrame).
      - Reads the in-memory bytes as a ZIP.
      - Reads the first CSV file in the ZIP (if multiple files exist, only the first is used).
      - Assigns column names as listed above.
      - Converts open_time and close_time to datetime.
      - Sets open_time as the DataFrame index and sorts the index.

    :param zip_content: The ZIP file content as bytes; may be b"404_NOT_FOUND".
    :return: A DataFrame with klines data or an empty DataFrame if content is 404 or invalid.
    """
    if zip_content == b"404_NOT_FOUND":
        return pd.DataFrame()

    in_memory_data = io.BytesIO(zip_content)

    with zipfile.ZipFile(in_memory_data) as zip_file:
        # List of files in the archive
        file_names = zip_file.namelist()

        # If the archive is empty, return an empty DataFrame
        if not file_names:
            return pd.DataFrame()

        # Extract the first CSV file
        csv_filename = file_names[0]

        with zip_file.open(csv_filename) as csv_file:
            df = pd.read_csv(csv_file, header=None)
            df.columns = [
                "open_time",
                "open",
                "high",
                "low",
                "close",
                "volume",
                "close_time",
                "quote_asset_volume",
                "number_of_trades",
                "taker_buy_base_volume",
                "taker_buy_quote_volume",
                "ignore",
            ]

    # Convert timestamps to datetime (Binance typically uses milliseconds for these fields)
    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms", errors="coerce")
    df["close_time"] = pd.to_datetime(df["close_time"], unit="ms", errors="coerce")

    df.set_index("open_time", inplace=True)
    df.sort_index(inplace=True)

    return df
