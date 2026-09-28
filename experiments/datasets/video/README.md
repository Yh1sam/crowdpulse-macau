# Video evaluation dataset

`yonge_dundas_raw.webm` — "Diagonal crosswalk at Yonge & Dundas in Toronto", Raysonho @ Open Grid Scheduler / Grid Engine,
Wikimedia Commons, **CC0** (public domain dedication). Source:
https://commons.wikimedia.org/wiki/File:DiagonalCrosswalkYongeDundas.webm

`yonge_dundas_640_10fps.mp4` — the same clip transcoded to 640×360, 10 fps, no audio (what the sensor pipeline consumes).
`frames/frame_NNN.png` — one frame every 5 s (frame_001 = t 0 s, frame_002 = t 5 s, ...) used for manual ground-truth counting.
`ground_truth.csv` — manual person counts per sampled frame (see experiments/video_eval.py).

The raw file is not committed (size); re-create with the commands in `experiments/video_eval.py --help`.
