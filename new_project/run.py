"""
应用入口

启动Flask开发服务器
"""
import sys
from pathlib import Path

# 将项目根目录添加到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.web import create_app
from config.settings import get_config

if __name__ == '__main__':
    # 获取配置
    config = get_config()

    # 创建应用
    app = create_app()

    # 启动服务器
    app.run(
        host=config.HOST,
        port=config.PORT,
        debug=config.DEBUG
    )
