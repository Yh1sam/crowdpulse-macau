# Melbourne pedestrian counts (real data for the forecasting check)

City of Melbourne, **Pedestrian Counting System – Past Hour (counts per minute)** and **Pedestrian Counting System – Sensor Locations**, from the City of Melbourne open data platform (<https://data.melbourne.vic.gov.au>). Licence: **CC BY** (attribution: City of Melbourne). Retrieved with `experiments/melbourne_archive.py`.

Why: CrowdPulse's forecasting accuracy so far comes only from our own simulator. These are real pedestrian counts from 99 sensors, per minute or per 5 minutes depending on the sensor (see "Things to know"), so the same forecasting approach (+5 / +10 / +15 min, compared with a persistence baseline) can be checked on real crowd dynamics. They are not from Macau and they count people passing a sensor line rather than estimating density from a phone camera, so a result here supports the *method*, not CrowdPulse's accuracy in Macau.

## How it is collected

The API keeps only a short window of minute counts, refreshed about every 15 minutes. On 2026-10-12 the window started at 2026-10-11 13:55 UTC in every check from 10:26 to 14:18 UTC; at 14:18 it held 24 hours, and it did not empty at Melbourne midnight. `experiments/melbourne_archive.py` downloads the whole window and merges it into one gzipped CSV per UTC day, de-duplicated on `(location_id, sensing_datetime)`. Collection started on 2026-10-12; the first run was on a team Mac (`archive_log.mac.jsonl`), and since 2026-10-12 14:18 UTC it runs on the team's Linux server, which is the source of truth (`archive_log.jsonl`).

On the server (Ubuntu 24.04, Python 3.12): the script is at `/opt/crowdpulse-melbourne/melbourne_archive.py`, run by `crowdpulse-melbourne-archive.service` (a systemd one-shot service with a throw-away sandboxed user, `DynamicUser=yes`, writing only to `/var/lib/crowdpulse-melbourne`) from `crowdpulse-melbourne-archive.timer` (every hour at minute 50 UTC; missed runs are caught up after downtime). Replace `<server>` with the team's SSH login:

```bash
rsync -a --exclude .archive.lock <server>:/var/lib/crowdpulse-melbourne/ experiments/datasets/melbourne/
```

```bash
ssh <server> 'systemctl list-timers crowdpulse-melbourne-archive.timer; tail -3 /var/lib/crowdpulse-melbourne/archive_log.jsonl'
```

To stop collecting: `ssh <server> 'systemctl disable --now crowdpulse-melbourne-archive.timer'`. To run it by hand anywhere instead:

```bash
python3 experiments/melbourne_archive.py --out experiments/datasets/melbourne
```

## Files

| file | content |
|---|---|
| `minute/YYYY-MM-DD.csv.gz` | one row per sensor and reporting interval (one minute, or five minutes for most sensors; see below) with at least one pedestrian, filed by the UTC day of `sensing_datetime`: `location_id`, `sensing_datetime` (UTC), `sensing_date` / `sensing_time` (Melbourne local), `direction_1`, `direction_2`, `total_of_directions` |
| `sensors.csv` | sensor id, description, coordinates, direction names, status; refreshed daily |
| `archive_log.jsonl` | one line per server run: rows downloaded, new rows, the window's first and last minute, or the error. Gaps between one run's `last` and the next run's `first` are gaps in the archive. `archive_log.mac.jsonl` holds the first runs on a team Mac. |

In git: `sensors.csv` and the `minute/` files of 11-12 Oct 2026 (UTC) are committed, so the video's S16 renders from a fresh clone. They are a snapshot; the server keeps archiving. The analysis commits every data file it uses: the `minute/` files, `sensors.csv` and the archive logs `archive_log.jsonl` and `archive_log.mac.jsonl`. The logs decide which 5-minute bins count as covered, so without them a clone would get different coverage. `manifest.json` in the results lists the SHA-256 of each of these files, and `coverage.csv` lists the covered time intervals, so readers can see which hours the archive held.

## Things to know before analysing

Corrected on 16 Oct 2026: an earlier version said every sensor reports per minute and that any missing minute means zero. That is wrong for most sensors. Figures below are from the committed files of 11-12 Oct (UTC).

- **Two reporting intervals.** 57 of the 99 sensors wrote rows only at minutes divisible by 5 (:00, :05, ...; all of their rows). The other 42 wrote rows at any minute, with 18-31% of their rows on a 5-minute mark, close to the one in five expected for per-minute data. A 5-minute sensor's row is about the size of a per-minute sensor's 5-minute sum (daytime medians 27 and 39 people per 5 minutes, 10:00-18:00 Melbourne time on 12 Oct), so each row looks like a 5-minute total. The data do not say whether its timestamp marks the start or the end of those 5 minutes. `experiments/melbourne_eval.py` labels a sensor "5 min" if at least 99% of its rows fall on 5-minute marks and lists the label per sensor in its output.
- **When a missing row means zero.** A sensor writes a row only for an interval in which someone passed it; rows with a total of 0 are rare (1 of 52,682). So, for a working sensor, a missing minute (per-minute sensor) or a missing 5-minute mark (5-minute sensor) means zero. The minutes between a 5-minute sensor's marks are never reported and are **not** zeros. Summing every sensor into 5-minute bins treats both kinds alike: a 5-minute bin with no row is zero, but only if (a) the archive's download windows covered all five of its minutes (`archive_log*.jsonl`; a gap in the archive is missing data, not zero), and (b) the sensor was working.
- **Outages are not flagged.** `sensors.csv` gives status "A" for all 134 sensors, so it cannot show an outage. Long empty stretches in the daytime can: sensor 21 had rows every 5 minutes until 10:45 on 12 Oct (Melbourne time), none for the 33 marks from 10:50 to 13:30, then 90 people at 13:35. The pre-registered analysis below drops such sensor-days by a fixed rule.
- **Time zones.** `sensing_datetime` is UTC. Melbourne is on AEDT (UTC+11) from 4 Oct 2026 to 4 Apr 2027 (Python's `zoneinfo` database, `Australia/Melbourne`), and the files' own `sensing_date` / `sensing_time` columns agree. Day files are UTC days, so `minute/2026-10-12.csv.gz` holds 12 Oct 11:00 to 13 Oct 10:59 Melbourne time.
- The city notes duplicate records for sensors 67, 68 and 69; the archive keeps one row per sensor and timestamp (7 duplicates removed in the first download).
- **Seen before the pre-registration.** The 11-12 Oct files (12 Oct 00:55 to 13 Oct 00:55 Melbourne time) were rendered in video shot S16 and were used on 16 Oct 2026 to write the data notes above and the data rules below. They fall in the training period only.
- Counts are people crossing a line, in two directions. CrowdPulse's zones use a density index; the count-to-level mapping is fixed in the section below.

## Pre-registered analysis (committed 16-17 Oct 2026, before the test window)

**Status.** Written on 16 Oct 2026, before any count from the test window existed. The lead commits this section on 16-17 Oct 2026 (Macau time) and pushes it to the team's public GitHub repository before the test window opens at **18 Oct 2026 00:00 Melbourne time (AEDT, UTC+11) = 17 Oct 13:00 UTC = 17 Oct 21:00 Hong Kong / Macau time**. Until then the team may amend it only by a dated commit pushed before that time (point 9). The commit that fixes or amends this section also updates `PREREG_SHA256` in `experiments/melbourne_eval.py` (run `--print-prereg-hash` and paste the value) and includes `experiments/melbourne_eval.py` itself. Merges are fast-forward only: a squash or a rebase gives the commit a new date, and the real run then refuses if that date is after the window opened. `experiments/melbourne_eval.py` implements this section exactly. It stores a SHA-256 hash of the section's text, from this heading to the next `## ` heading. Its real run refuses to start if the text differs from that hash, has uncommitted edits, or was last changed by a commit dated after the window opened. It also reports whether that commit is on a remote branch, and which (`pushed_to_remote` in the results).

**Seen before this section was committed.** The dry run (`--dry-run`, 16 Oct) uses only the 11-12 Oct minute files (with the archive logs and `sensors.csv`) and trains and scores on the same bins. Its output (`experiments/results/melbourne_dryrun/`) is therefore not a result, and it does not evaluate the verdict. A test of the real-run code path was also seen. It used the same files with a shifted split (train before 17:00 and test from 17:00 to midnight Melbourne time on 12 Oct, sensor minimum lowered to 100 bins, output not kept), and the model scored below persistence there. After these were seen, a review on 16 Oct led to the following changes. None of them changes the data rules, mapping, features, model, primary outcome or decision rule. They are: the failure-case wording (point 8); per-class intervals, a secondary interval with sensor blocks, and the horizon of the per-day results (points 7 and 8); committing and hashing the archive logs (points 1 and 8); listing sensors with no rows (point 3); the tie rule (point 5); stating that all 24 hours are used and what happens if data at the window's end are lost (point 2); and these two paragraphs.

**Question.** On real pedestrian counts, does the CrowdPulse forecasting method predict a sensor's level 15 minutes ahead better than "nothing changes"?

**1. Data and unit**

- Data: every `minute/*.csv.gz` file up to and including UTC day 2026-10-22, from the server's archive (rsync as above), with `sensors.csv` and the archive logs `archive_log.jsonl` (server) and `archive_log.mac.jsonl` (first runs on a team Mac). All of them are committed with the results.
- Unit: the 5-minute total per sensor, i.e. the sum of `total_of_directions` over rows with `sensing_datetime` in [b, b + 5 min), where b is a UTC 5-minute mark. Forecast origin t is a complete bin; the horizons +5, +10 and +15 min are 1, 2 and 3 bins ahead.
- Covered bins: a bin is covered if the download windows of successful runs in the archive logs (each from its `first` to its `last` minute) include all five of its minutes. Only if no `archive_log*.jsonl` file is present at all is a bin covered if it and the next bin each hold at least one row from any sensor. Uncovered bins are missing. A covered bin with no row for a sensor counts as 0 for that sensor.
- Outage rule: a sensor-day (a sensor on one Melbourne calendar date) is dropped, with all its bins set to missing, if between 08:00 and 20:00 Melbourne time the sensor has a run of 24 or more covered bins (2 hours) with a total of 0. Uncovered bins neither break nor extend a run.

**2. Training and test split**

- Training period: every bin before 18 Oct 2026 00:00 AEDT (17 Oct 13:00 UTC). A training row needs both its origin bin and its target bin in this period.
- Test period: the Melbourne calendar days 18, 19, 20, 21 and 22 Oct 2026 (Sunday to Thursday), i.e. 17 Oct 13:00 UTC to 22 Oct 13:00 UTC. A test row has its origin bin in this period and its target bin ending by 22 Oct 13:00 UTC. Its lag inputs may come from 17 Oct, because they are known at forecast time.
- All 24 hours of every day are used, in training and in test.
- The window is not moved, shortened or extended, whatever the coverage. Coverage of each test day is reported. The real run waits until the archive reaches the window's end. If those data are permanently lost (for example, a server outage that outlasts the API's 24-hour window), the run is started with `--allow-short-window "reason"`: the window stays as defined, the missing bins are missing, and the report lists this as a deviation with the reason.

**3. Sensor inclusion** (decided from training data only)

A sensor is included if it has (a) at least 576 non-missing training bins (two full days), (b) a WARNING threshold T_W of at least 5 people per 5 minutes, so that its levels are not decided by one or two people, and (c) T_C > T_W, so that WARNING can occur. Sensors with no training data, and sensors listed in `sensors.csv` that have no rows in the data files, are excluded. Every excluded sensor is listed with its reason.

**4. Count-to-level mapping** (fitted per sensor on training bins only)

- p_W = 14,505 / 17,152 ≈ 0.8457 and p_C = 1 − 1,427 / 17,152 ≈ 0.9168. These are the share of SAFE rows and the share of SAFE + WARNING rows in the simulator's +15-min test set (`ml/models/metrics.json`, `per_horizon.h15.test.support`: SAFE 14,505, WARNING 1,220, CRITICAL 1,427).
- T_W and T_C are the p_W- and p_C-quantiles of the sensor's training 5-minute totals. They use numpy's `inverted_cdf` method: the smallest observed total with at least that share of training bins at or below it.
- A 5-minute total c is CRITICAL if c ≥ T_C, WARNING if T_W ≤ c < T_C, and SAFE otherwise.
- Why this mapping: Melbourne has no density index and no published crowding thresholds for these footpaths, so any fixed count would be invented. Per-sensor percentiles make a busy CBD sensor and a quiet one comparable. They also do not depend on a sensor's scale, so it does not matter whether a row is a 1-minute or a 5-minute total. Matching the simulator test set's class shares gives both tests approximately the same base rates (ties at a threshold count as the higher level; realised training shares are reported) for macro-F1, the simulator's headline metric (+15 min: model 0.865, persistence 0.795, same file). The two results still come from different data and labels, so neither number is a calibration of the other. Two options were rejected. The simulator's training shares (88.4 / 6.3 / 5.2%) were rejected because the simulator's headline comes from its test set. A "busy-hour" reference was rejected because it would need another arbitrary definition.
- Meaning: in Melbourne, WARNING means "in about the top 15% of this sensor's own training 5-minute totals" and CRITICAL "in about the top 8%". These are relative busyness levels, **not** safety levels. The names are shared only so that the same classifier and metric code applies.

**5. Model**

- Features: only counts, and only the sensor's own 5-minute totals. Each total c becomes a level index u = (number of that sensor's training bins with a total ≤ c) / (number of its training bins). The features are u_t, u_t−1, u_t−2, u_t−3, u_t − u_t−1 and u_t − u_t−3. They are the count versions of `density`, `density_lag1`-`3`, `density_change_1` and `density_change_3` in `ml/pipeline/features.py`. The model gets no time of day, calendar, weather, neighbouring sensors or sensor identity. A row needs all of c_t−3 ... c_t and its target.
- Classifier: one per horizon, pooled over all included sensors. It is the random forest of `make_models()` in `ml/training/train.py`: `SimpleImputer(strategy="median")` then `RandomForestClassifier(n_estimators=300, min_samples_leaf=5, class_weight="balanced_subsample", random_state=0, n_jobs=-1)`, scikit-learn 1.9.1 (`uv.lock`). The ml/ code picks among three models on validation days and may calibrate probabilities. Here the random forest is fixed in advance, because ml/ chose it at all three horizons. There is no model selection, tuning or calibration, and no validation split, so every training day is used for fitting. The prediction is the class with the highest forest probability; ties go to the first of SAFE, WARNING, CRITICAL.

