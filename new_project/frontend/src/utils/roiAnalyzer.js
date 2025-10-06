/**
 * ROI分析工具
 * 计算眼动轨迹与ROI的交互统计
 */

/**
 * 检查点是否在ROI内部
 * @param {number} x - 点的X坐标
 * @param {number} y - 点的Y坐标
 * @param {Object} roi - ROI配置 {x, y, width, height}
 * @returns {boolean}
 */
function isPointInROI(x, y, roi) {
  return (
    x >= roi.x &&
    x <= roi.x + roi.width &&
    y >= roi.y &&
    y <= roi.y + roi.height
  );
}

/**
 * 计算单个ROI的统计信息
 * @param {Array} gazeData - 眼动数据 [{x, y, timestamp}, ...]
 * @param {Object} roi - ROI配置
 * @returns {Object} 统计结果
 */
export function calculateROIStats(gazeData, roi) {
  if (!gazeData || gazeData.length === 0) {
    return {
      entry_count: 0,
      exit_count: 0,
      points_inside: 0,
      total_points: 0,
      inside_ratio: 0,
      duration_inside: 0
    };
  }

  let entryCount = 0;      // 进入次数
  let exitCount = 0;       // 离开次数
  let pointsInside = 0;    // ROI内数据点数
  let durationInside = 0;  // ROI内停留时间(秒)

  let wasInside = false;   // 上一个点是否在ROI内

  for (let i = 0; i < gazeData.length; i++) {
    const point = gazeData[i];
    const isInside = isPointInROI(point.x, point.y, roi);

    // 统计进入和离开
    if (isInside && !wasInside) {
      entryCount++;  // 从外部进入ROI
    } else if (!isInside && wasInside) {
      exitCount++;   // 从ROI离开到外部
    }

    // 统计ROI内数据点
    if (isInside) {
      pointsInside++;

      // 计算停留时间（当前点到下一个点的时间差）
      if (i < gazeData.length - 1) {
        const timeDiff = gazeData[i + 1].timestamp - point.timestamp;
        durationInside += timeDiff;
      }
    }

    wasInside = isInside;
  }

  const totalPoints = gazeData.length;
  const insideRatio = totalPoints > 0 ? pointsInside / totalPoints : 0;

  return {
    entry_count: entryCount,
    exit_count: exitCount,
    points_inside: pointsInside,
    total_points: totalPoints,
    inside_ratio: insideRatio,
    duration_inside: durationInside
  };
}

/**
 * 计算所有ROI的统计信息
 * @param {Array} gazeData - 眼动数据
 * @param {Array} regions - ROI区域列表
 * @returns {Object} ROI统计结果映射 {roiId: stats}
 */
export function calculateAllROIStats(gazeData, regions) {
  if (!gazeData || !regions || regions.length === 0) {
    return {};
  }

  const roiStats = {};

  regions.forEach(roi => {
    roiStats[roi.id] = calculateROIStats(gazeData, roi);
  });

  return roiStats;
}

export default {
  calculateROIStats,
  calculateAllROIStats
};
