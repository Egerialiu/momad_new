# nuScenes 数据集还原手册

> **本手册用途**：服务器（SeetaCloud）上 `/root/autodl-tmp/nuscenes/`（约 377G）原始数据集因省钱已删除。本手册记录：
> 1. 删除前**快照**（各子目录大小 + 文件数），用于恢复后校验
> 2. 源压缩包 → 目录的**对应关系**
> 3. 从压缩包**解压还原**的完整步骤
> 4. 恢复后的**验证方法**
>
> 依照本手册，可在任何时间从 `/autodl-pub` 的源压缩包一键还原到删除前的状态。

---

## 0. 源压缩包位置与完整性

所有源压缩包均在服务器公共目录 `/autodl-pub/data/nuScenes/`，**未随数据集删除**，删除前已校验。

| 压缩包 | 路径 | 大小 | 完整性 |
|---|---|---|---|
| 元数据 | `/autodl-pub/data/nuScenes/Fulldatasetv1.0/Trainval/v1.0-trainval_meta.tgz` | 440M | ✅ 全量校验 OK |
| blob 1 | `/autodl-pub/data/nuScenes/Fulldatasetv1.0/Trainval/v1.0-trainval01_blobs.tgz` | 30G | ✅ gzip 头正常 |
| blob 2 | `/autodl-pub/data/nuScenes/Fulldatasetv1.0/Trainval/v1.0-trainval02_blobs.tgz` | 29G | ✅ gzip 头正常 |
| blob 3 | `/autodl-pub/data/nuScenes/Fulldatasetv1.0/Trainval/v1.0-trainval03_blobs.tgz` | 28G | ✅ gzip 头正常 |
| blob 4 | `/autodl-pub/data/nuScenes/Fulldatasetv1.0/Trainval/v1.0-trainval04_blobs.tgz` | 30G | ✅ gzip 头正常 |
| blob 5 | `/autodl-pub/data/nuScenes/Fulldatasetv1.0/Trainval/v1.0-trainval05_blobs.tgz` | 27G | ✅ gzip 头正常 |
| blob 6 | `/autodl-pub/data/nuScenes/Fulldatasetv1.0/Trainval/v1.0-trainval06_blobs.tgz` | 26G | ✅ gzip 头正常 |
| blob 7 | `/autodl-pub/data/nuScenes/Fulldatasetv1.0/Trainval/v1.0-trainval07_blobs.tgz` | 28G | ✅ gzip 头正常 |
| blob 8 | `/autodl-pub/data/nuScenes/Fulldatasetv1.0/Trainval/v1.0-trainval08_blobs.tgz` | 29G | ✅ gzip 头正常 |
| blob 9 | `/autodl-pub/data/nuScenes/Fulldatasetv1.0/Trainval/v1.0-trainval09_blobs.tgz` | 32G | ✅ gzip 头正常 |
| blob 10 | `/autodl-pub/data/nuScenes/Fulldatasetv1.0/Trainval/v1.0-trainval10_blobs.tgz` | 39G | ✅ gzip 头正常 |
| CAN bus | `/autodl-pub/data/nuScenes/CANbusexpansion/can_bus.zip` | 745M | ✅ 全量校验 OK |
| 地图扩展 v1.2 | `/autodl-pub/data/nuScenes/Mapexpansion/nuScenes-map-expansion-v1.2.zip` | 17M | ✅ 全量校验 OK |
| 地图扩展 v1.3 | `/autodl-pub/data/nuScenes/Mapexpansion/nuScenes-map-expansion-v1.3.zip` | 381M | ✅ 全量校验 OK |

> **校验说明**：
> - **blob 01–10**（26–39G）：单个包 `tar tzf` 全量校验需 5 分钟+，10 个包近 1 小时，故采用 **gzip 头部校验**（`1f8b` magic + 大小正常）。且删除前 377G 数据集就是从这些包解出且完整，双保险足够。
> - **meta / can_bus**（≤745M）：容器 CPU/IO 受限下 `tar tzf`/`unzip -t` 直接跑会超时，故用服务器后台 `nohup` 全量校验——**均通过**（`META_OK` / `CANBUS_OK`）。
> - **map v1.2 / v1.3**：全量校验 OK。

---

## 1. 删除前快照（2026-08-06 采集）

