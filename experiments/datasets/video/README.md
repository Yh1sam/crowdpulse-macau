# Video evaluation dataset

`yonge_dundas_raw.webm` — "Diagonal crosswalk at Yonge & Dundas in Toronto", Raysonho @ Open Grid Scheduler / Grid Engine,
Wikimedia Commons, **CC0** (public domain dedication). Source:
https://commons.wikimedia.org/wiki/File:DiagonalCrosswalkYongeDundas.webm

`yonge_dundas_640_10fps.mp4` — the same clip transcoded to 640×360, 10 fps, no audio (what the sensor pipeline consumes; also bundled in the iOS app as `sample_crowd.mp4` for video mode).

`frames/frame_NNN.png` — the hand-counted frames: video frame index 24 + 50·(N−1), i.e. **t = 2.4, 7.4, 12.4 … 52.4 s**.
Extract them with `ffmpeg -i yonge_dundas_640_10fps.mp4 -vf "select='eq(mod(n\,50)\,24)'" -vsync 0 frames/frame_%03d.png`.
(They were originally produced with `-vf fps=1/5`, which takes the last frame of each 5 s interval, not the frame at 0, 5, 10 s.
`experiments/video_eval.py` checks every frame pixel-for-pixel against its stated index and stops if they disagree.)

`ground_truth.csv` — manual counts per frame, cyclists included:
- `actual_count`: everyone visible (the far-sidewalk crowd ~50 m away is counted approximately, ±3).
- `near_count`: people whose feet are below y = 0.66 of frame height (near half of the crossing and camera-side corners, roughly within 20 m).
- `near_count_v1`: an earlier, looser "on the crossing" count kept for transparency; not used for scoring.

`counts_*.csv` — per-frame detector output from `ios/CrowdPulseSensor/Tools/videoeval` (one file per detector variant).
`boxes_*.json`, the video files and `frames/` are not committed (size); re-create with the commands in `experiments/video_eval.py --help`.
