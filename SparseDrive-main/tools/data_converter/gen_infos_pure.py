#!/usr/bin/env python3
"""
Two-phase nuScenes info generator for SparseDrive.
Phase 1: filter large JSONs via streaming
Phase 2: load filtered data, build and save pkl (val first, then train)
Peak memory < 1.5GB.
"""

import json, os, pickle, sys, time, argparse, gc
import numpy as np
from collections import defaultdict

try:
    import ijson
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "ijson", "-q"])
    import ijson


def q2mat(q):
    w, x, y, z = q
    return np.array([
        [1-2*y*y-2*z*z, 2*x*y-2*w*z, 2*x*z+2*w*y],
        [2*x*y+2*w*z, 1-2*x*x-2*z*z, 2*y*z-2*w*x],
        [2*x*z-2*w*y, 2*y*z+2*w*x, 1-2*x*x-2*y*y],
    ], dtype=np.float32)


CAM_ORDER = ["CAM_FRONT", "CAM_FRONT_LEFT", "CAM_FRONT_RIGHT",
             "CAM_BACK", "CAM_BACK_LEFT", "CAM_BACK_RIGHT"]


def phase1(data_root, version, tmp_dir):
    jd = os.path.join(data_root, version)
    os.makedirs(tmp_dir, exist_ok=True)
    t0 = time.time()

    kf_path = os.path.join(tmp_dir, "keyframes.jsonl")
    open(kf_path, "w").close()

    ego_needed = set()
    print("[Ph1] sample_data.json -> keyframes...")
    with open(os.path.join(jd, "sample_data.json"), "rb") as fin:
        for item in ijson.items(fin, "item"):
            if item.get("is_key_frame") is True:
                e = {"token": item["token"], "channel": item.get("channel", ""),
                     "sample_token": item.get("sample_token", ""),
                     "ego_pose_token": item.get("ego_pose_token", ""),
                     "calibrated_sensor_token": item.get("calibrated_sensor_token", ""),
                     "filename": item.get("filename", ""),
                     "timestamp": item.get("timestamp", 0),
                     "prev": item.get("prev", "")}
                with open(kf_path, "a") as f:
                    f.write(json.dumps(e) + "\n")
                if e["ego_pose_token"]:
                    ego_needed.add(e["ego_pose_token"])

    print("[Ph1] Prev-chain ego tokens...")
    lidar_map = {}
    with open(os.path.join(jd, "sample_data.json"), "rb") as fin:
        for item in ijson.items(fin, "item"):
            if item.get("channel") == "LIDAR_TOP":
                lidar_map[item["token"]] = {
                    "prev": item.get("prev", ""),
                    "ego_pose_token": item.get("ego_pose_token", "")}

    kf_lidar = []
    with open(kf_path) as f:
        for line in f:
            item = json.loads(line)
            if item.get("channel") == "LIDAR_TOP":
                kf_lidar.append(item["token"])

    for tok in kf_lidar:
        p = lidar_map.get(tok, {}).get("prev", "")
        cnt = 0
        while p and cnt < 4:
            entry = lidar_map.get(p)
            if not entry:
                break
            if entry["ego_pose_token"]:
                ego_needed.add(entry["ego_pose_token"])
            p = entry["prev"]
            cnt += 1
    del lidar_map, kf_lidar
    print(f"  ego tokens needed: {len(ego_needed)}")

    ep_path = os.path.join(tmp_dir, "ego_pose.jsonl")
    open(ep_path, "w").close()
    written = 0
    print("[Ph1] ego_pose.json (filtered)...")
    with open(os.path.join(jd, "ego_pose.json"), "rb") as fin:
        for item in ijson.items(fin, "item"):
            if item["token"] in ego_needed:
                with open(ep_path, "a") as f:
                    f.write(json.dumps({
                        "token": item["token"],
                        "rotation": [float(x) for x in item["rotation"]],
                        "translation": [float(x) for x in item["translation"]]}) + "\n")
                written += 1
    print(f"  {written} ego_poses kept ({time.time()-t0:.0f}s)")
    del ego_needed
    gc.collect()
    return kf_path, ep_path


