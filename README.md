# San Onofre Surf Condition Forecasting

I'm building this project to forecast significant wave height near San Onofre
six hours ahead using historical wave observations and, where useful, weather
and tide data. I want to test whether machine learning can improve on a simple
baseline: predicting that wave height will stay the same over the next six hours.

## Current progress

I started by inspecting the 2023 observations from Green Beach Offshore
(CDIP 271 / NDBC 46277). The dataset contains 9,525 rows, missing wave measurements,
and irregular timestamps, including a gap of more than 19 days.

Further inspection shows that all four wave fields are missing together on
175 rows. Records with wave measurements use both 00/30 and 26/56 minutes
within the hour; some short intervals separate wave records from records
containing temperature but no wave measurements.

These observations describe offshore conditions rather than breaking-wave height
at San Onofre. Selecting the nearshore target location and investigating data
quality are the next steps. Model development has not started yet.

## Files

- `inspect_waves.py`: load the file and inspect timestamps, measurements, and missingness.
- `data/README.md`: data source, units, download command, and limitations.
- `requirements.txt`: Python dependencies.
- `.gitignore`: keep the local environment and downloaded data out of Git.

## Setup

From the project directory in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Download the dataset using the commands in [data/README.md](data/README.md), then
run the inspection:

```powershell
.\.venv\Scripts\python.exe inspect_waves.py
```

Verified with Python 3.10.6 and pandas 2.3.3.

## Planned evaluation

I plan to compare models against a persistence baseline using chronological
training and validation periods. Features must use information available at the
time of prediction, and a separate final test period will remain untouched during
feature selection and model tuning.

The 2023 data has already been used for exploratory analysis and will not serve
as an untouched final test set. Split dates will be chosen after confirming the
target dataset and its usable coverage.
