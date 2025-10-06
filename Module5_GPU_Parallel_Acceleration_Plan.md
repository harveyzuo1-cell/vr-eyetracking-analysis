# 模块5 RQA流程 GPU并行加速开发方案

## 📋 文档信息
- **项目名称**: VR眼动数据分析系统 - 模块5 RQA批处理GPU加速
- **创建时间**: 2025-10-01
- **目标**: 将10,200组合的批处理时间从142小时降至5-7小时 (20-30x提速)
- **硬件环境**: NVIDIA GeForce RTX 3080 Mobile (16GB VRAM, CUDA 12.6)

---

## 🎯 项目目标

### 当前问题
- **任务规模**: 10,200个参数组合 (m×τ×ε×l_min)
- **当前性能**: 50秒/组合
- **预计耗时**: 142小时 (约6天)
- **瓶颈分析**:
  1. CPU单线程执行RQA计算 (NumPy)
  2. 顺序处理10,200个组合
  3. 同步阻塞API设计

### 优化目标
| 指标 | 当前 | 目标 | 提升 |
|------|------|------|------|
| 单组合耗时 | 50秒 | 2.5秒 | 20x |
| 并行任务数 | 1 | 4-6 | 4-6x |
| 总处理时间 | 142小时 | 5-7小时 | **20-30x** |
| GPU利用率 | 0% | 80-90% | - |
| 实时进度 | 无 | WebSocket流式 | ✅ |

---

## 🏗️ 技术架构

### 系统架构图
```
┌─────────────────────────────────────────────────────────────┐
│                      前端 (Browser)                          │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ 配置面板    │  │ 进度监控      │  │ GPU状态监控      │   │
│  └──────┬──────┘  └──────┬───────┘  └────────┬─────────┘   │
│         │                 │                    │              │
│         └─────────────────┼────────────────────┘              │
└───────────────────────────┼───────────────────────────────────┘
                            │
                      WebSocket (实时进度)
                            │
┌───────────────────────────┼───────────────────────────────────┐
│                    Flask Backend                              │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  /api/rqa-pipeline/batch-execute-gpu (REST API)        │ │
│  │  • 参数验证                                             │ │
│  │  • 任务分配                                             │ │
│  │  • 进度广播 (WebSocket)                                 │ │
│  └────────────────────┬────────────────────────────────────┘ │
│                       │                                        │
│  ┌────────────────────▼────────────────────────────────────┐ │
│  │     多进程调度引擎 (ProcessPoolExecutor)                │ │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │ │
│  │  │ Worker 1 │ │ Worker 2 │ │ Worker 3 │ │ Worker 4 │  │ │
│  │  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘  │ │
│  └───────┼────────────┼────────────┼────────────┼─────────┘ │
└──────────┼────────────┼────────────┼────────────┼───────────┘
           │            │            │            │
           └────────────┴────────────┴────────────┘
                         GPU共享
                            │
┌───────────────────────────▼───────────────────────────────────┐
│              NVIDIA RTX 3080 Mobile (16GB)                    │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  CUDA 12.6 Runtime                                      │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐             │ │
│  │  │ CuPy RQA │  │ PyTorch  │  │ GPU-Scipy│             │ │
│  │  │ Kernel   │  │ Tensors  │  │ Stats    │             │ │
│  │  └──────────┘  └──────────┘  └──────────┘             │ │
│  └─────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────┘
```

### 关键技术栈
| 层级 | 技术 | 版本要求 | 用途 |
|------|------|---------|------|
| GPU加速 | **CuPy** | ≥13.0.0 | NumPy GPU替代 (RQA计算) |
| 深度学习 | **PyTorch** | ≥2.0.0+cu118 | GPU张量运算 |
| 并行计算 | **concurrent.futures** | 内置 | 多进程任务池 |
| 实时通信 | **Flask-SocketIO** | ≥5.3.0 | WebSocket进度推送 |
| 任务队列 | **Redis** (可选) | ≥7.0 | 分布式任务管理 |

---

## 📊 详细开发计划

### Phase 1: 环境准备与依赖安装 (预计45分钟)

#### 1.1 检查CUDA环境
```bash
# 验证CUDA版本
nvidia-smi  # 确认CUDA 12.6

# 检查现有PyTorch版本
python -c "import torch; print(torch.__version__)"  # 当前: 2.7.0+cpu
```