def load_jsonl(path):
    tbl = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                item = json.loads(line)
                tbl[item["token"]] = item
    return tbl


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", default="./data/nuscenes")
    parser.add_argument("--out-dir", default="./data/infos")
    parser.add_argument("--version", default="v1.0-trainval")
    parser.add_argument("--max-sweeps", type=int, default=4)
    parser.add_argument("--tmp-dir", default="/tmp/nuscenes_info_gen")
    args = parser.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    jd = os.path.join(args.data_root, args.version)
    t_all = time.time()

    # ===== Phase 1 =====
    kf_path, ep_path = phase1(args.data_root, args.version, args.tmp_dir)
    print(f"Phase1: {time.time()-t_all:.0f}s")

    # ===== Load tables =====
    print("[Ph2] Loading tables...")
    with open(os.path.join(jd, "scene.json")) as f:
        scene_tbl = {x["token"]: x for x in json.load(f)}
    with open(os.path.join(jd, "sample.json")) as f:
        sample_tbl = {x["token"]: x for x in json.load(f)}
    with open(os.path.join(jd, "sensor.json")) as f:
        sensor_tbl = {x["token"]: x for x in json.load(f)}
    with open(os.path.join(jd, "calibrated_sensor.json")) as f:
        cal_tbl = {x["token"]: x for x in json.load(f)}
    kfs = load_jsonl(kf_path)
    ego_tbl = load_jsonl(ep_path)
    print(f"  {len(kfs)}kfs {len(ego_tbl)}ego_poses ({time.time()-t_all:.0f}s)")

    # Build sensor mapping
    print("[Ph2] Building sample->sensor map...")
    sample_sd_map = defaultdict(dict)
    sensor_chan = {s["token"]: s["channel"] for s in sensor_tbl.values()}
    for sd in kfs.values():
        cs = cal_tbl.get(sd.get("calibrated_sensor_token", ""))
        if cs is None or cs.get("sensor_token") is None:
            continue
        chan = sensor_chan.get(cs["sensor_token"])
        if chan:
            sample_sd_map[sd["sample_token"]][chan] = sd

    # Split tokens
    scene_keys = sorted(scene_tbl.keys())
    val_scenes = {scene_tbl[k]["token"] for k in scene_keys[700:]}
    del scene_tbl, sensor_tbl, sensor_chan, scene_keys

    val_tokens = [s["token"] for s in sample_tbl.values() if s["scene_token"] in val_scenes]
    train_tokens = [s["token"] for s in sample_tbl.values() if s["scene_token"] not in val_scenes]
    print(f"  val={len(val_tokens)} train={len(train_tokens)}")

    # ===== Build one info dict =====
    def build_one(stok):
        sd_map = sample_sd_map.get(stok, {})
        lidar_sd = sd_map.get("LIDAR_TOP")
        if lidar_sd is None:
            return None

        lcs = cal_tbl.get(lidar_sd.get("calibrated_sensor_token", ""))
        lego = ego_tbl.get(lidar_sd.get("ego_pose_token", ""))
        if lcs is None or lego is None:
            return None

        l2e_t = np.array(lcs["translation"], dtype=np.float32)
        l2e_r = q2mat(np.array(lcs["rotation"], dtype=np.float32))
        e2g_t = np.array(lego["translation"], dtype=np.float32)
        e2g_r = q2mat(np.array(lego["rotation"], dtype=np.float32))

        ego_st = np.zeros(13, dtype=np.float32)
        ego_st[:3] = e2g_t
        ego_st[3:7] = np.array(lego["rotation"], dtype=np.float32)

        sweeps = []
        prev = lidar_sd.get("prev", "")
        cnt = 0
        while prev and cnt < args.max_sweeps:
            psd = kfs.get(prev)
            if psd is None:
                break
            pego = ego_tbl.get(psd.get("ego_pose_token", ""))
            pcs = cal_tbl.get(psd.get("calibrated_sensor_token", ""))
            if pego is None or pcs is None:
                break
            sweeps.append({"data_path": psd["filename"], "timestamp": psd["timestamp"],
                           "sensor2lidar_rotation": q2mat(np.array(pcs["rotation"], dtype=np.float32)),
                           "sensor2lidar_translation": np.array(pcs["translation"], dtype=np.float32),
                           "ego2global_rotation": q2mat(np.array(pego["rotation"], dtype=np.float32)),
                           "ego2global_translation": np.array(pego["translation"], dtype=np.float32)})
            prev = psd.get("prev", "")
            cnt += 1

        cams = {}
        for cam in CAM_ORDER:
            csd = sd_map.get(cam)
            if csd is None:
                continue
            ccs = cal_tbl.get(csd.get("calibrated_sensor_token", ""))
            cego = ego_tbl.get(csd.get("ego_pose_token", ""))
            if ccs is None or cego is None:
                continue
            cams[cam] = {"data_path": csd["filename"],
                         "sensor2lidar_rotation": q2mat(np.array(ccs["rotation"], dtype=np.float32)),
                         "sensor2lidar_translation": np.array(ccs["translation"], dtype=np.float32),
                         "cam2ego_rotation": np.array(cego["rotation"], dtype=np.float32),
                         "cam2ego_translation": np.array(cego["translation"], dtype=np.float32)}

        return {"token": stok, "timestamp": lidar_sd["timestamp"],
                "lidar_path": lidar_sd["filename"], "map_location": [0.0, 0.0],
                "sweeps": sweeps,
                "lidar2ego_translation": l2e_t, "lidar2ego_rotation": l2e_r,
                "ego2global_translation": e2g_t, "ego2global_rotation": e2g_r,
                "ego_status": ego_st,
                "map_annos": {"ped_crossing": [], "divider": [], "boundary": []},
                "cams": cams}

    # ===== Phase 2a: Val (small) =====
    print(f"\n[Ph2a] Val: {len(val_tokens)} tokens...")
    val_infos = []
    for i, tok in enumerate(val_tokens):
        info = build_one(tok)
        if info:
            val_infos.append(info)
        if i % 1000 == 0 and i > 0:
            print(f"  val {i}/{len(val_tokens)} ({len(val_infos)} infos)")
    vpath = os.path.join(args.out_dir, "nuscenes_infos_val.pkl")
    print(f"  Saving {len(val_infos)} val infos...")
    with open(vpath, "wb") as f:
        pickle.dump({"infos": val_infos, "metadata": {"version": args.version}}, f, protocol=pickle.HIGHEST_PROTOCOL)
    del val_infos, val_tokens
    gc.collect()
    print(f"  Val done ({time.time()-t_all:.0f}s)")

    # ===== Phase 2b: Train (larger) =====
    print(f"\n[Ph2b] Train: {len(train_tokens)} tokens...")
    train_infos = []
    for i, tok in enumerate(train_tokens):
        info = build_one(tok)
        if info:
            train_infos.append(info)
        if i % 5000 == 0 and i > 0:
            print(f"  train {i}/{len(train_tokens)} ({len(train_infos)} infos)")
    tpath = os.path.join(args.out_dir, "nuscenes_infos_train.pkl")
    print(f"  Saving {len(train_infos)} train infos...")
    with open(tpath, "wb") as f:
        pickle.dump({"infos": train_infos, "metadata": {"version": args.version}}, f, protocol=pickle.HIGHEST_PROTOCOL)
    del train_infos, train_tokens
    print(f"  Train done ({time.time()-t_all:.0f}s)")

    print(f"\nDone! Total: {time.time()-t_all:.0f}s")
    print(f"  Train: {os.path.getsize(tpath)/1024**2:.0f}MB")
    print(f"  Val:   {os.path.getsize(vpath)/1024**2:.0f}MB")


if __name__ == "__main__":
    main()
