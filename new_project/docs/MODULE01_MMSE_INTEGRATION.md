# Module01 MMSE数据集成补充文档
# Module01 MMSE Data Integration Addendum

**文档版本：** v1.0
**创建日期：** 2025-10-02
**关联文档：** MODULE01_DEVELOPMENT_PLAN.md

---

## 🎯 重要发现：Legacy数据(v1)有完整MMSE评分

### 问题修正

**原规划中的错误假设：**
```json
{
  "control_legacy_1": {
    "has_mmse": false,      // ❌ 错误！
    "mmse_scores": null     // ❌ 错误！
  }
}
```

**实际情况：**
- ✅ **所有65名v1 Legacy受试者都有完整MMSE评分**
- ✅ MMSE数据存储在：`data/MMSE_Score/`目录
- ✅ 分为3个文件：
  - `控制组.csv` (22名受试者: n01-n22)
  - `轻度认知障碍组.csv` (22名受试者: M01-M22)
  - `阿尔兹海默症组.csv` (21名受试者: ad01-ad21)

---

## 📊 MMSE数据结构分析

### 1. 文件位置

```
老项目根目录/data/MMSE_Score/
├── 控制组.csv                    # 控制组MMSE评分 (22人)
├── 轻度认知障碍组.csv             # MCI组MMSE评分 (22人)
└── 阿尔兹海默症组.csv             # AD组MMSE评分 (21人)
```

### 2. CSV文件格式

```csv
受试者,年份,季节,月份,星期,省市区,街道,建筑,楼层,即刻记忆,100-7,93-7,86-7,79-7,72-7,词1,词2,词3,总分
n01,1,1,1,2,2,1,1,1,3,1,1,1,1,1,1,1,1,21
n02,1,1,1,2,2,1,1,1,3,1,1,1,1,1,1,1,0,20
M01,1,1,1,2,2,1,1,1,3,1,1,1,0,0,1,0,0,18
ad01,1,1,0,1,2,1,1,1,2,1,0,0,0,0,0,0,0,12
```

### 3. MMSE评分字段映射

| CSV列名 | 英文字段名 | 中文含义 | 分值 |
|---------|-----------|---------|------|
| 年份 | q1_year | 时间定向-年份 | 0-1 |
| 季节 | q1_season | 时间定向-季节 | 0-1 |
| 月份 | q1_month | 时间定向-月份 | 0-1 |
| 星期 | q1_weekday | 时间定向-星期 | 0-1 |
| 省市区 | q2_province | 地点定向-省市区 | 0-2 |
| 街道 | q2_street | 地点定向-街道 | 0-1 |
| 建筑 | q2_building | 地点定向-建筑 | 0-1 |
| 楼层 | q2_floor | 地点定向-楼层 | 0-1 |
| 即刻记忆 | q3_immediate_memory | 即刻记忆 | 0-3 |
| 100-7 | q4_attention_1 | 注意力和计算-第1次 | 0-1 |
| 93-7 | q4_attention_2 | 注意力和计算-第2次 | 0-1 |
| 86-7 | q4_attention_3 | 注意力和计算-第3次 | 0-1 |
| 79-7 | q4_attention_4 | 注意力和计算-第4次 | 0-1 |
| 72-7 | q4_attention_5 | 注意力和计算-第5次 | 0-1 |
| 词1 | q5_recall_word1 | 延迟回忆-词1 | 0-1 |
| 词2 | q5_recall_word2 | 延迟回忆-词2 | 0-1 |
| 词3 | q5_recall_word3 | 延迟回忆-词3 | 0-1 |
| 总分 | total_score | MMSE总分 | 0-30 |

### 4. 受试者ID映射

**控制组 (Control):**
- MMSE文件ID: `n01`, `n02`, ..., `n22`
- 眼动数据ID: `control_legacy_1`, `control_legacy_2`, ..., `control_legacy_22`
- **映射规则：** `n{N}` → `control_legacy_{N}`

**MCI组:**
- MMSE文件ID: `M01`, `M02`, ..., `M22`
- 眼动数据ID: `mci_legacy_1`, `mci_legacy_2`, ..., `mci_legacy_22`
- **映射规则：** `M{N}` → `mci_legacy_{N}`