#### 1.2 卸载CPU版PyTorch
```bash
pip uninstall torch torchvision torchaudio -y
```

#### 1.3 安装PyTorch GPU版 (CUDA 12.1兼容)
```bash
# CUDA 12.6向后兼容CUDA 12.1
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

#### 1.4 安装CuPy (CUDA 12.x)
```bash
# 从预编译轮子安装 (推荐)
pip install cupy-cuda12x

# 验证安装
python -c "import cupy as cp; print('CuPy版本:', cp.__version__); print('CUDA版本:', cp.cuda.runtime.runtimeGetVersion())"
```

#### 1.5 安装WebSocket支持
```bash
pip install flask-socketio python-socketio eventlet
```

#### 1.6 验证GPU可用性
```python
# test_gpu_ready.py
import torch
import cupy as cp

print("=== GPU环境验证 ===")
print(f"PyTorch版本: {torch.__version__}")
print(f"CUDA可用: {torch.cuda.is_available()}")
print(f"GPU名称: {torch.cuda.get_device_name(0)}")
print(f"显存总量: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")

print(f"\nCuPy版本: {cp.__version__}")
x = cp.array([1, 2, 3])
print(f"CuPy测试: {x.sum()}")  # 应输出: 6
```

---

### Phase 2: GPU加速RQA核心 (预计90分钟)

#### 2.1 创建GPU RQA模块
**文件**: `analysis/rqa_analyzer_gpu.py`

**核心优化策略**:
1. **距离矩阵计算** (最耗时 ~60%):
```python
import cupy as cp

def compute_distance_matrix_gpu(traj, m, tau):
    """
    GPU加速的距离矩阵计算

    优化点:
    - NumPy → CuPy (20x提速)
    - 使用GPU并行计算欧氏距离
    """
    n_points = len(traj) - (m - 1) * tau

    # 构建嵌入空间 (在GPU上)
    embedding = cp.zeros((n_points, m), dtype=cp.float32)
    for i in range(m):
        embedding[:, i] = cp.array(traj[i * tau : i * tau + n_points])

    # GPU并行计算距离矩阵 (使用CuPy的优化kernel)
    # 替代原来的CPU嵌套循环
    dist_matrix = cp.linalg.norm(
        embedding[:, None, :] - embedding[None, :, :],
        axis=2
    )

    return cp.asnumpy(dist_matrix)  # 只在需要时传回CPU
```

2. **递归矩阵生成**:
```python
def compute_recurrence_matrix_gpu(dist_matrix, eps):
    """GPU加速的递归矩阵生成"""
    dist_gpu = cp.array(dist_matrix)
    rec_matrix_gpu = (dist_gpu < eps).astype(cp.int8)
    return cp.asnumpy(rec_matrix_gpu)
```

3. **RQA指标计算** (混合CPU/GPU):
```python
def compute_rqa_metrics_gpu(rec_matrix):
    """
    混合计算策略:
    - 简单指标(RR): GPU
    - 复杂指标(DET, ENT): CPU (避免GPU-CPU频繁传输)
    """
    rec_gpu = cp.array(rec_matrix)

    # GPU计算RR
    rr = cp.sum(rec_gpu) / cp.prod(rec_gpu.shape)

    # 传回CPU计算DET/ENT (避免复杂kernel编写)
    rec_cpu = cp.asnumpy(rec_gpu)
    det, lmax, entr = compute_det_cpu(rec_cpu)  # 复用原CPU代码

    return {
        'RR': float(rr),
        'DET': det,
        'L_max': lmax,
        'ENT': entr
    }
```

#### 2.2 内存管理策略
```python
class GPUMemoryManager:
    """GPU显存管理器"""

    def __init__(self, max_gpu_usage=0.8):
        self.max_usage = max_gpu_usage
        self.total_mem = cp.cuda.Device(0).mem_info[1]

    def can_allocate(self, size_bytes):
        """检查是否可分配指定大小"""
        free_mem = cp.cuda.Device(0).mem_info[0]
        return free_mem > size_bytes + self.total_mem * (1 - self.max_usage)

    def clear_cache(self):
        """清理GPU缓存"""
        cp.get_default_memory_pool().free_all_blocks()
