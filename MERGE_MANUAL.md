# 手动合并大文件说明（Manual Merge）

仓库里超过 GitHub 100MB 单文件上限的大 pkl 被切成了 `<90MB` 的分块，存放在同路径下的 `<文件名>.pkl.parts/` 目录中：

```
nuscenes_infos_train.pkl.parts/
├── chunk_000            # 分块，按序号排序（000, 001, 002 ...）
├── chunk_001
├── ...
├── chunk_007
├── original_filename.txt  # 记录原始文件相对路径
└── checksum.md5           # 原始文件的 MD5，用于合并后校验
```

涉及以下 4 个大文件（MomAD-main 与 SparseDrive-main 各一套）：

| 原始文件 | 大小 | 分块数 |
|---|---|---|
| MomAD-main/open_loop/data/infos/nuscenes_infos_train.pkl | 662M | 8 |
| MomAD-main/open_loop/data/infos/nuscenes_infos_val.pkl | 136M | 2 |
| SparseDrive-main/data/infos/nuscenes_infos_train.pkl | 662M | 8 |
| SparseDrive-main/data/infos/nuscenes_infos_val.pkl | 136M | 2 |

## 方式一：手动合并（不依赖任何脚本）

### Linux / macOS

以 `MomAD-main/open_loop/data/infos/nuscenes_infos_train.pkl` 为例：

```bash
cd MomAD-main/open_loop/data/infos

# 1. 按序号顺序拼接所有分块
cat nuscenes_infos_train.pkl.parts/chunk_000 \
    nuscenes_infos_train.pkl.parts/chunk_001 \
    nuscenes_infos_train.pkl.parts/chunk_002 \
    nuscenes_infos_train.pkl.parts/chunk_003 \
    nuscenes_infos_train.pkl.parts/chunk_004 \
    nuscenes_infos_train.pkl.parts/chunk_005 \
    nuscenes_infos_train.pkl.parts/chunk_006 \
    nuscenes_infos_train.pkl.parts/chunk_007 \
    > nuscenes_infos_train.pkl

# 也可以偷懒（chunk_* 按字典序就是正确顺序）：
# cat nuscenes_infos_train.pkl.parts/chunk_* > nuscenes_infos_train.pkl

# 2. 校验 MD5 是否与原文件一致
md5sum nuscenes_infos_train.pkl
cat nuscenes_infos_train.pkl.parts/checksum.md5
# 两个值相同即合并成功
```

其余 3 个文件同理，把目录名和文件名换掉即可。

### Windows（cmd / PowerShell）

cmd 下用 `copy /b` 二进制拼接（注意 `+` 连接、按序号顺序）：

```cmd
cd MomAD-main\open_loop\data\infos
copy /b nuscenes_infos_train.pkl.parts\chunk_000+^
        nuscenes_infos_train.pkl.parts\chunk_001+^
        nuscenes_infos_train.pkl.parts\chunk_002+^
        nuscenes_infos_train.pkl.parts\chunk_003+^
        nuscenes_infos_train.pkl.parts\chunk_004+^
        nuscenes_infos_train.pkl.parts\chunk_005+^
        nuscenes_infos_train.pkl.parts\chunk_006+^
        nuscenes_infos_train.pkl.parts\chunk_007 ^
        nuscenes_infos_train.pkl
```

校验 MD5（PowerShell）：

```powershell
Get-FileHash nuscenes_infos_train.pkl -Algorithm MD5
# 与 nuscenes_infos_train.pkl.parts\checksum.md5 里的值对比
```

## 方式二：脚本自动合并（推荐）

仓库根目录提供了 `merge_pkl.sh`，在仓库根目录执行：

```bash
bash merge_pkl.sh
```

它会自动找到所有 `*.pkl.parts/` 目录，按序合并到 `original_filename.txt` 记录的原始路径，并逐个校验 MD5。

## 注意事项

- 分块是按字节顺序切割的（`split -b 90m`），**必须按 chunk_000 → chunk_007 的顺序拼接**，乱序会得到损坏的文件（MD5 校验能发现）。
- 合并后如确认无误，`.pkl.parts/` 目录可以删除以节省空间。
- `.pth` 权重文件（resnet50-19c8e357.pth，约 98MB）没有拆分，直接在原路径，无需合并。