**AD组:**
- MMSE文件ID: `ad01`, `ad02`, ..., `ad21`
- 眼动数据ID: `ad_legacy_1`, `ad_legacy_2`, ..., `ad_legacy_21`
- **映射规则：** `ad{N}` → `ad_legacy_{N}`

---

## 🔧 技术实现方案

### 1. 创建MMSE数据加载器

**新增类：** `MMSEDataLoader`

**文件位置：** `src/web/modules/module01_data_visualization/mmse_loader.py`

```python
"""
MMSE数据加载器
用于读取Legacy数据的MMSE评分
"""
import pandas as pd
from pathlib import Path
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class MMSEDataLoader:
    """MMSE数据加载器 - 读取Legacy MMSE评分"""

    def __init__(self, mmse_data_dir: str = None):
        """
        初始化MMSE数据加载器

        Args:
            mmse_data_dir: MMSE数据目录，默认为老项目的data/MMSE_Score/
        """
        if mmse_data_dir is None:
            # 默认路径：new_project -> az - 副本 (11) -> data/MMSE_Score
            current_file = Path(__file__)
            project_root = current_file.parent.parent.parent.parent.parent.parent
            mmse_data_dir = project_root / "data" / "MMSE_Score"

        self.mmse_data_dir = Path(mmse_data_dir)
        self.mmse_cache = {}  # 缓存MMSE数据
        logger.info(f"MMSEDataLoader initialized with dir: {self.mmse_data_dir}")

        # 加载MMSE数据到缓存
        self._load_all_mmse_data()

    def _load_all_mmse_data(self):
        """加载所有MMSE数据到缓存"""
        try:
            # 文件映射
            files = {
                'control': self.mmse_data_dir / "控制组.csv",
                'mci': self.mmse_data_dir / "轻度认知障碍组.csv",
                'ad': self.mmse_data_dir / "阿尔兹海默症组.csv"
            }

            for group, file_path in files.items():
                if file_path.exists():
                    df = pd.read_csv(file_path, encoding='utf-8-sig')
                    # 转换为字典，以受试者ID为key
                    for _, row in df.iterrows():
                        subject_id = self._map_mmse_id_to_subject_id(group, str(row['受试者']))
                        self.mmse_cache[subject_id] = self._parse_mmse_row(row)

            logger.info(f"Loaded MMSE data for {len(self.mmse_cache)} subjects")

        except Exception as e:
            logger.error(f"Failed to load MMSE data: {e}", exc_info=True)

    def _map_mmse_id_to_subject_id(self, group: str, mmse_id: str) -> str:
        """
        将MMSE文件中的ID映射到系统subject_id

        Args:
            group: control/mci/ad
            mmse_id: MMSE文件中的受试者ID (如 'n01', 'M01', 'ad01')

        Returns:
            系统subject_id (如 'control_legacy_1', 'mci_legacy_1')
        """
        # 提取数字部分
        import re
        match = re.search(r'\d+', mmse_id)
        if not match:
            return None

        number = int(match.group())

        # 生成subject_id
        return f"{group}_legacy_{number}"

    def _parse_mmse_row(self, row: pd.Series) -> Dict:
        """
        解析MMSE数据行

        Args:
            row: DataFrame行数据

        Returns:
            解析后的MMSE字典
        """
        return {
            "q1_time_orientation": {
                "year": int(row.get('年份', 0)),
                "season": int(row.get('季节', 0)),
                "month": int(row.get('月份', 0)),
                "weekday": int(row.get('星期', 0)),
                "subtotal": int(row.get('年份', 0)) + int(row.get('季节', 0)) +
                           int(row.get('月份', 0)) + int(row.get('星期', 0))
            },
            "q2_place_orientation": {
                "province": int(row.get('省市区', 0)),
                "street": int(row.get('街道', 0)),
                "building": int(row.get('建筑', 0)),
                "floor": int(row.get('楼层', 0)),
                "subtotal": int(row.get('省市区', 0)) + int(row.get('街道', 0)) +
                           int(row.get('建筑', 0)) + int(row.get('楼层', 0))
            },
            "q3_immediate_memory": int(row.get('即刻记忆', 0)),
            "q4_attention": {
                "step1": int(row.get('100-7', 0)),
                "step2": int(row.get('93-7', 0)),
                "step3": int(row.get('86-7', 0)),
                "step4": int(row.get('79-7', 0)),
                "step5": int(row.get('72-7', 0)),
                "subtotal": int(row.get('100-7', 0)) + int(row.get('93-7', 0)) +
                           int(row.get('86-7', 0)) + int(row.get('79-7', 0)) +
                           int(row.get('72-7', 0))
            },
            "q5_recall": {
                "word1": int(row.get('词1', 0)),
                "word2": int(row.get('词2', 0)),
                "word3": int(row.get('词3', 0)),
                "subtotal": int(row.get('词1', 0)) + int(row.get('词2', 0)) +
                           int(row.get('词3', 0))
            },
            "total_score": int(row.get('总分', 0))
        }

    def get_mmse_score(self, subject_id: str) -> Optional[Dict]:
        """
        获取指定受试者的MMSE评分

        Args:
            subject_id: 受试者ID (如 'control_legacy_1')

        Returns:
            MMSE评分字典，如果不存在返回None
        """
        return self.mmse_cache.get(subject_id)

    def has_mmse_score(self, subject_id: str) -> bool:
        """
        检查受试者是否有MMSE评分

        Args:
            subject_id: 受试者ID

        Returns:
            True如果有MMSE评分，否则False
        """
        return subject_id in self.mmse_cache

    def get_all_subjects_with_mmse(self) -> list:
        """
        获取所有有MMSE评分的受试者ID列表

        Returns:
            受试者ID列表
        """
        return list(self.mmse_cache.keys())
```