```

#### 2.3 性能对比测试
```python
# benchmark_gpu.py
import time
import numpy as np
from analysis.rqa_analyzer import compute_rqa_1d  # 原CPU版本
from analysis.rqa_analyzer_gpu import compute_rqa_1d_gpu  # GPU版本

# 模拟真实数据
traj_x = np.random.randn(5000)

params = {'m': 5, 'tau': 3, 'eps': 0.08, 'lmin': 2}

# CPU版本
start = time.time()
result_cpu = compute_rqa_1d(traj_x, traj_x, params)
time_cpu = time.time() - start

# GPU版本
start = time.time()
result_gpu = compute_rqa_1d_gpu(traj_x, traj_x, params)
time_gpu = time.time() - start

print(f"CPU耗时: {time_cpu:.2f}秒")
print(f"GPU耗时: {time_gpu:.2f}秒")
print(f"加速比: {time_cpu/time_gpu:.1f}x")
```

**预期结果**: 15-25x加速 (取决于数据量)

---

### Phase 3: 多进程并行引擎 (预计60分钟)

#### 3.1 并行调度器设计
**文件**: `visualization/parallel_executor.py`

```python
import os
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, as_completed
import cupy as cp

class GPUParallelExecutor:
    """GPU多进程并行执行器"""

    def __init__(self, n_workers=4, gpu_id=0):
        """
        Args:
            n_workers: 并行worker数量 (建议4-6)
            gpu_id: 使用的GPU编号
        """
        self.n_workers = n_workers
        self.gpu_id = gpu_id

        # 计算每个worker的显存配额
        total_mem = cp.cuda.Device(gpu_id).mem_info[1]
        self.mem_per_worker = (total_mem * 0.8) / n_workers  # 80%显存分配

    def execute_batch(self, param_combinations, callback=None):
        """
        并行执行批量任务

        Args:
            param_combinations: 参数组合列表
            callback: 进度回调函数 callback(index, result)
        """
        results = []

        with ProcessPoolExecutor(
            max_workers=self.n_workers,
            mp_context=mp.get_context('spawn')  # Windows必须用spawn
        ) as executor:
            # 提交所有任务
            future_to_params = {
                executor.submit(
                    self._worker_task,
                    params,
                    self.gpu_id
                ): (i, params)
                for i, params in enumerate(param_combinations)
            }

            # 收集结果
            for future in as_completed(future_to_params):
                idx, params = future_to_params[future]
                try:
                    result = future.result()
                    results.append((idx, params, result))

                    # 进度回调
                    if callback:
                        callback(idx, result)

                except Exception as e:
                    print(f"❌ 任务{idx}失败: {e}")
                    results.append((idx, params, {'error': str(e)}))

        return results

    @staticmethod
    def _worker_task(params, gpu_id):
        """
        Worker任务函数 (在子进程中执行)

        注意: 必须在子进程中重新初始化CuPy上下文
        """
        import cupy as cp
        from analysis.rqa_analyzer_gpu import compute_rqa_1d_gpu

        # 设置GPU设备
        cp.cuda.Device(gpu_id).use()

        # 执行RQA流程 (调用GPU版本)
        try:
            from visualization.rqa_pipeline_api import execute_full_pipeline_internal_gpu
            result = execute_full_pipeline_internal_gpu(params)
            return result
        finally:
            # 清理GPU缓存
            cp.get_default_memory_pool().free_all_blocks()
