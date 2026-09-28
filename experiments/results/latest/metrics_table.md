# CrowdPulse evaluation (20260928T111302Z)

Model version: crowdpulse-clf-0.1  
Trained: 2026-09-28T11:12:07.504976+00:00  
Split days: {"train": ["2026-09-21", "2026-09-22", "2026-09-23", "2026-09-24", "2026-09-26", "2026-09-28", "2026-09-29", "2026-10-01", "2026-10-03"], "val": ["2026-09-25", "2026-10-02"], "test": ["2026-09-27", "2026-09-30", "2026-10-04"]}  
Rows: {"train": 53459, "val": 11868, "test": 17728, "stress": 5865}

| horizon | model | accuracy | precision (macro) | recall (macro) | F1 (macro) | ROC-AUC (ovr) | ECE | persistence F1 | acc vs ground truth | density MAE | stress-day F1 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| +5 min | random_forest | 0.969 | 0.877 | 0.897 | 0.887 | 0.993 | 0.001 | 0.849 | 0.974 | 0.017 | 0.857 |
| +10 min | random_forest | 0.966 | 0.871 | 0.882 | 0.876 | 0.991 | 0.007 | 0.827 | 0.972 | 0.019 | 0.832 |
| +15 min | random_forest | 0.964 | 0.863 | 0.869 | 0.865 | 0.991 | 0.007 | 0.795 | 0.972 | 0.020 | 0.814 |

Per-class (test):

| horizon | class | precision | recall | F1 | support |
|---|---|---|---|---|---|
| +5 min | SAFE | 0.997 | 0.990 | 0.993 | 14748 |
| +5 min | WARNING | 0.780 | 0.791 | 0.785 | 1222 |
| +5 min | CRITICAL | 0.853 | 0.911 | 0.881 | 1435 |
| +10 min | SAFE | 0.995 | 0.990 | 0.993 | 14613 |
| +10 min | WARNING | 0.777 | 0.747 | 0.762 | 1224 |
| +10 min | CRITICAL | 0.840 | 0.909 | 0.873 | 1428 |
| +15 min | SAFE | 0.994 | 0.991 | 0.992 | 14505 |
| +15 min | WARNING | 0.773 | 0.708 | 0.739 | 1220 |
| +15 min | CRITICAL | 0.823 | 0.908 | 0.864 | 1427 |
