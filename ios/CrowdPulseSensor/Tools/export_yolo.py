"""Export a YOLO11 detector to CoreML (with a built-in NMS stage) for the sensor app.

The resulting .mlpackage takes an RGB image plus `iouThreshold` / `confidenceThreshold`
inputs and returns `confidence` (N x 80 COCO classes) and `coordinates` (N x 4); Vision
wraps it as VNRecognizedObjectObservations. The app keeps only the "person" class.

Licence: Ultralytics YOLO11 weights are AGPL-3.0. Fine for an open-source hackathon
prototype; a closed-source or App Store deployment needs an Ultralytics enterprise licence
or a permissively licensed detector (see docs/model-card.md).

Environment (coremltools 9.0 fails with torch >= 2.8 / numpy >= 2.3):
    uv venv --python 3.12 yolo-env
    uv pip install --python yolo-env/bin/python ultralytics coremltools "numpy<2.3" "torch==2.7.1" "torchvision==0.22.1"
    yolo-env/bin/python ios/CrowdPulseSensor/Tools/export_yolo.py --weights yolo11n.pt --out ios/CrowdPulseSensor/Resources
"""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from ultralytics import YOLO


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--weights", default="yolo11n.pt")
    ap.add_argument("--imgsz", type=int, default=640)
    ap.add_argument("--out", default="ios/CrowdPulseSensor/Resources")
    args = ap.parse_args()
    exported = Path(YOLO(args.weights).export(format="coreml", nms=True, imgsz=args.imgsz, half=True))
    dest = Path(args.out) / exported.name
    if dest.exists():
        shutil.rmtree(dest)
    shutil.move(str(exported), dest)
    print("wrote", dest)


if __name__ == "__main__":
    main()