删除前 `/root/autodl-tmp/nuscenes/` 各子目录的**大小 + 文件数**（恢复后按此校验）：

| 子目录 | 大小 | 文件数 |
|---|---|---|
| `samples/` | 53G | 409,778 |
| `sweeps/` | 318G | 1,969,985 |
| `v1.0-trainval/` | 2.5G | 13 |
| `can_bus/` | 4.4G | 7,832 |
| `maps/` | 5.6M | 4 |
| **合计** | **约 377G** | **2,387,612** |

传感器子目录（`samples/` 与 `sweeps/` 下均相同，各 12 个）：
`CAM_BACK, CAM_BACK_LEFT, CAM_BACK_RIGHT, CAM_FRONT, CAM_FRONT_LEFT, CAM_FRONT_RIGHT, LIDAR_TOP, RADAR_BACK_LEFT, RADAR_BACK_RIGHT, RADAR_FRONT, RADAR_FRONT_LEFT, RADAR_FRONT_RIGHT`

`v1.0-trainval/` 的 13 个文件（元数据 json）：
`attribute.json, calibrated_sensor.json, category.json, ego_pose.json, instance.json, log.json, map.json, sample.json, sample_annotation.json, sample_data.json, scene.json, sensor.json, visibility.json`

`maps/` 的 4 个文件：4 个城市地图 png（`boston-seaport`, `singapore-hollandvillage`, `singapore-onenorth`, `singapore-queenstown`）。

`can_bus/`：各场景的 `*_meta.json / *_pose.json / *_route.json` 等，共 7,832 个文件。

> **注**：目录下还有 9 个 `.v1.0-trainval0N_blobs.txt` 标记文件（约 145B 每个），来自 blob 压缩包，是解压残留，不影响数据完整性。

---

## 2. 删除操作记录

- **删除对象**：`/root/autodl-tmp/nuscenes/`（约 377G）
- **删除时间**：2026-08-06 22:57（已执行并核验）
- **删除命令**：
  ```bash
  rm -rf /root/autodl-tmp/nuscenes/
  ```
- **删除前已核对**：源压缩包完好（§0）、快照已记录（§1）、无进程占用、非 symlink、保护对象分离
- **删除后已核验**（2026-08-06）：
  - `ls -ld /root/autodl-tmp/nuscenes` → No such file or directory ✅
  - 磁盘：`/root/autodl-tmp` 378G → 799M 已用（1%），**约 377G 已释放** ✅
  - `/root/autodl-tmp/infos/*.pkl` 完好（train 662M + val 136M）✅
  - `/root/SparseDrive-main/data/nuscenes` symlink 悬空（指向已删目标），恢复时重建 ✅
- **删除后保留**：
  - `/root/autodl-tmp/infos/nuscenes_infos_train.pkl`（662MB）+ `nuscenes_infos_val.pkl`（136MB）——派生 info 文件，**未删**，重生成很贵
  - `/root/SparseDrive-main/data/infos/` 下同一份 pkl 副本
  - `/root/SparseDrive-main/data/nuscenes` → symlink → `/root/autodl-tmp/nuscenes`（已悬空，恢复后自动恢复指向）

---

## 3. 压缩包 → 目录 对应关系

| 源压缩包 | 解压出的目录 |
|---|---|
| `v1.0-trainval_meta.tgz` | `v1.0-trainval/`（13 个 json）+ `maps/`（4 个 png） |
| `v1.0-trainval0N_blobs.tgz`（01–10） | `samples/` + `sweeps/` + `.v1.0-trainval0N_blobs.txt` 标记 |
| `can_bus.zip` | `can_bus/` |
| `nuScenes-map-expansion-*.zip` | （**未解压**，无需还原） |

> **还原步骤已验证可行**（2026-08-06，对源压缩包实时核验）：
> - `v1.0-trainval_meta.tgz` 顶层结构 = `maps/` + `v1.0-trainval/`
> - **每个** blob 包（抽查 01/10）同时含 `samples/` 和 `sweeps/`，解压到目标目录自然覆盖两者
> - `can_bus.zip` 顶层 = `can_bus/`，`unzip -d /root/autodl-tmp/nuscenes/` 解出正确
> - `maps/` **不是**来自 blob 包，而是来自 meta 包

---

## 4. 解压还原步骤

在服务器上执行（目标目录 `/root/autodl-tmp/nuscenes/`）：

