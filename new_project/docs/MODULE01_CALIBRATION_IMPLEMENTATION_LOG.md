# Module01 眼动数据校正功能实施日志

## 📅 实施记录

**开始日期**: 2025-10-03
**当前状态**: Phase 1 Day 1 完成 ✅

---

## Phase 1: 后端开发

### Day 1 完成 ✅

#### 1. CalibrationService (calibration_service.py)
- **文件**: `src/web/modules/module01_data_visualization/calibration_service.py`
- **行数**: 108行
- **覆盖率**: 97%
- **功能**:
  - `apply_position_offset()` - X/Y轴位置偏移
  - `apply_time_trim()` - 起始/结束时间裁剪
  - `save_calibrated_data()` - 保存到data/02_processed
  - `get_saved_params()` - 读取校正参数
  - `load_calibrated_data()` - 加载校正数据
  - `delete_calibration()` - 删除校正

#### 2. CalibrationValidator (calibration_validator.py)
- **文件**: `src/web/modules/module01_data_visualization/calibration_validator.py`
- **行数**: 86行
- **覆盖率**: 81%
- **验证规则**:
  - offsetX/Y: -0.1 ~ 0.1
  - trimStart/End: 0 ~ 60秒
  - 组合裁剪: ≤ 60秒
  - 组别验证: control/mci/ad

#### 3. 单元测试 (test_calibration_service.py)
- **文件**: `tests/test_calibration_service.py`
- **测试数**: 25个
- **通过率**: 100%
- **测试覆盖**:
  - 17个 CalibrationService 测试
  - 8个 CalibrationValidator 测试

**测试结果**:
```
============================= 25 passed in 2.82s ==============================
Coverage:
  calibration_service.py:    108   3    97%
  calibration_validator.py:   86  16    81%
```

---

### Day 2 待完成 (下一步)

#### 1. CalibrationAPI (calibration_api.py)
- [ ] `POST /api/module01/calibration/save`
- [ ] `GET /api/module01/calibration/params`
- [ ] `GET /api/module01/calibration/data`
- [ ] `DELETE /api/module01/calibration/delete`

#### 2. Blueprint注册
- [ ] 注册到 `src/web/routes.py`
- [ ] 测试API端点

#### 3. 集成测试
- [ ] API集成测试
- [ ] 端到端流程测试

---

## Phase 2: 前端开发 (待开始)

### Day 3 计划

#### CalibrationPanel 组件
- **文件**: `frontend/src/components/Calibration/CalibrationPanel.jsx`
- **功能**:
  - 位置校正控件 (X/Y滑块+输入框)
  - 时间裁剪控件 (起始/结束滑块+输入框)
  - 实时预览计算
  - 保存/重置操作

#### calibrationService.js
- **文件**: `frontend/src/services/calibrationService.js`
- **方法**:
  - `saveCalibration()`
  - `getCalibrationParams()`
  - `loadCalibratedData()`

### Day 4 计划

#### GazeTrajectoryChartEnhanced 集成
- **文件**: `frontend/src/components/Charts/GazeTrajectoryChartEnhanced.jsx`
- **集成点**:
  - 导入 CalibrationPanel
  - 实时预览数据更新
  - 样式调整
  - 响应式布局

---

## Phase 3: 测试与优化 (待开始)

### Day 5 计划

- [ ] 端到端测试
- [ ] 性能优化 (防抖处理)
- [ ] 用户验收测试
- [ ] 文档更新

---

## 技术细节

### 数据流

```
用户调整参数 → 前端实时计算预览 → 显示在图表
                                    ↓
                             用户点击保存
                                    ↓
                          API调用 (POST /save)
                                    ↓
                   后端处理 (offset + trim)
                                    ↓
                保存文件 (calibrated.csv + params.json)
```

### 文件命名规范

```
原始数据:
  data/01_raw/{group}/{subject_id}_{task}.csv

校正数据:
  data/02_processed/{group}/{subject_id}_{task}_calibrated.csv

校正参数:
  data/02_processed/{group}/{subject_id}_{task}_calibration_params.json
```

### 参数格式

```javascript
{
  offsetX: 0.01,      // -0.1 ~ 0.1
  offsetY: -0.02,     // -0.1 ~ 0.1
  trimStart: 0.1,     // 0 ~ 60 (秒)
  trimEnd: 0.2        // 0 ~ 60 (秒)
}
```

---

## 后续工作

1. **立即**: 完成 Phase 1 Day 2 (API层)
2. **下一步**: 开始 Phase 2 (前端组件)
3. **最后**: Phase 3 (集成测试)

---

**最后更新**: 2025-10-03
**下次更新**: Phase 1 Day 2 完成后
