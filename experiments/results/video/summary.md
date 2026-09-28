# Video count evaluation

Clip: CC0 Yonge & Dundas crossing, 640×360, 10 fps, 566 frames. Ground truth: 11 frames counted by hand (t = 2.4 + 5k s; alignment verified pixel-for-pixel; cyclists included). Near field = people whose feet are below y = 0.66 (near half of the crossing, roughly within 20 m); whole frame adds the far-sidewalk crowd (~50 m). "Found" = sum of estimates / sum of hand counts; above 100% means over-counting. With 11 labelled frames from one clip, differences of 1–2 people in MAE are within noise.

## Detectors at their default settings

| detector | median latency on Mac (ms) | near MAE | near bias | near found | near r | near MAE at line 0.63 / 0.69 | whole-frame MAE | whole-frame found |
|---|---|---|---|---|---|---|---|---|
| Apple built-in, upper body (previous default) | 5.4 | 3.0 | -3.0 | 55% | 0.96 | 3.0 / 3.0 | 38.8 | 9% |
| Apple built-in, full body | 5.2 | 5.5 | -5.5 | 16% | 0.69 | 5.5 / 5.5 | 41.4 | 3% |
| YOLO11n CoreML, conf 0.25 (new default) | 6.0 | 1.5 | -0.2 | 97% | 0.91 | 3.0 / 1.9 | 31.2 | 27% |
| YOLO11s CoreML, conf 0.25 | 8.4 | 1.6 | +0.0 | 100% | 0.85 | 3.7 / 2.3 | 31.5 | 26% |

## Where the errors come from (near field)

| detector | near bias, sparse frames (hand count < 10) | near found, dense frames (hand count ≥ 10) |
|---|---|---|
| Apple built-in, upper body (previous default) | -2.2 | 61% |
| Apple built-in, full body | -3.7 | 15% |
| YOLO11n CoreML, conf 0.25 (new default) | +0.4 | 82% |
| YOLO11s CoreML, conf 0.25 | +0.8 | 79% |

## Threshold sensitivity (not used to choose a setting)

| detector | median latency on Mac (ms) | near MAE | near bias | near found | near r | near MAE at line 0.63 / 0.69 | whole-frame MAE | whole-frame found |
|---|---|---|---|---|---|---|---|---|
| YOLO11n, conf 0.15 (sensitivity) | 6.9 | 1.5 | +1.1 | 116% | 0.93 | 4.2 / 1.5 | 26.0 | 39% |
| YOLO11n, conf 0.35 (sensitivity) | 5.4 | 1.4 | -1.0 | 85% | 0.90 | 2.5 / 2.5 | 34.2 | 19% |