```

#### 3.2 Worker数量优化策略
```python
def calculate_optimal_workers(gpu_mem_gb=16, single_task_mem_gb=2.5):
    """
    计算最优worker数量

    Args:
        gpu_mem_gb: GPU显存容量
        single_task_mem_gb: 单任务平均显存占用

    Returns:
        最优worker数量
    """
    # 保留20%显存buffer
    usable_mem = gpu_mem_gb * 0.8

    # 理论最大worker数
    max_workers = int(usable_mem / single_task_mem_gb)

    # CPU核心数限制
    cpu_cores = os.cpu_count()

    # 取较小值
    optimal = min(max_workers, cpu_cores // 2, 6)  # 最多6个

    return max(optimal, 1)
```

---

### Phase 4: WebSocket实时进度 (预计45分钟)

#### 4.1 后端WebSocket服务
**文件**: `visualization/socketio_server.py`

```python
from flask_socketio import SocketIO, emit
from flask import Flask

# 初始化SocketIO
socketio = SocketIO(cors_allowed_origins="*")

class ProgressBroadcaster:
    """进度广播器"""

    def __init__(self, socketio_instance):
        self.sio = socketio_instance
        self.current_task = None

    def start_batch(self, total_count):
        """开始批处理"""
        self.sio.emit('batch_started', {
            'total': total_count,
            'timestamp': time.time()
        })

    def update_progress(self, current, total, params, result):
        """更新进度"""
        self.sio.emit('progress_update', {
            'current': current,
            'total': total,
            'progress': (current / total) * 100,
            'param_signature': generate_param_signature(params),
            'success': result.get('success', False),
            'skipped': result.get('skipped', False),
            'timestamp': time.time()
        })

    def batch_complete(self, stats):
        """批处理完成"""
        self.sio.emit('batch_completed', {
            'stats': stats,
            'timestamp': time.time()
        })

    def gpu_stats_update(self, gpu_util, mem_used, mem_total):
        """GPU状态更新 (每5秒)"""
        self.sio.emit('gpu_stats', {
            'utilization': gpu_util,
            'memory_used': mem_used,
            'memory_total': mem_total,
            'memory_percent': (mem_used / mem_total) * 100
        })
```

#### 4.2 GPU监控线程
```python
import threading
import pynvml

class GPUMonitor:
    """GPU状态监控"""

    def __init__(self, broadcaster, interval=5):
        self.broadcaster = broadcaster
        self.interval = interval
        self.running = False

        pynvml.nvmlInit()
        self.handle = pynvml.nvmlDeviceGetHandleByIndex(0)

    def start(self):
        """启动监控"""
        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop)
        self.thread.daemon = True
        self.thread.start()

    def _monitor_loop(self):
        while self.running:
            # 获取GPU状态
            util = pynvml.nvmlDeviceGetUtilizationRates(self.handle)
            mem_info = pynvml.nvmlDeviceGetMemoryInfo(self.handle)

            # 广播状态
            self.broadcaster.gpu_stats_update(
                gpu_util=util.gpu,
                mem_used=mem_info.used / 1e9,  # GB
                mem_total=mem_info.total / 1e9
            )

            time.sleep(self.interval)

    def stop(self):
        self.running = False
        pynvml.nvmlShutdown()
```

#### 4.3 前端WebSocket接收
**文件**: `visualization/templates/enhanced_index.html`

```javascript
// 初始化SocketIO连接
const socket = io('http://127.0.0.1:8080');

// 监听批处理开始
socket.on('batch_started', (data) => {
    console.log('📦 批处理已启动，总任务数:', data.total);
    document.getElementById('batchProgressPanel').style.display = 'block';
});

// 监听进度更新
socket.on('progress_update', (data) => {
    const progress = data.progress.toFixed(1);

    // 更新进度条
    const progressBar = document.getElementById('batchProgressBar');
    progressBar.style.width = progress + '%';
    progressBar.innerHTML = `<span class="fs-5 fw-bold">${progress}%</span>`;

    // 更新统计卡片
    document.getElementById('batch-current-count').textContent = data.current;

    // 实时日志
    addLogEntry(data.param_signature, data.success, data.skipped);
});

// 监听GPU状态
socket.on('gpu_stats', (data) => {
    document.getElementById('gpu-utilization').textContent = data.utilization + '%';
    document.getElementById('gpu-memory').textContent =
        `${data.memory_used.toFixed(1)} / ${data.memory_total.toFixed(1)} GB`;

    // 更新GPU进度条
    const gpuBar = document.getElementById('gpuUtilizationBar');
    gpuBar.style.width = data.utilization + '%';
    gpuBar.className = data.utilization > 80 ? 'bg-success' : 'bg-warning';
});