**6. Baselines** (scored on the same rows)

- Persistence ("nothing changes"): the level at t + h is the level at t.
- Moving-average persistence: the level of the mean of c_t, c_t−1 and c_t−2 (the last 15 minutes), with the same thresholds.

**7. Primary outcome and decision rule**

- Primary outcome: macro-F1 over SAFE / WARNING / CRITICAL at +15 min, model minus persistence, on all test rows pooled. Macro-F1 is `classification_metrics` in `ml/pipeline/metrics.py` (scikit-learn `f1_score`, all three labels, `average="macro"`, `zero_division=0`).
- 95% interval: block bootstrap with sensor-days as blocks (sensor × Melbourne date of the origin bin), 2,000 resamples, seed 0, percentile interval. The same resampled blocks are used for every method.
- Secondary interval: the same bootstrap with sensors as blocks (all of a sensor's test days resampled together; 2,000 resamples, seed 0), reported alongside the primary interval for every difference. It does not decide the verdict.
- **The model beats persistence** if the primary interval's lower bound is above 0. **It is worse than persistence** if the upper bound is below 0. Otherwise there is **no clear difference**. There is no minimum effect size: the difference and its interval are always reported. Only this comparison decides the headline. Everything else is secondary.

**8. Reported whatever the result** (written to `experiments/results/melbourne/` and committed with the data files it used)

- the primary difference, its interval and the verdict;
- macro-F1, accuracy and per-class precision / recall / F1 for the model and both baselines at all three horizons, with bootstrap intervals, and their confusion matrices, as counts and as each true level's shares (the shares with bootstrap intervals);
- the model against moving-average persistence at +15 min, with the same intervals and rule, as a secondary outcome;
- results per test day and per reporting interval (1-minute and 5-minute sensors), at +15 min;
- the included and excluded sensors and dropped sensor-days, with reasons; the archive coverage of each test day; and the class shares in training and test at +15 min;
- one failure case: among test sensor-days whose true levels include all three classes, the one with the lowest +15-min macro-F1 of the model minus that of persistence (if the model is ahead on every one, this is its smallest margin, and the report says so);
- every deviation from this section, with its reason;
- the SHA-256 of every data file used (minute files, archive logs and `sensors.csv`), and whether the commit that fixed this section is on a remote branch, and which.

Video shot S16 reports the +15-min macro-F1 of the model and of persistence and the verdict, whichever way it comes out (`docs/video/script.md`, section 5B).

**9. Amendments**

The section can be amended only before the test window opens, and only by a dated git commit pushed to the public GitHub repository before then. That commit edits this section, updates `PREREG_SHA256` in `experiments/melbourne_eval.py` (`--print-prereg-hash` prints the new value), includes that script, and gives the reason in its message. Merges are fast-forward only, so the commit keeps its date. A committer date can be set by hand, so the script's date check is not proof on its own; the push to the public repository is what lets the date be checked from outside. Once the window opens, this section is frozen. Any later change to the analysis code is listed in the results as a deviation, with its reason.

**10. Known limits**

The data are not from Macau and count people crossing a line, not density. The training period is short (about six days, 12-17 Oct). Sensor-day blocks ignore correlation within one sensor across days and city-wide effects shared by all sensors on one day; for these reasons the sensor-block interval and the per-day results are reported alongside the pooled interval. The levels are relative to each sensor's own training period.
