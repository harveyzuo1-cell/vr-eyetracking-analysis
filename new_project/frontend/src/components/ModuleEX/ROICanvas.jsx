import React, { useRef, useEffect, useState } from 'react';
import { message } from 'antd';
import { useTranslation } from 'react-i18next';

const ROICanvas = ({
  imageUrl,
  imageDimensions,
  rois,
  selectedRoi,
  drawingMode,
  onAddRoi,
  onUpdateRoi,
  onSelectRoi,
  taskId,
  version
}) => {
  const { t } = useTranslation(['module11']);
  const canvasRef = useRef(null);
  const [image, setImage] = useState(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [startPoint, setStartPoint] = useState(null);

  // 加载图片
  useEffect(() => {
    if (!imageUrl) {
      setImage(null);
      return;
    }

    const img = new Image();
    img.onload = () => {
      setImage(img);
    };
    img.onerror = () => {
      message.error(t('imageLoadFailed'));
      setImage(null);
    };
    img.src = imageUrl;
  }, [imageUrl, t]);

  // 绘制Canvas
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !image) return;

    const ctx = canvas.getContext('2d');
    const { width, height } = imageDimensions;

    // 清空画布
    ctx.clearRect(0, 0, width, height);

    // 绘制背景图片
    ctx.drawImage(image, 0, 0, width, height);

    // 定义ROI类型对应的颜色
    const typeColors = {
      'KW': '#1890ff',    // 蓝色
      'INST': '#52c41a',  // 绿色
      'BG': '#faad14'     // 橙色
    };

    // 绘制所有ROI
    const allRois = [
      ...(rois.keywords || []),
      ...(rois.instructions || []),
      ...(rois.background || [])
    ];

    allRois.forEach(roi => {
      const isSelected = selectedRoi && selectedRoi.id === roi.id;
      const type = roi.id.split('_')[0]; // 从ID中提取类型 (KW/INST/BG)
      const color = typeColors[type] || '#999';

      // 使用统一的normalized_coords格式 [x, y, w, h]
      if (!roi.normalized_coords || !Array.isArray(roi.normalized_coords)) {
        console.warn('Invalid ROI format (missing normalized_coords):', roi);
        return;
      }

      const x = roi.normalized_coords[0] * width;
      const y = roi.normalized_coords[1] * height;
      const w = roi.normalized_coords[2] * width;
      const h = roi.normalized_coords[3] * height;

      // 绘制矩形
      ctx.strokeStyle = color;
      ctx.lineWidth = isSelected ? 3 : 2;
      ctx.strokeRect(x, y, w, h);

      // 如果选中，添加填充效果
      if (isSelected) {
        ctx.fillStyle = color + '20'; // 添加透明度
        ctx.fillRect(x, y, w, h);
      }

      // 绘制标签
      ctx.fillStyle = color;
      ctx.fillRect(x, y - 24, ctx.measureText(roi.id).width + 8, 24);
      ctx.fillStyle = '#fff';
      ctx.font = '12px sans-serif';
      ctx.fillText(roi.id, x + 4, y - 8);
    });
  }, [image, imageDimensions, rois, selectedRoi]);

  // 鼠标事件处理
  const handleMouseDown = (e) => {
    if (!drawingMode || !taskId) return;

    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();

    // 考虑Canvas缩放：将鼠标坐标转换为Canvas内部坐标
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    const x = (e.clientX - rect.left) * scaleX;
    const y = (e.clientY - rect.top) * scaleY;

    setIsDrawing(true);
    setStartPoint({ x, y });
  };

  const handleMouseMove = (e) => {
    if (!isDrawing || !startPoint) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    const rect = canvas.getBoundingClientRect();

    // 考虑Canvas缩放
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    const currentX = (e.clientX - rect.left) * scaleX;
    const currentY = (e.clientY - rect.top) * scaleY;

    // 重新绘制（清除临时绘制）
    const { width, height } = imageDimensions;
    ctx.clearRect(0, 0, width, height);
    ctx.drawImage(image, 0, 0, width, height);

    // 绘制临时矩形
    ctx.strokeStyle = '#1890ff';
    ctx.lineWidth = 2;
    ctx.setLineDash([5, 5]);
    ctx.strokeRect(
      startPoint.x,
      startPoint.y,
      currentX - startPoint.x,
      currentY - startPoint.y
    );
    ctx.setLineDash([]);
  };

  const handleMouseUp = (e) => {
    if (!isDrawing || !startPoint) return;

    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();

    // 考虑Canvas缩放
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    const endX = (e.clientX - rect.left) * scaleX;
    const endY = (e.clientY - rect.top) * scaleY;

    const { width, height } = imageDimensions;

    // 计算归一化坐标
    const x1 = Math.min(startPoint.x, endX) / width;
    const y1 = Math.min(startPoint.y, endY) / height;
    const w = Math.abs(endX - startPoint.x) / width;
    const h = Math.abs(endY - startPoint.y) / height;

    // 验证ROI大小
    if (w > 0.01 && h > 0.01) { // 最小尺寸限制
      // 创建完整的ROI对象，而不是只传坐标数组
      const newRoi = {
        type: drawingMode, // 'KW', 'INST', 或 'BG'
        task_id: taskId,
        normalized_coords: [x1, y1, w, h],
        version: version
      };
      onAddRoi(newRoi);
    } else {
      message.warning(t('roiTooSmall'));
    }

    setIsDrawing(false);
    setStartPoint(null);
  };

  const handleCanvasClick = (e) => {
    if (drawingMode) return; // 绘制模式下不处理点击选择

    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    const { width, height } = imageDimensions;

    // 查找被点击的ROI
    const allRois = [
      ...(rois.keywords || []),
      ...(rois.instructions || []),
      ...(rois.background || [])
    ];

    for (let i = allRois.length - 1; i >= 0; i--) {
      const roi = allRois[i];

      if (!roi.normalized_coords || !Array.isArray(roi.normalized_coords)) {
        continue;
      }

      const roiX = roi.normalized_coords[0] * width;
      const roiY = roi.normalized_coords[1] * height;
      const roiW = roi.normalized_coords[2] * width;
      const roiH = roi.normalized_coords[3] * height;

      if (x >= roiX && x <= roiX + roiW && y >= roiY && y <= roiY + roiH) {
        onSelectRoi(roi);
        return;
      }
    }

    // 如果没有点击到任何ROI，取消选择
    onSelectRoi(null);
  };

  if (!imageUrl || !image) {
    return (
      <div style={{
        border: '1px dashed #d9d9d9',
        borderRadius: '4px',
        padding: '60px',
        textAlign: 'center',
        color: '#999',
        background: '#fafafa'
      }}>
        {imageUrl ? t('loadingImage') : t('noImageSelected')}
      </div>
    );
  }

  return (
    <div style={{ position: 'relative', border: '1px solid #d9d9d9', borderRadius: '4px', overflow: 'hidden' }}>
      <canvas
        ref={canvasRef}
        width={imageDimensions.width}
        height={imageDimensions.height}
        style={{
          display: 'block',
          cursor: drawingMode ? 'crosshair' : 'pointer',
          maxWidth: '100%',
          height: 'auto'
        }}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onClick={handleCanvasClick}
      />
    </div>
  );
};

export default ROICanvas;