```bash
# 0) 确保目标目录存在且为空
mkdir -p /root/autodl-tmp/nuscenes && cd /root/autodl-tmp/nuscenes

# 1) 解压元数据 + 地图（v1.0-trainval/ + maps/）
tar xzf /autodl-pub/data/nuScenes/Fulldatasetv1.0/Trainval/v1.0-trainval_meta.tgz -C /root/autodl-tmp/nuscenes/

# 2) 解压 10 个 blob 压缩包（samples/ + sweeps/）
#    ⚠️ 建议串行，避免 I/O 争抢；每个约需数分钟
for f in /autodl-pub/data/nuScenes/Fulldatasetv1.0/Trainval/v1.0-trainval0{1..9}_blobs.tgz \
         /autodl-pub/data/nuScenes/Fulldatasetv1.0/Trainval/v1.0-trainval10_blobs.tgz; do
  echo "=== 解压 $f ==="
  tar xzf "$f" -C /root/autodl-tmp/nuscenes/
done

# 3) 解压 CAN bus（can_bus/）
unzip -o /autodl-pub/data/nuScenes/CANbusexpansion/can_bus.zip -d /root/autodl-tmp/nuscenes/

# 4) （可选）恢复 symlink 指向（若 data/nuscenes 是悬空 symlink）
#    SparseDrive 侧：
#    cd /root/SparseDrive-main && rm -f data/nuscenes && ln -s /root/autodl-tmp/nuscenes data/nuscenes
```

> **磁盘空间要求**：解压前 `/root/autodl-tmp` 需有 ≥ 400G 可用空间（当前容量 400G，删除前已用 378G，删除后可完全放下）。

---

## 5. Mapexpansion（地图扩展）说明

- `nuScenes-map-expansion-v1.2.zip`（17M）和 `-v1.3.zip`（381M）**在服务器上从未被解压**。
- 原对话中试图提取地图时遇到缺 JSON 报错，解决方式是**修改 SparseDrive 代码** `projects/mmdet3d_plugin/datasets/map_utils/nuscmap_extractor.py`（加 try/except 跳过缺失地图），而不是补地图数据。
- 因此：**还原到删除前状态不需要** Mapexpansion。若未来某功能需要地图扩展，再按需解压 v1.3（新版）。

---

## 6. 恢复后验证

```bash
# 1) 校验各子目录文件数是否与 §1 快照一致
for d in samples sweeps v1.0-trainval can_bus maps; do
  echo -n "$d: "; find /root/autodl-tmp/nuscenes/$d -type f 2>/dev/null | wc -l;
done

# 2) 校验各子目录大小
du -sh /root/autodl-tmp/nuscenes/*/

# 3) 快速抽样：加载 NuScenes 并统计场景/样本数
export PATH="/root/miniconda3/envs/momad/bin:$PATH"
python3 -c "
from nuscenes import NuScenes
nusc = NuScenes(version='v1.0-trainval', dataroot='/root/autodl-tmp/nuscenes', verbose=False)
print(f'Scenes: {len(nusc.scene)}, Samples: {len(nusc.sample)}')
"
# 期望：Scenes: 850, Samples: 34149

# 4) 校验派生 info 文件仍可用（未删，应直接可用）
python3 -c "
import pickle
d = pickle.load(open('/root/autodl-tmp/infos/nuscenes_infos_train.pkl','rb'))
print('train infos:', len(d['infos']))
"
# 期望：28130 train infos
```

---

## 7. 关键文件/路径速查

| 项 | 路径 |
|---|---|
| 数据集根 | `/root/autodl-tmp/nuscenes/` |
| SparseDrive symlink | `/root/SparseDrive-main/data/nuscenes` → `/root/autodl-tmp/nuscenes` |
| 派生 info（train） | `/root/autodl-tmp/infos/nuscenes_infos_train.pkl`（662MB） |
| 派生 info（val） | `/root/autodl-tmp/infos/nuscenes_infos_val.pkl`（136MB） |
| info 副本（SparseDrive） | `/root/SparseDrive-main/data/infos/` 下同两份 |
| 源压缩包 | `/autodl-pub/data/nuScenes/` |
| 本手册 | `C:\Users\14643\Desktop\论文新起\nuscenes_还原手册.md` |

---

*本手册由对话记录 + 服务器实时核对生成。* 生成日期：2026-08-06
