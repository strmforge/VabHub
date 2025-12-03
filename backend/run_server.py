"""
简化的服务启动脚本
直接启动uvicorn服务器，跳过所有检查
用于快速启动和测试

# 启动后端服务测试完整功能
cd backend && python run_server.py

# 访问通知API
curl http://localhost:8000/api/notifications/
"""

import uvicorn
import sys
from pathlib import Path

# 添加backend目录到路径
backend_dir = Path(__file__).parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

if __name__ == "__main__":
    print("="*60)
    print("启动 VabHub 服务器")
    print("="*60)
    print("主机: 0.0.0.0")
    print("端口: 8000")
    print("API文档: http://localhost:8000/docs")
    print("="*60)
    print("")
    
    try:
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n服务器已停止")
    except Exception as e:
        print(f"\n启动失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

