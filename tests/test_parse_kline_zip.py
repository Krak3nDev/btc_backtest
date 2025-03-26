import io
import zipfile
import pandas as pd
import pytest

from btc_backtest.core.binance.parser import parse_kline_zip


def test_parse_kline_zip_404_not_found():
    """
    If the content is exactly b"404_NOT_FOUND",
    parse_kline_zip should return an empty DataFrame.
    """
    df = parse_kline_zip(b"404_NOT_FOUND")
    assert isinstance(df, pd.DataFrame)
    assert df.empty, "Expected an empty DataFrame for 404_NOT_FOUND."


def test_parse_kline_zip_empty_zip():
    """
    If the ZIP file is empty (no files inside),
    parse_kline_zip should return an empty DataFrame.
    """
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, mode="w") as zf:
        pass  # Create an empty ZIP

    df = parse_kline_zip(buf.getvalue())
    assert isinstance(df, pd.DataFrame)
    assert df.empty, "Expected an empty DataFrame for an empty ZIP."


def test_parse_kline_zip_valid_csv():
    """
    If the ZIP file contains a valid CSV kline file,
    parse_kline_zip should return a DataFrame with the expected columns & data.
    """
    # Sample CSV data; two rows with millisecond timestamps
    csv_content = b"""1640995200000,42,45,40,44,1000,1640995260000,40000,123,555,666,0
1640995260000,44,46,44,45,500,1640995320000,22500,55,333,444,0
"""

    buf = io.BytesIO()
    # Create a ZIP in memory with a single CSV file
    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("kline_data.csv", csv_content)

    df = parse_kline_zip(buf.getvalue())

    # Check that we got a DataFrame with data
    assert not df.empty, "Expected non-empty DataFrame for valid CSV data."
    # The function sets open_time as index, so check that
    assert df.index.name == "open_time", "Expected 'open_time' to be the index."

    # Verify column presence (besides the index)
    expected_cols = [
        "open", "high", "low", "close", "volume",
        "close_time", "quote_asset_volume", "number_of_trades",
        "taker_buy_base_volume", "taker_buy_quote_volume", "ignore"
    ]
    for col in expected_cols:
        assert col in df.columns, f"Missing expected column: {col}"

    # Confirm the index is datetime
    assert pd.api.types.is_datetime64_any_dtype(df.index), "open_time should be converted to datetime."
    # Optionally, check that close_time is also datetime
    assert pd.api.types.is_datetime64_any_dtype(df["close_time"]), "close_time should be converted to datetime."


def test_parse_kline_zip_multiple_files():
    """
    If the ZIP file has multiple files, parse_kline_zip should parse only the first file.
    """
    csv_content_1 = b"1640995200000,42,45,40,44,1000,1640995260000,40000,123,555,666,0"
    csv_content_2 = b"This is some other CSV file that shouldn't be read."

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("first.csv", csv_content_1)
        zf.writestr("second.csv", csv_content_2)  # The function should ignore this

    df = parse_kline_zip(buf.getvalue())

    # Expect exactly 1 row from 'first.csv'
    assert len(df) == 1, "Expected parse_kline_zip to read only the first file in the ZIP."
    first_row = df.iloc[0]
    assert first_row["open"] == 42, "Parsed data mismatch from the first CSV file."