// 监听批处理完成
socket.on('batch_completed', (data) => {
    console.log('✅ 批处理完成！', data.stats);
    showCompletionModal(data.stats);
});
```

---

### Phase 5: API集成 (预计30分钟)

#### 5.1 新增GPU批处理API
**文件**: `visualization/rqa_pipeline_api.py`

```python
@rqa_pipeline_bp.route('/api/rqa-pipeline/batch-execute-gpu', methods=['POST'])
def batch_execute_gpu():
    """GPU并行批处理API"""
    data = request.json

    # 解析参数
    batch_config = data.get('batch_config', {})
    param_combinations = generate_param_grid(
        batch_config['m_range'],
        batch_config['tau_range'],
        batch_config['eps_range'],
        batch_config['lmin_range']
    )

    total_count = len(param_combinations)

    # 初始化进度广播器
    broadcaster = ProgressBroadcaster(socketio)
    broadcaster.start_batch(total_count)

    # 启动GPU监控
    gpu_monitor = GPUMonitor(broadcaster)
    gpu_monitor.start()

    # 计算最优worker数
    n_workers = calculate_optimal_workers()

    # 执行并行任务
    executor = GPUParallelExecutor(n_workers=n_workers)

    def progress_callback(idx, result):
        broadcaster.update_progress(
            idx + 1,
            total_count,
            param_combinations[idx],
            result
        )

    try:
        results = executor.execute_batch(
            param_combinations,
            callback=progress_callback
        )

        # 统计结果
        stats = {
            'total': total_count,
            'success': sum(1 for _, _, r in results if r.get('success')),
            'failed': sum(1 for _, _, r in results if not r.get('success')),
            'skipped': sum(1 for _, _, r in results if r.get('skipped'))
        }

        broadcaster.batch_complete(stats)

        return jsonify({'success': True, 'stats': stats})

    finally:
        gpu_monitor.stop()
```

#### 5.2 GPU版本pipeline函数
```python
def execute_full_pipeline_internal_gpu(params):
    """
    GPU加速的完整pipeline

    流程:
    1. RQA计算 (GPU加速)
    2. 数据合并 (CPU)
    3. 特征提取 (混合)
    4. 统计分析 (CPU)
    5. 可视化 (CPU)
    """
    from analysis.rqa_analyzer_gpu import compute_rqa_1d_gpu, compute_rqa_2d_gpu

    param_signature = generate_param_signature(params)

    # 断点续传检查
    param_dir = os.path.join(MODULE10_DATASET_ROOT, param_signature)
    metadata_file = os.path.join(param_dir, 'metadata.json')

    if os.path.exists(metadata_file):
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        if all(metadata.get(f'step_{i}_completed') for i in range(1, 6)):
            return {'success': True, 'skipped': True, 'param_signature': param_signature}

    try:
        # Step 1: RQA计算 (GPU加速) ⚡
        rqa_results = {}
        for group in ['control', 'mci', 'ad']:
            group_results = []
            for subject_data in load_group_data(group):
                # 使用GPU版本计算
                result_1d = compute_rqa_1d_gpu(subject_data['x'], subject_data['y'], params)
                result_2d = compute_rqa_2d_gpu(subject_data['x'], subject_data['y'], params)
                group_results.append({**result_1d, **result_2d})
            rqa_results[group] = group_results

        update_metadata(param_dir, 'step_1_completed', True)

        # Step 2-5: 使用原CPU版本
        merge_data(rqa_results, param_dir)
        update_metadata(param_dir, 'step_2_completed', True)

        enrich_features(param_dir)
        update_metadata(param_dir, 'step_3_completed', True)

        statistical_analysis(param_dir)
        update_metadata(param_dir, 'step_4_completed', True)

        generate_visualizations(param_dir)
        update_metadata(param_dir, 'step_5_completed', True)

        return {'success': True, 'param_signature': param_signature}

    except Exception as e:
        return {'success': False, 'error': str(e), 'param_signature': param_signature}
```

---

### Phase 6: 前端UI增强 (预计30分钟)

#### 6.1 GPU模式切换开关
**文件**: `visualization/static/modules/module5_rqa_pipeline.html`

```html
<!-- 在批处理配置面板顶部添加 -->
<div class="card border-success mb-3">
    <div class="card-header bg-success text-white">
        <h5><i class="fas fa-rocket"></i> GPU并行加速</h5>
    </div>
    <div class="card-body">
        <div class="row align-items-center">
            <!-- GPU模式开关 -->
            <div class="col-md-4">
                <div class="form-check form-switch">
                    <input class="form-check-input" type="checkbox"
                           id="enableGpuMode" checked>
                    <label class="form-check-label" for="enableGpuMode">
                        <strong>启用GPU加速</strong>
                        <small class="text-muted d-block">
                            RTX 3080 Mobile (16GB)
                        </small>
                    </label>
                </div>
            </div>

            <!-- 并行Worker数量 -->
            <div class="col-md-4">
                <label class="form-label"><strong>并行任务数</strong></label>
                <input type="number" class="form-control"
                       id="parallelWorkers" value="4" min="1" max="6">
                <small class="text-muted">建议4-6个 (根据显存调整)</small>
            </div>

            <!-- 预估时间 -->
            <div class="col-md-4">
                <div class="alert alert-info mb-0">
                    <strong>预计耗时</strong><br>
                    <span id="estimatedTime" class="fs-5">计算中...</span>
                </div>
            </div>
        </div>
    </div>
