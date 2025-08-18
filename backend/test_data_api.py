"""
测试数据表格API的简化版Flask应用
"""

from flask import Flask, jsonify
from flask_cors import CORS

# 创建简化的Flask应用只用于测试数据表格API
app = Flask(__name__)
CORS(app)

app.config['JSON_AS_ASCII'] = False

# 只注册数据表格API
try:
    from m10_service.data_api import bp as data_bp
    app.register_blueprint(data_bp, url_prefix='/api/m10')
    print("✅ 数据表格API注册成功")
except ImportError as e:
    print(f"❌ 数据表格API注册失败: {e}")

@app.route('/')
def health():
    return jsonify({
        "status": "healthy",
        "message": "数据表格API测试服务",
        "test_endpoints": [
            "/api/m10/data/health",
            "/api/m10/data/list",
            "/api/m10/data/table/Q1"
        ]
    })

if __name__ == '__main__':
    print("🚀 启动数据表格API测试服务...")
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)