---

### 2. 集成到DataVisualizationService

**修改文件：** `src/web/modules/module01_data_visualization/service.py`

```python
from .mmse_loader import MMSEDataLoader

class DataVisualizationService:
    """数据可视化服务类"""

    def __init__(self, data_root: Optional[str] = None):
        # ... 现有代码 ...

        # 初始化MMSE加载器
        self.mmse_loader = MMSEDataLoader()
        logger.info("MMSEDataLoader initialized")

    def get_subjects(self, group: str) -> Dict[str, Any]:
        """获取指定组别的受试者列表"""
        # ... 现有代码 ...

        subjects = []
        for subject_dir in sorted(group_path.iterdir()):
            if subject_dir.is_dir():
                subject_id = subject_dir.name

                # 检查是否有MMSE评分
                has_mmse = self.mmse_loader.has_mmse_score(subject_id)
                mmse_score = None
                if has_mmse:
                    mmse_data = self.mmse_loader.get_mmse_score(subject_id)
                    mmse_score = mmse_data.get('total_score') if mmse_data else None

                subjects.append({
                    "id": subject_id,
                    "task_count": len(task_files),
                    "has_mmse": has_mmse,
                    "mmse_total": mmse_score  # 新增字段
                })

        return {
            "success": True,
            "data": subjects
        }

    def load_raw_data(self, group: str, subject_id: str, task_id: str) -> Dict[str, Any]:
        """加载原始眼动数据"""
        # ... 现有读取CSV代码 ...

        # 获取MMSE评分
        mmse_scores = None
        has_mmse = self.mmse_loader.has_mmse_score(subject_id)
        if has_mmse:
            mmse_scores = self.mmse_loader.get_mmse_score(subject_id)

        # 元数据
        metadata = {
            "group": group,
            "subject_id": subject_id,
            "task": task_id,
            "file_path": str(data_file),
            "has_mmse": has_mmse,
            "mmse_scores": mmse_scores  # 新增字段
        }

        return {
            "success": True,
            "data": data,
            "stats": stats,
            "metadata": metadata
        }
```

---

## ✅ 任务清单更新

### 新增任务（插入到Phase 1）

#### Task 1.4: 创建MMSE数据加载器
**优先级：** P0
**工作量：** 1.5小时

