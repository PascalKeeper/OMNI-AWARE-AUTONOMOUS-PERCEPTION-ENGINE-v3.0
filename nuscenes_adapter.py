"""nuScenes mini adapter for the OMNI-AWARE benchmark harness.

Loads v1.0-mini from C:\\data\\sets\\nuscenes and yields one dictionary
per keyframe. Ground truth is in the ego frame used by the harness:

    x  forward (m)
    y  left (m)
    z  up (m)

car and truck map to vehicle. Pedestrians stay pedestrian. Barriers,
cones, and debris are obstacles. Every other category is skipped.
"""
import os
from collections import Counter

import numpy as np
from nuscenes.nuscenes import NuScenes
from nuscenes.utils.data_classes import Box
from pyquaternion import Quaternion

VERSION = "v1.0-mini"
DATAROOT = r"C:\data\sets\nuscenes"

# Midpoint of each nuScenes visibility bin. Ground truth is certain;
# the bin is kept so the annotation's visibility field is not dropped.
VISIBILITY_CONFIDENCE = {
    "v0-40": 0.20,
    "v40-60": 0.50,
    "v60-80": 0.70,
    "v80-100": 0.90,
}

STATS = {
    "skipped_samples": 0,
    "skipped_annotations": 0,
    "skipped_categories": Counter(),
    "mapped": Counter(),
}


def map_category(name: str):
    """Map a nuScenes category name onto an OMNI-AWARE type."""
    if name in ("vehicle.car", "vehicle.truck"):
        return "vehicle"
    if name.startswith("human.pedestrian."):
        return "pedestrian"
    if name in (
        "movable_object.barrier",
        "movable_object.trafficcone",
        "movable_object.debris",
    ):
        return "obstacle"
    return None


def lidar_point_count(path: str) -> int:
    """Number of points in a nuScenes .pcd.bin sweep (5 float32 fields)."""
    try:
        nbytes = os.path.getsize(path)
    except OSError:
        return 0
    if nbytes < 20:
        return 0
    if nbytes % 20 != 0:
        raw = np.fromfile(path, dtype=np.float32)
        return int(raw.size // 5)
    return nbytes // 20


def _visibility_confidence(nusc, ann) -> float:
    vis = nusc.get("visibility", ann["visibility_token"])
    return float(VISIBILITY_CONFIDENCE.get(vis.get("level", ""), 1.0))


def _ground_truth(nusc, sample) -> list:
    """Annotations in the ego frame at the lidar keyframe pose."""
    lidar_sd = nusc.get("sample_data", sample["data"]["LIDAR_TOP"])
    pose = nusc.get("ego_pose", lidar_sd["ego_pose_token"])
    pose_t = np.array(pose["translation"])
    pose_r = Quaternion(pose["rotation"]).inverse
    boxes = []
    for ann_token in sample["anns"]:
        ann = nusc.get("sample_annotation", ann_token)
        name = ann.get("category_name")
        if not name:
            name = nusc.get("category", ann["category_token"])["name"]
        omni_type = map_category(name)
        if omni_type is None:
            STATS["skipped_annotations"] += 1
            STATS["skipped_categories"][name] += 1
            continue
        box = Box(ann["translation"], ann["size"], Quaternion(ann["rotation"]))
        box.translate(-pose_t)
        box.rotate(pose_r)
        width, length, height = (float(v) for v in box.wlh)
        x, y, z = (float(v) for v in box.center)
        boxes.append(
            {
                "type": omni_type,
                "x": x,
                "y": y,
                "z": z,
                "width": width,
                "length": length,
                "height": height,
                "confidence": _visibility_confidence(nusc, ann),
            }
        )
        STATS["mapped"][omni_type] += 1
    return boxes


def build_frame(nusc, scene, sample):
    """One sample, or None when the front image or lidar sweep is unusable."""
    if "CAM_FRONT" not in sample["data"] or "LIDAR_TOP" not in sample["data"]:
        return None
    image_path, _, _ = nusc.get_sample_data(sample["data"]["CAM_FRONT"])
    lidar_path, _, _ = nusc.get_sample_data(sample["data"]["LIDAR_TOP"])
    if not image_path or not os.path.isfile(image_path) or os.path.getsize(image_path) == 0:
        return None
    if lidar_point_count(lidar_path) <= 0:
        return None
    return {
        "image_path": image_path,
        "lidar_path": lidar_path,
        "ground_truth": _ground_truth(nusc, sample),
        "timestamp": int(sample["timestamp"]),
        "sample_token": sample["token"],
        "scene_token": scene["token"],
        "scene_name": scene["name"],
        "scene_description": scene["description"],
    }


def open_nuscenes(dataroot: str = None, version: str = VERSION) -> NuScenes:
    root = dataroot or DATAROOT
    return NuScenes(version=version, dataroot=root, verbose=False)


def iter_frames(dataroot: str = None, version: str = VERSION):
    """Yield every usable keyframe in every scene."""
    nusc = open_nuscenes(dataroot, version)
    for scene in nusc.scene:
        token = scene["first_sample_token"]
        while token:
            sample = nusc.get("sample", token)
            frame = build_frame(nusc, scene, sample)
            if frame is None:
                STATS["skipped_samples"] += 1
            else:
                yield frame
            token = sample["next"]


def verify(dataroot: str = None, version: str = VERSION) -> dict:
    """Confirm the mini split shape and print the scene list."""
    root = dataroot or DATAROOT
    nusc = NuScenes(version=version, dataroot=root, verbose=True)
    cameras = set()
    lidars = set()
    radars = set()
    bad = []
    for sample in nusc.sample:
        cams, lids, rads = [], [], []
        for channel in sample["data"]:
            if channel.startswith("CAM_"):
                cams.append(channel)
            elif channel.startswith("LIDAR_"):
                lids.append(channel)
            elif channel.startswith("RADAR_"):
                rads.append(channel)
        cameras.update(cams)
        lidars.update(lids)
        radars.update(rads)
        if len(cams) != 6 or len(lids) != 1 or len(rads) != 5:
            bad.append(sample["token"])
    print(f"dataroot: {root}")
    print(f"version: {version}")
    print(f"scenes: {len(nusc.scene)}")
    print(f"samples: {len(nusc.sample)}")
    print(f"cameras: {len(cameras)} {sorted(cameras)}")
    print(f"lidars: {len(lidars)} {sorted(lidars)}")
    print(f"radars: {len(radars)} {sorted(radars)}")
    print(f"samples_missing_expected_sensors: {len(bad)}")
    print("scene list:")
    for scene in nusc.scene:
        print(f"  {scene['token']}  {scene['name']}  {scene['description']}")
    return {
        "scenes": len(nusc.scene),
        "samples": len(nusc.sample),
        "cameras": len(cameras),
        "lidars": len(lidars),
        "radars": len(radars),
        "bad_samples": bad,
    }


if __name__ == "__main__":
    report = verify()
    ok = (
        report["scenes"] == 10
        and report["samples"] == 404
        and report["cameras"] == 6
        and report["lidars"] == 1
        and report["radars"] == 5
        and not report["bad_samples"]
    )
    print("verification:", "PASS" if ok else "FAIL")
