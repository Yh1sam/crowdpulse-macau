# Mall dataset (person-counting benchmark)

**Not redistributed here.** The dataset is "for research purposes only and as such cannot be used commercially" (CUHK), which is not compatible with this repository's AGPL-3.0 licence, so the archive, frames, ground truth and per-frame outputs stay local (this folder is git-ignored except for this README). Only aggregate metrics and charts without dataset imagery are committed, in `experiments/results/mall/`.

- Source: <https://personal.ie.cuhk.edu.hk/~ccloy/downloads_mall_dataset.html>, file `mall_dataset.zip`, 91,833,998 bytes, SHA-256 `21baea1066ea1473289c28c2f9fc8440cea3c8d8905b83a66529fbef184d47e3`, downloaded 2026-10-12.
- Content: 2,000 frames (640×480, < 2 Hz) from a publicly accessible shopping-mall webcam, with the head position of every pedestrian in every frame (13–53 per frame, 62,315 in total).
- Cite: K. Chen, C. C. Loy, S. Gong and T. Xiang, "Feature Mining for Localised Crowd Counting", BMVC 2012; and K. Chen, S. Gong, T. Xiang and C. C. Loy, "Cumulative Attribute Space for Age and Crowd Density Estimation", CVPR 2013.

Reproduce:

```bash
curl -o experiments/datasets/mall/mall_dataset.zip https://personal.ie.cuhk.edu.hk/~ccloy/files/datasets/mall_dataset.zip
```

```bash
unzip -q experiments/datasets/mall/mall_dataset.zip -d experiments/datasets/mall
```

Then follow the commands at the top of `experiments/mall_eval.py` (wrap the frames into an MJPEG `.mov` without re-encoding, run the app's detectors with `videoeval`, score with `mall_eval.py`).
