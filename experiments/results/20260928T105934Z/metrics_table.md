# CrowdPulse evaluation (20260928T105934Z)

Model version: crowdpulse-clf-0.1  
Trained: 2026-09-28T10:56:10.887143+00:00  
Split days: {"train": ["2026-09-21", "2026-09-22", "2026-09-23", "2026-09-24", "2026-09-26", "2026-09-28", "2026-09-29", "2026-10-01", "2026-10-03"], "val": ["2026-09-25", "2026-10-02"], "test": ["2026-09-27", "2026-09-30", "2026-10-04"]}  
Rows: {"train": 53473, "val": 11866, "test": 17754, "stress": 5865}

| horizon | model | accuracy | precision (macro) | recall (macro) | F1 (macro) | ROC-AUC (ovr) | ECE | persistence F1 | acc vs ground truth | density MAE | stress-day F1 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| +5 min | random_forest | 0.969 | 0.884 | 0.898 | 0.890 | 0.992 | 0.004 | 0.842 | 0.973 | 0.018 | 0.620 |
| +10 min | random_forest | 0.965 | 0.873 | 0.888 | 0.880 | 0.990 | 0.007 | 0.812 | 0.967 | 0.020 | 0.638 |
| +15 min | random_forest | 0.963 | 0.865 | 0.881 | 0.873 | 0.989 | 0.009 | 0.779 | 0.967 | 0.021 | 0.609 |

Per-class (test):

| horizon | class | precision | recall | F1 | support |
|---|---|---|---|---|---|
| +5 min | SAFE | 0.996 | 0.988 | 0.992 | 14439 |
| +5 min | WARNING | 0.766 | 0.765 | 0.766 | 1129 |
| +5 min | CRITICAL | 0.889 | 0.939 | 0.913 | 1921 |
| +10 min | SAFE | 0.994 | 0.987 | 0.991 | 14322 |
| +10 min | WARNING | 0.737 | 0.746 | 0.742 | 1128 |
| +10 min | CRITICAL | 0.890 | 0.929 | 0.909 | 1917 |
| +15 min | SAFE | 0.994 | 0.986 | 0.990 | 14221 |
| +15 min | WARNING | 0.716 | 0.736 | 0.726 | 1128 |
| +15 min | CRITICAL | 0.884 | 0.923 | 0.903 | 1912 |