**任务内容：**
1. 创建 `mmse_loader.py` 文件
2. 实现MMSE CSV文件读取
3. 实现ID映射逻辑 (n01→control_legacy_1)
4. 解析MMSE各项评分
5. 提供缓存机制

#### Task 1.5: 集成MMSE到DataVisualizationService
**优先级：** P0
**工作量：** 0.5小时

**任务内容：**
1. 在Service初始化时创建MMSEDataLoader实例
2. 修改 `get_subjects()` 添加MMSE字段
3. 修改 `load_raw_data()` 添加MMSE评分到metadata

---

## 📊 API响应格式更新

### API 2: GET /api/data/subjects?group=control

**更新后的响应：**
```json
{
  "success": true,
  "data": [
    {
      "id": "control_legacy_1",
      "task_count": 5,
      "data_version": "v1",
      "roi_layout": "v1",
      "source_type": "legacy",
      "has_mmse": true,                    // ✅ 修正为true
      "mmse_total": 21,                    // ✅ 新增总分
      "import_date": "2025-10-02T01:07:50.655133",
      "display_name": "Control Legacy #1"
    }
  ]
}
```

### API 4: GET /api/data/raw?...&subject_id=control_legacy_1&...

**metadata字段更新：**
```json
{
  "metadata": {
    "subject_id": "control_legacy_1",
    "group": "control",
    "task": "q1",
    "data_version": "v1",
    "roi_layout": "v1",
    "source_type": "legacy",
    "import_date": "2025-10-02T01:07:50.655133",
    "has_mmse": true,                      // ✅ 修正为true
    "mmse_scores": {                       // ✅ 完整MMSE评分
      "q1_time_orientation": {
        "year": 1,
        "season": 1,
        "month": 1,
        "weekday": 2,
        "subtotal": 5
      },
      "q2_place_orientation": {
        "province": 2,
        "street": 1,
        "building": 1,
        "floor": 1,
        "subtotal": 5
      },
      "q3_immediate_memory": 3,
      "q4_attention": {
        "step1": 1,
        "step2": 1,
        "step3": 1,
        "step4": 1,
        "step5": 1,
        "subtotal": 5
      },
      "q5_recall": {
        "word1": 1,
        "word2": 1,
        "word3": 1,
        "subtotal": 3
      },
      "total_score": 21
    },
    "file_path": "data/01_raw/control/control_legacy_1_q1.csv"
  }
}
```

---

## 🎨 前端显示优化

### SubjectInfo组件更新

**MMSE显示增强：**

```jsx
<Descriptions.Item label={t('subjectInfo.mmse')}>
  {subjectData.has_mmse ? (
    <Space direction="vertical">
      <Tag color="success">
        {t('subjectInfo.mmseAvailable')}
        <strong> 总分: {subjectData.mmse_total}/30</strong>
      </Tag>
      {/* 评分等级提示 */}
      {subjectData.mmse_total >= 27 && (
        <Text type="success">认知正常</Text>
      )}
      {subjectData.mmse_total >= 21 && subjectData.mmse_total < 27 && (
        <Text type="warning">轻度认知障碍</Text>
      )}
      {subjectData.mmse_total < 21 && (
        <Text type="danger">中重度认知障碍</Text>
      )}
    </Space>
  ) : (
    <Tag>{t('subjectInfo.mmseNotAvailable')}</Tag>
  )}
</Descriptions.Item>
```

---

## 📈 统计信息更新

### 组别统计更新

**修正后的MMSE可用性统计：**

| 组别 | v1受试者数 | v1有MMSE | v2受试者数 | v2有MMSE | 总MMSE可用数 |
|------|-----------|---------|-----------|---------|------------|
| Control | 22 | 22 ✅ | 32 | 32 ✅ | 54 |
| MCI | 22 | 22 ✅ | 20 | 20 ✅ | 42 |
| AD | 21 | 21 ✅ | 21 | 21 ✅ | 42 |
| **总计** | **65** | **65** | **73** | **73** | **138** |

**重要发现：**
- ✅ **所有138名受试者（v1 + v2）都有完整的MMSE评分！**
- ✅ v1 Legacy数据：65/65 有MMSE
- ✅ v2 Eye Tracking数据：73/73 有MMSE

