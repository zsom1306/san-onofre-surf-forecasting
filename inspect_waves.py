"""Inspect historical buoy observations for coverage, missing values, and time gaps."""

from pathlib import Path

import matplotlib
import pandas as pd

# Render saved figures without opening an interactive window.
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt

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

# Compare missingness across the four wave measurements within each row.
wave_columns = ["WVHT", "DPD", "APD", "MWD"]
missing_wave_cells = waves[wave_columns].isna()
any_wave_missing = missing_wave_cells.any(axis=1)
all_waves_missing = missing_wave_cells.all(axis=1)
partly_missing = any_wave_missing & ~all_waves_missing

print("\nWave measurement availability by row:")
print(f"All four present: {(~any_wave_missing).sum()}")
print(f"All four missing: {all_waves_missing.sum()}")
print(f"Only some missing: {partly_missing.sum()}")
print("\nFirst five rows with all four wave measurements missing:")
print(waves.loc[all_waves_missing, wave_columns + ["ATMP", "WTMP"]].head().to_string())

# Pair each record with its predecessor to locate gaps in the full record stream.
record_times = waves.index.to_series()
gaps = pd.DataFrame({
    "previous_time": record_times.shift(1),
    "current_time": record_times,
    "elapsed": record_times.diff(),
})
long_gaps = gaps.loc[gaps["elapsed"] > pd.Timedelta(minutes=30)]
print("\nFive longest intervals between records (UTC):")
print(long_gaps.sort_values("elapsed", ascending=False).head().to_string(index=False))

# Inspect the first short interval without assuming its cause.
short_steps = time_steps.loc[time_steps < pd.Timedelta(minutes=30)]
if not short_steps.empty:
    example_time = short_steps.index[0]
    window_start = example_time - pd.Timedelta(minutes=30)
    window_end = example_time + pd.Timedelta(minutes=30)
    print("\nRecords around the first interval shorter than 30 minutes (UTC):")
    print(waves.loc[window_start:window_end, wave_columns + ["ATMP", "WTMP"]].to_string())

# Compare the minute within each hour across both groups of records.
print("\nTimestamp minute counts for rows with all wave measurements present:")
print(waves.loc[~any_wave_missing].index.minute.value_counts().sort_index().to_string())
print("\nTimestamp minute counts for rows with all wave measurements missing:")
print(waves.loc[all_waves_missing].index.minute.value_counts().sort_index().to_string())

# Keep complete wave records separately; presence does not establish data quality.
wave_observations = waves.loc[~any_wave_missing, wave_columns].copy()
observation_times = wave_observations.index.to_series()
wave_time_steps = observation_times.diff().dropna()

print(f"\nWave observation table shape: {wave_observations.shape}")
print(f"Original measurement table shape: {waves.shape}")
print("\nAll time-step frequencies between wave observations:")
print(wave_time_steps.value_counts().sort_index().to_string())
print(f"Wave intervals shorter than 30 minutes: {(wave_time_steps < pd.Timedelta(minutes=30)).sum()}")
print(f"Wave intervals longer than 30 minutes: {(wave_time_steps > pd.Timedelta(minutes=30)).sum()}")

wave_gaps = pd.DataFrame({
    "previous_time": observation_times.shift(1),
    "current_time": observation_times,
    "elapsed": observation_times.diff(),
})
long_wave_gaps = wave_gaps.loc[wave_gaps["elapsed"] > pd.Timedelta(minutes=30)]
print("\nFive longest intervals between wave observations (UTC):")
print(long_wave_gaps.sort_values("elapsed", ascending=False).head().to_string(index=False))

# Summarize observed ranges before applying basic value checks.
range_summary = wave_observations.agg(["count", "min", "max"]).T
print("\nWave measurement ranges (WVHT: m; DPD/APD: s; MWD: degrees true):")
print(range_summary.to_string())

# These checks flag obvious violations, not every possible measurement error.
range_flags = pd.DataFrame({
    "negative_height": wave_observations["WVHT"] < 0,
    "nonpositive_dominant_period": wave_observations["DPD"] <= 0,
    "nonpositive_average_period": wave_observations["APD"] <= 0,
    "direction_outside_0_360": ~wave_observations["MWD"].between(0, 360, inclusive="both"),
})
flagged_rows = range_flags.any(axis=1)
print("\nNumber of violations for each basic value check:")
print(range_flags.sum().to_string())
print(f"Observations failing at least one check: {flagged_rows.sum()}")
if flagged_rows.any():
    print("\nFirst ten flagged observations:")
    print(wave_observations.loc[flagged_rows].head(10).to_string())
else:
    print("No observations violate these four checks; further quality assessment is still needed.")

# Start a new plotted run whenever successive wave observations are >30 min apart.
gap_before = observation_times.diff() > pd.Timedelta(minutes=30)
segment_ids = gap_before.cumsum()

