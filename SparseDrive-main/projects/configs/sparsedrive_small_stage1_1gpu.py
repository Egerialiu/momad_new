__base__ = "./sparsedrive_small_stage1.py"

num_gpus = 1
batch_size = 4
num_iters_per_epoch = int(28130 // (num_gpus * batch_size))
num_epochs = 100
checkpoint_epoch_interval = 20

data = dict(
    samples_per_gpu=batch_size,
    workers_per_gpu=2,
)

# Gradient accumulation: 4 * 16 = 64 effective batch (matches original)
optimizer_config = dict(
    grad_clip=dict(max_norm=25, norm_type=2),
    type="GradientCumulativeOptimizerHook",
    cumulative_iters=16,
)

# Scale max_iters to account for grad accum (LR scheduler steps per iter)
# Original: 439 iters/epoch * 100 epochs = 43900 optimizer steps
# Ours: 7032 iters/epoch * 100 epochs = 703200 forward passes / 16 = 43950 optimizer steps
runner = dict(
    type="IterBasedRunner",
    max_iters=num_iters_per_epoch * num_epochs,
)

evaluation = dict(
    interval=num_iters_per_epoch * checkpoint_epoch_interval,
)