</div>
```

#### 6.2 实时GPU监控面板
```html
<!-- GPU状态监控卡片 -->
<div class="card border-warning mb-3" id="gpuMonitorPanel" style="display:none;">
    <div class="card-header bg-warning text-dark">
        <h5><i class="fas fa-microchip"></i> GPU实时状态</h5>
    </div>
    <div class="card-body">
        <div class="row">
            <!-- GPU利用率 -->
            <div class="col-md-6">
                <label><strong>GPU利用率</strong></label>
                <div class="progress mb-2" style="height: 30px;">
                    <div class="progress-bar bg-success"
                         id="gpuUtilizationBar"
                         style="width: 0%">
                        <span id="gpu-utilization">0%</span>
                    </div>
                </div>
            </div>

            <!-- 显存占用 -->
            <div class="col-md-6">
                <label><strong>显存占用</strong></label>
                <div class="progress mb-2" style="height: 30px;">
                    <div class="progress-bar bg-info"
                         id="gpuMemoryBar"
                         style="width: 0%">
                        <span id="gpu-memory">0 / 16 GB</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- 实时日志流 -->
        <div class="mt-3">
            <label><strong>实时处理日志</strong></label>
            <div id="realtimeLog" class="border p-2"
                 style="height: 150px; overflow-y: auto; background: #1e1e1e; color: #00ff00; font-family: monospace;">
                等待任务启动...
            </div>
        </div>
    </div>
</div>
```

#### 6.3 JavaScript增强
```javascript
// 估算时间计算
function updateEstimatedTime() {
    const totalCombinations = updateBatchCombinationCount();
    const gpuEnabled = document.getElementById('enableGpuMode').checked;
    const workers = parseInt(document.getElementById('parallelWorkers').value) || 4;

    let timePerTask = 50;  // CPU默认50秒

    if (gpuEnabled) {
        timePerTask = 2.5;  // GPU加速后2.5秒
    }

    const totalSeconds = (totalCombinations * timePerTask) / workers;
    const hours = Math.floor(totalSeconds / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);

    document.getElementById('estimatedTime').textContent =
        `${hours}小时 ${minutes}分钟`;
}

// 实时日志添加
function addLogEntry(paramSig, success, skipped) {
    const logDiv = document.getElementById('realtimeLog');
    const timestamp = new Date().toLocaleTimeString();

    let icon = '✅';
    let color = '#00ff00';
    if (skipped) {
        icon = '⏭️';
        color = '#ffaa00';
    } else if (!success) {
        icon = '❌';
        color = '#ff0000';
    }

    const entry = `<div style="color: ${color}">[${timestamp}] ${icon} ${paramSig}</div>`;
    logDiv.innerHTML += entry;
    logDiv.scrollTop = logDiv.scrollHeight;  // 自动滚动到底部
}

// 修改批处理执行函数
async function startBatchExecution() {
    const gpuEnabled = document.getElementById('enableGpuMode').checked;
    const workers = parseInt(document.getElementById('parallelWorkers').value) || 4;

    const apiEndpoint = gpuEnabled
        ? '/api/rqa-pipeline/batch-execute-gpu'
        : '/api/rqa-pipeline/batch-execute';

    const batchConfig = {
        m_range: { /* ... */ },
        tau_range: { /* ... */ },
        eps_range: { /* ... */ },
        lmin_range: { /* ... */ },
        n_workers: workers
    };

    // 显示GPU监控面板
    if (gpuEnabled) {
        document.getElementById('gpuMonitorPanel').style.display = 'block';
    }

    try {
        const response = await fetch(apiEndpoint, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({batch_config: batchConfig})
        });

        const result = await response.json();
        console.log('批处理结果:', result);

    } catch (error) {
        console.error('批处理失败:', error);
        alert('批处理执行失败: ' + error.message);
    }
}
```

---

### Phase 7: 性能测试与调优 (预计60分钟)

#### 7.1 基准测试脚本
**文件**: `tests/benchmark_gpu_parallel.py`

```python
import time
import numpy as np
from visualization.parallel_executor import GPUParallelExecutor