---

## 📝 工作量调整

### Phase 1任务更新（总工时：7小时）

| 任务 | 原工时 | 新增内容 | 新工时 |
|-----|-------|---------|--------|
| Task 1.1 - MetadataReader | 1h | 无变化 | 1h |
| Task 1.2 - 重构Service | 2h | 无变化 | 2h |
| Task 1.3 - 文件路径逻辑 | 0.5h | 无变化 | 0.5h |
| **Task 1.4 - MMSE加载器** | **-** | **新增** | **1.5h** |
| **Task 1.5 - 集成MMSE** | **-** | **新增** | **0.5h** |
| Task 5.1 - Backend测试 | 1.5h | 增加MMSE测试 | 1.5h |
| **小计** | **5h** | **+2h** | **7h** |

### 总体工作量更新

| 阶段 | 原工时 | 新工时 | 变化 |
|------|--------|--------|------|
| P0核心 | 5h | 7h | +2h |
| P1增强 | 4h | 4h | - |
| P2优化 | 3.5h | 3.5h | - |
| **总计** | **12.5h** | **14.5h** | **+2h** |

**预计交付时间：** 2.5个工作日（从2天增加到2.5天）

---

## 🧪 测试用例补充

### 新增Backend测试

```python
def test_mmse_loader():
    """测试MMSE数据加载器"""
    loader = MMSEDataLoader()

    # 测试控制组
    mmse_control = loader.get_mmse_score('control_legacy_1')
    assert mmse_control is not None
    assert mmse_control['total_score'] > 0

    # 测试MCI组
    mmse_mci = loader.get_mmse_score('mci_legacy_1')
    assert mmse_mci is not None
    assert mmse_mci['total_score'] > 0

    # 测试AD组
    mmse_ad = loader.get_mmse_score('ad_legacy_1')
    assert mmse_ad is not None
    assert mmse_ad['total_score'] > 0

    # 测试ID映射
    assert loader.has_mmse_score('control_legacy_22')
    assert loader.has_mmse_score('mci_legacy_22')
    assert loader.has_mmse_score('ad_legacy_21')

def test_service_with_mmse():
    """测试Service集成MMSE"""
    service = DataVisualizationService()

    # 测试subjects API包含MMSE
    result = service.get_subjects('control')
    assert result['success'] == True
    first_subject = result['data'][0]
    assert first_subject['has_mmse'] == True
    assert first_subject['mmse_total'] is not None

    # 测试raw data API包含MMSE
    result = service.load_raw_data('control', 'control_legacy_1', 'q1')
    assert result['metadata']['has_mmse'] == True
    assert result['metadata']['mmse_scores'] is not None
    assert result['metadata']['mmse_scores']['total_score'] > 0
```

---

## 📌 关键要点总结

### 修正内容

1. **MMSE可用性修正：**
   - ❌ 原文档：Legacy数据无MMSE (`has_mmse: false`)
   - ✅ 实际情况：所有65名Legacy受试者都有MMSE评分

2. **数据位置补充：**
   - 📁 MMSE数据位于：`data/MMSE_Score/`（老项目根目录）
   - 📁 包含3个CSV文件（按组别分类）

3. **ID映射规则：**
   - `n{N}` → `control_legacy_{N}`
   - `M{N}` → `mci_legacy_{N}`
   - `ad{N}` → `ad_legacy_{N}`

### 新增内容

1. **MMSEDataLoader类** - 读取和解析MMSE数据
2. **Service集成** - 将MMSE数据关联到受试者
3. **API响应增强** - subjects和raw data API返回MMSE评分
4. **Frontend显示** - 显示MMSE总分和评分等级

### 工作量影响

- 新增2小时工作量（P0阶段）
- 总工时从12.5小时增加到14.5小时
- 预计交付时间从2天增加到2.5天

---

**文档状态：** ✅ 已补充MMSE集成方案
**关联主文档：** MODULE01_DEVELOPMENT_PLAN.md
**下一步：** 等待用户确认后实施
