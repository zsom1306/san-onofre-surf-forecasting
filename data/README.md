# Data sources and initial findings

Sources verified on 2026-09-16. Downloaded files are stored unchanged in `raw/`.

## Offshore buoy observations

- Provider: Scripps/CDIP; distributed here through NOAA NDBC.
- Station: Green Beach Offshore, CDIP 271 / NDBC 46277.
- Current station metadata: 33.336 N, 117.659 W; water depth 303 m.
- [Station page](https://www.ndbc.noaa.gov/station_page.php?station=46277)
- [Historical listing](https://www.ndbc.noaa.gov/station_history.php?station=46277)
  listed annual standard meteorological files for 2023, 2024, and 2025.
- [Downloaded 2023 file](https://www.ndbc.noaa.gov/data/historical/stdmet/46277h2023.txt.gz)
- Retrieved 2026-09-16; compressed size 106598 bytes.
- SHA256: `a42dfee90316d72e8ff6a26d16fdc1b120e7c64f58a282627fbb14ee8bb735f7`.
- I selected this offshore station for the initial analysis and as a potential
  source of predictors. It does not directly measure surf at the beach. The
  station metadata above describes the current location; deployment locations
  still need to be checked before combining years.

Download from the project directory in PowerShell:

```powershell
New-Item -ItemType Directory -Force data/raw | Out-Null
Invoke-WebRequest -Uri 'https://www.ndbc.noaa.gov/data/historical/stdmet/46277h2023.txt.gz' -OutFile data/raw/46277h2023.txt.gz
```

The first line holds names; the second holds units. Times are UTC. The `.gz`
suffix means gzip compression; pandas decompresses it automatically.

| Field | Meaning | Units | Missing marker |
| --- | --- | --- | --- |
| #YY, MM, DD, hh, mm | Year, month, day, hour, minute | UTC date/time parts | Not expected |
| WVHT | Significant wave height | meters | 99.0 |
| DPD | Dominant wave period (maximum spectral energy) | seconds | 99.0 |
| APD | Average wave period | seconds | 99.0 |
| MWD | Direction waves at the dominant period come from | degrees clockwise from true north | 999 |
| ATMP, WTMP | Air and water temperature | degrees Celsius | 999.0 |
| WDIR | Wind direction | degrees true | 999 |
| WSPD, GST | Wind speed and gust | meters/second | 99.0 |
| PRES | Pressure | hPa | 9999.0 |
| DEWP | Dew point | degrees Celsius | 999.0 |
| VIS | Visibility | source header: mi | 99.0 |
| TIDE | Water level relative to MLLW | feet | 99.0 |

[NDBC field definitions and historical missing-data convention](https://www.ndbc.noaa.gov/faq/measdes.shtml).
Column presence does not guarantee observations exist. Missing wind or tide must
not be interpreted as calm wind or zero water level. The historical file is
post-processed; historical observation timestamps do not establish when each
value became available in real time. Reporting delays and revisions need to be
accounted for before evaluating performance under operational conditions.

## Additional CDIP sources

- [CDIP 271 historical metadata](https://thredds.cdip.ucsd.edu/thredds/dodsC/cdip/archive/271p1/271p1_historic.nc.das)
  labels its source `insitu observations`, gives nominal 30-minute resolution,
  and coverage 2023-05-26 18:00 UTC through 2025-01-14 19:59:59 UTC.
  This particular archive's coverage differs from the NDBC annual listings.
- [CDIP MOP documentation](https://cdip.ucsd.edu/MOP_v1.1/)
  describes modeled coastal waves derived using buoy input and wave propagation.
- [Transect definitions](https://cdip.ucsd.edu/MOP_v1.1/CA_v1.1_transect_definitions.txt)
  list a candidate in the San Onofre area, D1175: backbeach 33.37220,
  -117.56420; prediction point 33.36261, -117.57224; approximately 10 m depth.
  This is a geographic candidate, not a finalized match to a named surf break.
- [D1175 hindcast metadata](https://thredds.cdip.ucsd.edu/thredds/dodsC/cdip/model/MOP_alongshore/D1175_hindcast.nc.das)
  reports hourly resolution and coverage bounds 1999-12-31 23:30 UTC through
  2025-03-31 23:30 UTC. Coverage bounds describe time cells, not necessarily
  first/last observation labels; they do not prove complete valid coverage.
  Source is explicitly `model output`. Fields include `waveTime`, `waveHs`
  (m), `waveTp` and `waveTa` (s), `waveDp` (degrees true), `waveFlagPrimary`,
  and `waveFlagSecondary`.
- [MOP format and QC requirements](https://cdip.ucsd.edu/MOP_v1.1/MOP_netCDF.txt)
  require inspecting quality flags when loading modeled values.

The D1175 hindcast reconstructs past nearshore conditions using a wave model.
Using it as the target would measure agreement with modeled wave heights rather
than independently measured surf conditions. Reconstructed inputs may include
information unavailable at the nominal timestamp, so their availability and
temporal processing need to be checked before using them as features.

No external wind or tide dataset has been selected or downloaded. Their station
representativeness, historical coverage, units, and availability need separate
verification. Later annual buoy files were not opened for exploratory analysis.

## Initial inspection results

`inspect_waves.py` ran successfully against the downloaded snapshot:

- 9,525 rows, 18 original columns; 13 measurement columns after indexing by time.
- Actual rows span 2023-05-30 20:00 through 2023-12-31 23:56 UTC.
- No duplicate timestamps; 175 missing values in each wave parameter.
- Air temperature: 4,072 missing; water temperature: 1 missing.
- Wind direction/speed/gust, pressure, dew point, visibility, and tide: all missing.
- 9,350 nonmissing wave heights; mean 0.851 m, median 0.820 m,
  minimum 0.390 m, maximum 2.190 m (rounded).
- 9,189 successive intervals are 30 minutes; 159 are 26 minutes and 153 are
  4 minutes. There are 23 intervals longer than 30 minutes; the largest is
  19 days, 2 hours. These count timestamp intervals, not missing measurements.

The inspection preserves all rows and leaves missing values unfilled. The causes
of the irregular timestamps and remaining measurement quality issues still need
investigation. Forecast targets will need to be aligned by elapsed time because
twelve rows ahead does not reliably correspond to six hours ahead.
