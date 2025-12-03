"""
VabHub 版本信息
RELEASE-1 R0-1 实现
"""

APP_NAME = "VabHub"
APP_VERSION = "0.1.0-rc1"

# 预留：后续可通过 CI 自动注入
BUILD_COMMIT = None
BUILD_DATE = None


def get_version_info() -> dict:
    """获取完整版本信息"""
    return {
        "name": APP_NAME,
        "version": APP_VERSION,
        "build_commit": BUILD_COMMIT,
        "build_date": BUILD_DATE,
    }
