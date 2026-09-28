# Video count evaluation

Ground truth: 11 frames counted by hand (every 5 s). Near field = people on the crossing within ~15 m of the camera; whole frame also includes the far sidewalk (~50 m).

| variant | median latency (ms) | near-field MAE | near-field detected % | near-field r | whole-frame MAE | whole-frame detected % |
|---|---|---|---|---|---|---|
| 640px, upper-body (app default) | 7.1 | 7.0 | 34% | 0.60 | 38.4 | 8% |
| 640px, full-body | 7.4 | 9.5 | 7% | -0.02 | 41.2 | 2% |
| 1280px, upper-body | 7.9 | 7.0 | 35% | 0.59 | 38.3 | 9% |
| 1280px, full-body | 7.4 | 9.6 | 6% | 0.17 | 41.3 | 1% |