def benchmark_full_pipeline():
    """完整pipeline性能测试"""

    # 测试参数集 (12个组合)
    test_params = [
        {'m': m, 'tau': 1, 'eps': 0.06, 'lmin': 2}
        for m in range(1, 13)
    ]

    print("="*60)
    print("GPU并行加速性能测试")
    print("="*60)

    # 测试不同worker数量
    for n_workers in [1, 2, 4, 6]:
        executor = GPUParallelExecutor(n_workers=n_workers)

        start = time.time()
        results = executor.execute_batch(test_params)
        elapsed = time.time() - start

        success_count = sum(1 for _, _, r in results if r.get('success'))

        print(f"\nWorker数量: {n_workers}")
        print(f"  总耗时: {elapsed:.1f}秒")
        print(f"  单任务平均: {elapsed/len(test_params):.1f}秒")
        print(f"  成功率: {success_count}/{len(test_params)}")
        print(f"  理论加速比: {1*50/(elapsed/len(test_params)):.1f}x")

if __name__ == '__main__':
    benchmark_full_pipeline()
```

#### 7.2 性能优化检查清单

| 优化项 | 目标 | 验证方法 |
|--------|------|----------|
| GPU利用率 | >80% | `nvidia-smi dmon` |
| 显存占用 | <14GB (留2GB buffer) | `nvidia-smi` |
| CPU瓶颈 | <30% | 任务管理器 |
| 磁盘I/O | <20% | 资源监视器 |
| 单任务耗时 | <3秒 | benchmark脚本 |
| 并行效率 | >80% | 对比单线程 |

#### 7.3 常见性能问题排查

**问题1: GPU利用率低 (<50%)**
```python
# 原因: CPU预处理成为瓶颈
# 解决: 增加数据预加载线程

from concurrent.futures import ThreadPoolExecutor

def preload_data_async(param_list):
    """异步预加载数据"""
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(load_subject_data, p) for p in param_list]
        return [f.result() for f in futures]
```

**问题2: 显存溢出 (OOM)**
```python
# 原因: 并行任务过多
# 解决: 动态调整worker数量

def adaptive_worker_count():
    """根据显存动态调整"""
    free_mem = cp.cuda.Device(0).mem_info[0]

    if free_mem < 2e9:  # 小于2GB
        return 2
    elif free_mem < 4e9:  # 2-4GB
        return 3
    else:
        return 4
```

**问题3: 磁盘I/O瓶颈**
```python
# 原因: 频繁读写metadata.json
# 解决: 批量写入

class MetadataBuffer:
    """元数据缓冲写入"""
    def __init__(self, flush_interval=10):
        self.buffer = {}
        self.flush_interval = flush_interval
        self.counter = 0

    def update(self, param_sig, step, value):
        self.buffer.setdefault(param_sig, {})[step] = value
        self.counter += 1

        if self.counter >= self.flush_interval:
            self.flush()

    def flush(self):
        """批量写入磁盘"""
        for param_sig, updates in self.buffer.items():
            metadata_file = os.path.join(MODULE10_DATASET_ROOT, param_sig, 'metadata.json')
            # 批量更新...
        self.buffer.clear()
        self.counter = 0
