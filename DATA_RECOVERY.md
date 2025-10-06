# Data Recovery Guide / 数据恢复指南

## 🚨 Emergency Data Recovery / 紧急数据恢复

### Problem: tasks_available field lost in subject_metadata.json

**Symptoms / 症状:**
- Module01 shows 0 tasks for all subjects
- Module01无法显示任务列表
- subject_metadata.json中tasks_available字段为空数组

**Root Cause / 根本原因:**
`rebuild_subject_metadata.py` script incorrectly overwrote the `tasks_available` field

**Solution / 解决方案:**

```bash
cd "path/to/project"
python restore_tasks_available.py
```

This script will:
1. Scan original V1 data directories (`data/control_raw`, `data/mci_raw`, `data/ad_raw`)
2. Detect which tasks (q1-q5) exist for each subject
3. Update `subject_metadata.json` with correct `tasks_available` arrays
4. Preserve all calibrated data in `new_project/data/02_processed/`

---

## 📋 Data Integrity Verification / 数据完整性验证

### Check if calibrated data is intact / 检查校正数据是否完好

```bash
cd new_project/data/02_processed

# Count calibrated files
ls control/*calibrated*.csv | wc -l  # Should be ~100 (20 subjects × 5 tasks)
ls mci/*calibrated*.csv | wc -l      # Should be ~105 (21 subjects × 5 tasks)
```

### Check if raw data is intact / 检查原始数据是否完好

```bash
cd data

# V1 raw data
ls control_raw/control_group_*/[1-5].txt | wc -l  # Should be 110 (22 subjects × 5 tasks)
ls mci_raw/mci_group_*/[1-5].txt | wc -l          # Should be 110 (22 subjects × 5 tasks)
ls ad_raw/ad_group_*/[1-5].txt | wc -l            # Should be 105 (21 subjects × 5 tasks)
```

---

## 🔧 Manual Recovery Steps / 手动恢复步骤

If automatic recovery fails:

### Step 1: Backup current state / 备份当前状态

```bash
cp new_project/data/01_raw/clinical/subject_metadata.json \
   new_project/data/01_raw/clinical/subject_metadata.json.backup_$(date +%Y%m%d_%H%M%S)
```

### Step 2: Verify original data exists / 验证原始数据存在

```bash
# Check V1 data
ls -la data/control_raw/
ls -la data/mci_raw/
ls -la data/ad_raw/

# Check V2 data
ls -la eye_tracking_data/
```

### Step 3: Re-import via Module00 / 通过Module00重新导入

1. Open browser: `http://127.0.0.1:9090`
2. Go to Module00 (Data Management Center)
3. Click "Scan V1 Legacy Data" / "扫描V1 Legacy数据"
4. Click "Batch Import V1 Data" / "批量导入V1数据"
5. Verify tasks are restored in Module01

---

## 🛡️ Future Prevention / 未来预防措施

### 1. Automatic Backup System / 自动备份系统

`MetadataManager`已优化，每次保存前自动备份（保留最近5个版本）

### 2. Data Validation / 数据验证

修改元数据前务必验证完整性

### 3. Regular Backups / 定期备份

建议每日备份关键数据目录

---

## 📞 Emergency Contacts / 紧急联系

If data recovery fails:
- GitHub Issues: https://github.com/harveyzuo1-cell/vr-eyetracking-analysis/issues

---

## ✅ Post-Recovery Verification / 恢复后验证

1. Check tasks_available fields are restored
2. Restart backend service
3. Test Module01 - verify tasks appear
4. Check calibrated data integrity

**Expected**: V1 subjects with tasks: 58/58

---

**Last Updated**: 2025-10-07
**Version**: 1.0.0
