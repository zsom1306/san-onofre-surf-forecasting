"""Inspect historical buoy observations for coverage, missing values, and time gaps."""

from pathlib import Path

import pandas as pd

# Locate the data beside this script, regardless of the terminal's directory.
data_path = Path(__file__).resolve().parent / "data" / "raw" / "46277h2023.txt.gz"

# NDBC historical missing-value markers are specific to each column.
# A global marker list could also erase valid directions such as 99 degrees.
missing_values = {
    "WDIR": 999, "WSPD": 99.0, "GST": 99.0,
    "WVHT": 99.0, "DPD": 99.0, "APD": 99.0, "MWD": 999,
    "PRES": 9999.0, "ATMP": 999.0, "WTMP": 999.0,
    "DEWP": 999.0, "VIS": 99.0, "TIDE": 99.0,
}

# Row 0 contains column names; row 1 contains units, not observations.
raw = pd.read_csv(data_path, sep=r"\s+", skiprows=[1], na_values=missing_values)

date_parts = raw[["#YY", "MM", "DD", "hh", "mm"]].rename(columns={
    "#YY": "year", "MM": "month", "DD": "day", "hh": "hour", "mm": "minute",
})
timestamps = pd.to_datetime(date_parts, utc=True)

# Replace the five date-part columns with one chronological row index.
waves = raw.drop(columns=["#YY", "MM", "DD", "hh", "mm"])
waves.index = pd.DatetimeIndex(timestamps, name="time_utc")
waves = waves.sort_index()

print(f"Raw shape (rows, columns): {raw.shape}")
print(f"Measurement table shape: {waves.shape}")
print(f"Columns: {waves.columns.tolist()}")
print(f"UTC coverage: {waves.index.min()} to {waves.index.max()}")
print(f"Duplicate timestamps: {waves.index.duplicated().sum()}")

print("\nFirst five rows (selected measurements):")
print(waves[["WVHT", "DPD", "APD", "MWD", "ATMP", "WTMP"]].head().to_string())

print("\nMissing values per measurement column:")
print(waves.isna().sum().to_string())

print("\nWave-height summary, in meters (missing values excluded):")
print(waves["WVHT"].describe().round(3).to_string())

# A missing row is different from a missing value in a row that exists.
time_steps = waves.index.to_series().diff().dropna()
print("\nMost common time steps between successive rows:")
print(time_steps.value_counts().head().to_string())
print(f"Gaps longer than 30 minutes: {(time_steps > pd.Timedelta(minutes=30)).sum()}")
print(f"Largest time step: {time_steps.max()}")