```

---

## 📈 预期性能提升

### 性能对比表

| 场景 | 当前方案 | GPU并行方案 | 提升倍数 |
|------|---------|------------|---------|
| **单任务耗时** | 50秒 | 2.5秒 | **20x** |
| **100组合** | 1.4小时 | 4分钟 | **21x** |
| **1,200组合** | 16.7小时 | 50分钟 | **20x** |
| **10,200组合** | 142小时 | **6.5小时** | **22x** |

### 资源利用率

| 指标 | 优化前 | 优化后 |
|------|--------|--------|
| GPU利用率 | 0% | 85-90% |
| CPU利用率 | 15% (单核) | 50% (多核) |
| 显存占用 | 0 GB | 12-14 GB |
| 系统内存 | 2 GB | 8 GB |
| 磁盘I/O | 低 | 中等 |

---

## 🚀 实施时间表

| 阶段 | 任务 | 预计耗时 | 关键产出 |
|------|------|---------|---------|
| Phase 1 | 环境准备 | 45分钟 | PyTorch+CuPy安装完成 |
| Phase 2 | GPU RQA核心 | 90分钟 | `rqa_analyzer_gpu.py` |
| Phase 3 | 并行引擎 | 60分钟 | `parallel_executor.py` |
| Phase 4 | WebSocket | 45分钟 | 实时进度推送 |
| Phase 5 | API集成 | 30分钟 | `/batch-execute-gpu` |
| Phase 6 | 前端UI | 30分钟 | GPU监控面板 |
| Phase 7 | 性能测试 | 60分钟 | 基准测试报告 |
| **总计** | | **6小时** | 完整GPU并行系统 |

---

## ⚠️ 风险与应对

### 技术风险

| 风险 | 概率 | 影响 | 应对措施 |
|------|------|------|---------|
| CUDA版本不兼容 | 低 | 高 | 使用cu121轮子 (向后兼容) |
| 显存溢出 | 中 | 中 | 动态调整worker数量 |
| 多进程GPU冲突 | 中 | 高 | 使用spawn上下文+显式设备绑定 |
| Windows进程限制 | 低 | 中 | 使用ProcessPoolExecutor |

### 回退方案

如果GPU加速出现问题:
1. **快速回退**: 保留原CPU版本API (`/batch-execute`)
2. **降级策略**: GPU失败自动切换到CPU
3. **调试模式**: 添加`--cpu-only`启动参数

```python
# 自动降级示例
def execute_rqa_with_fallback(params):
    try:
        # 优先GPU
        return compute_rqa_1d_gpu(params)
    except (cp.cuda.memory.OutOfMemoryError, RuntimeError):
        # 降级到CPU
        print("⚠️ GPU失败，切换到CPU模式")
        return compute_rqa_1d_cpu(params)
```

---

## 📝 验收标准

### 功能验收
- [ ] 成功安装PyTorch GPU版本 + CuPy
- [ ] GPU版RQA计算正确性验证 (与CPU版本对比误差<0.1%)
- [ ] 4-worker并行执行无错误
- [ ] WebSocket实时进度正常推送
- [ ] GPU监控面板实时更新

### 性能验收
- [ ] 单任务耗时 < 3秒 (相比CPU 50秒)
- [ ] 10,200组合总耗时 < 8小时 (目标6.5小时)
- [ ] GPU利用率 > 80%
- [ ] 显存占用稳定在 12-14GB
- [ ] 无内存泄漏 (长时间运行显存不增长)

### 用户体验验收
- [ ] 前端可切换GPU/CPU模式
- [ ] 实时日志流畅显示 (无卡顿)
- [ ] 进度条准确反映实际进度
- [ ] 出错时有明确提示

---

## 📚 参考资料

### 官方文档
1. CuPy官方文档: https://docs.cupy.dev/en/stable/
2. PyTorch CUDA最佳实践: https://pytorch.org/docs/stable/notes/cuda.html
3. Flask-SocketIO文档: https://flask-socketio.readthedocs.io/

### 性能优化参考
1. CUDA编程指南: https://docs.nvidia.com/cuda/cuda-c-programming-guide/
2. Python多进程GPU共享: https://stackoverflow.com/questions/tagged/multiprocessing+cuda
3. RQA算法优化论文: Marwan et al. (2007) "Recurrence plots for the analysis of complex systems"

---

## 🔧 后续扩展

### Phase 8: 分布式扩展 (可选)
如果需要处理更大规模数据 (100,000+组合):
- 添加Redis任务队列
- 支持多GPU并行 (RTX 3080 + 其他GPU)
- 集群部署 (多台机器协同)

### Phase 9: 算法优化 (可选)
- 实现自适应ε选择算法
- 添加RQA指标缓存机制
- 优化距离矩阵计算 (使用CUDA kernel)

---

**文档版本**: v1.0
**最后更新**: 2025-10-01
**维护者**: Claude AI Assistant