fig, ax = plt.subplots(figsize=(12, 5), layout="constrained")
for segment_id, segment in wave_observations.groupby(segment_ids):
    ax.plot(segment.index, segment["WVHT"], color="#176B87",
            linewidth=0.7, marker=".", markersize=1.5)

# Highlight the largest gap; all other gaps also break the plotted line.
if not long_wave_gaps.empty:
    largest_gap = long_wave_gaps.sort_values("elapsed", ascending=False).iloc[0]
    ax.axvspan(largest_gap["previous_time"], largest_gap["current_time"],
               color="#E5E7EB", label="Longest gap: no wave observations")
    ax.legend(loc="upper left", frameon=False)

ax.set_title("Green Beach Offshore | CDIP 271 / NDBC 46277 | 2023\n"
             "Observed significant wave height; line breaks at gaps >30 minutes",
             fontsize=12, loc="left", pad=14)
ax.set_xlabel("Observation time (UTC)")
ax.set_ylabel("Significant wave height (m)")
ax.set_ylim(bottom=0)
ax.xaxis.set_major_locator(mdates.MonthLocator(tz="UTC"))
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y", tz="UTC"))
ax.grid(axis="y", alpha=0.25)
ax.spines[["top", "right"]].set_visible(False)

figure_path = Path(__file__).resolve().parent / "figures" / "wave_height_2023.png"
figure_path.parent.mkdir(exist_ok=True)
fig.savefig(figure_path, dpi=180)
plt.close(fig)
print(f"\nSaved wave-height plot: {figure_path}")
print(f"Plotted {len(wave_observations)} observations in {segment_ids.nunique()} separate runs.")

# Inspect a fixed window around the observed August peak, including both end dates.
event = wave_observations.loc["2023-08-19":"2023-08-23"].copy()
event_records = waves.loc["2023-08-19":"2023-08-23"]
expected_times = pd.date_range("2023-08-19", "2023-08-24", freq="30min",
                               inclusive="left", tz="UTC")
missing_times = expected_times.difference(event.index)
off_grid_times = event.index.difference(expected_times)

print(f"\nAugust 19-23: {len(event)} complete wave observations; {len(expected_times)} expected half-hour slots.")
print("Missing wave cells in the existing source rows in this window:")
print(event_records[wave_columns].isna().sum().to_string())
print(f"Expected timestamps without complete wave observations: {missing_times.tolist()}")
print(f"Wave timestamps outside this expected grid: {len(off_grid_times)}")

peak_time = event["WVHT"].idxmax()
print(f"\nFirst window maximum: {event.loc[peak_time, 'WVHT']:.2f} m at {peak_time}")
print("Measurements within one hour of the maximum:")
print(event.loc[peak_time - pd.Timedelta(hours=1):peak_time + pd.Timedelta(hours=1),
                ["WVHT", "DPD", "APD"]].to_string())

# Separate panels preserve each variable's units while sharing the same time axis.
event_fig, axes = plt.subplots(2, 1, figsize=(11, 7), sharex=True, layout="constrained")
for segment_id, segment in event.groupby(segment_ids.loc[event.index]):
    axes[0].plot(segment.index, segment["WVHT"], color="#176B87", marker=".", linewidth=1)
    axes[1].plot(segment.index, segment["DPD"], color="#176B87", marker=".", linewidth=1)
    axes[1].plot(segment.index, segment["APD"], color="#C46B24", marker=".", linewidth=1)

axes[0].set_ylabel("Significant wave height (m)")
axes[0].set_ylim(bottom=0)
axes[1].set_ylabel("Wave period (s)")
axes[1].set_ylim(bottom=0)
# The first two period lines represent DPD and APD in the first plotted run.
axes[1].legend(axes[1].lines[:2], ["Dominant period (DPD)", "Average period (APD)"],
               loc="lower left", frameon=False)
for ax in axes:
    ax.axvline(peak_time, color="#6B7280", linestyle="--", linewidth=0.8)
    ax.grid(axis="y", alpha=0.25)
    ax.spines[["top", "right"]].set_visible(False)

axes[1].set_xlabel("Observation time (UTC)")
axes[1].xaxis.set_major_locator(mdates.DayLocator(tz="UTC"))
axes[1].xaxis.set_major_formatter(mdates.DateFormatter("%b %d", tz="UTC"))
event_fig.suptitle("Green Beach Offshore | August 19-23, 2023\n"
                   "Dashed line: first height maximum; line breaks: gaps >30 minutes", fontsize=12)
event_figure_path = figure_path.parent / "wave_event_august_2023.png"
event_fig.savefig(event_figure_path, dpi=180)
plt.close(event_fig)
print(f"\nSaved event plot: {event_figure_path}")
