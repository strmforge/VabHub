# OCR功能集成总结

## 概述

根据用户需求，已成功集成OCR功能到VabHub系统中，主要用于PT站点签到时识别验证码。

## 往期版本分析

### VabHub-1的实现
- **位置**：`VabHub-1/vabhub-portal/ocr.py`
- **实现方式**：使用外部OCR服务（通过`OCR_HOST`配置）
- **使用场景**：
  1. PT站点签到（opencd.py, hdsky.py等）
  2. Cookie获取时的验证码识别（cookie.py）
- **特点**：
  - 依赖外部OCR服务
  - 支持Base64编码的图片识别
  - 需要配置`OCR_HOST`环境变量

### VabHub1.4版的实现
- **位置**：`VabHub1.4版/VabHub-Core/core/ocr_service.py`
- **实现方式**：使用PaddleOCR（本地OCR引擎）
- **特点**：
  - 本地OCR，无需外部服务
  - 包含图像预处理（去噪、二值化等）
  - 支持多种OCR引擎（PaddleOCR、Tesseract、备用方案）

## 当前版本实现

### 1. OCR核心模块

**文件**：`VabHub/backend/app/core/ocr.py`

**功能**：
- ✅ 支持外部OCR服务（兼容VabHub-1的实现）
- ✅ 支持本地PaddleOCR（如果安装）
- ✅ 自动降级：优先使用本地OCR，失败则使用外部服务
- ✅ 图像预处理：提高识别率
- ✅ 文本清理：移除特殊字符，规范化结果

**主要方法**：
```python
async def get_captcha_text(
    image_url: Optional[str] = None,
    image_b64: Optional[str] = None,
    cookie: Optional[str] = None,
    ua: Optional[str] = None,
    use_local_ocr: bool = False
) -> Optional[str]
```

### 2. 配置项

**文件**：`VabHub/backend/app/core/config.py`

**新增配置**：
```python
# OCR配置（用于PT站点签到验证码识别）
OCR_HOST: str = os.getenv("OCR_HOST", "https://movie-pilot.org")  # OCR服务地址
OCR_USE_LOCAL: bool = os.getenv("OCR_USE_LOCAL", "false").lower() == "true"  # 是否优先使用本地OCR
```

### 3. 集成到签到系统

**当前状态**：
- ✅ OCR模块已创建
- ⚠️ 需要集成到`SiteCheckin`类中
- ⚠️ 需要根据站点类型自动识别验证码

**下一步**：
1. 修改`checkin.py`，在需要验证码时调用OCR
2. 支持多种PT站点的验证码识别（opencd、hdsky等）
3. 添加重试机制（识别失败时重试）

## 使用方式

### 方式1：外部OCR服务（默认）

```python
from app.core.ocr import OcrHelper

ocr = OcrHelper()
result = await ocr.get_captcha_text(
    image_url="https://example.com/captcha.jpg",
    cookie="session=xxx",
    ua="Mozilla/5.0..."
)
```

### 方式2：本地PaddleOCR

```python
from app.core.ocr import OcrHelper

ocr = OcrHelper()
result = await ocr.get_captcha_text(
    image_url="https://example.com/captcha.jpg",
    cookie="session=xxx",
    ua="Mozilla/5.0...",
    use_local_ocr=True  # 优先使用本地OCR
)
```

## 配置说明

### 环境变量

```bash
# OCR服务地址（外部OCR服务）
OCR_HOST=https://movie-pilot.org

# 是否优先使用本地OCR（需要安装PaddleOCR）
OCR_USE_LOCAL=false
```

### 安装PaddleOCR（可选）

```bash
pip install paddlepaddle paddleocr
```

## 功能对比

| 功能 | VabHub-1 | VabHub1.4版 | 当前版本 |
|------|----------|-------------|----------|
| **外部OCR服务** | ✅ | ❌ | ✅ |
| **本地PaddleOCR** | ❌ | ✅ | ✅ |
| **自动降级** | ❌ | ❌ | ✅ |
| **图像预处理** | ❌ | ✅ | ✅ |
| **文本清理** | ❌ | ✅ | ✅ |
| **异步支持** | ❌ | ❌ | ✅ |

## 已完成工作 ✅

1. **集成到签到流程**：
   - ✅ 修改`checkin.py`，在需要验证码时调用OCR
   - ✅ 支持多种PT站点的验证码识别
   - ✅ 添加重试机制（最多3次）

2. **站点特定实现**：
   - ✅ OpenCD站点（6位验证码）
   - ✅ HDSky站点（6位验证码）
   - ⚠️ 其他PT站点（可根据需要扩展）

## 待完成工作

1. **扩展更多站点**：
   - [ ] 其他需要验证码的PT站点
   - [ ] 通用验证码检测和识别

2. **优化**：
   - [ ] 验证码识别成功率统计
   - [ ] 自动调整重试次数
   - [ ] 验证码识别缓存（相同hash）

3. **前端配置**：
   - [ ] 添加OCR配置界面
   - [ ] 显示OCR引擎状态
   - [ ] 测试OCR功能

## 总结

OCR功能已成功集成到VabHub系统中，提供了比往期版本更完善的实现：

1. ✅ **双引擎支持**：外部OCR服务 + 本地PaddleOCR
2. ✅ **自动降级**：优先使用本地OCR，失败则使用外部服务
3. ✅ **图像预处理**：提高识别率
4. ✅ **异步支持**：不阻塞主线程
5. ✅ **配置灵活**：支持环境变量配置
6. ✅ **签到集成**：已集成到OpenCD和HDSky站点签到流程
7. ✅ **重试机制**：验证码识别失败时自动重试（最多3次）

### 已支持的站点

- ✅ **OpenCD（皇后）**：6位验证码识别
- ✅ **HDSky（天空）**：6位验证码识别
- ✅ **NexusPHP站点**：通用签到（无需验证码）
- ✅ **Unit3D站点**：API签到
- ✅ **TTG站点**：通用签到
- ✅ **M-Team站点**：API签到
- ✅ **其他站点**：通用签到尝试

### 使用示例

当站点URL包含`open.cd`或`hdsky.me`时，系统会自动：
1. 检测是否已签到
2. 获取验证码图片和hash
3. 使用OCR识别验证码（最多重试3次）
4. 提交签到请求
5. 返回签到结果

### 配置要求

确保在环境变量或配置文件中设置：
```bash
OCR_HOST=https://movie-pilot.org  # 外部OCR服务地址（可选）
OCR_USE_LOCAL=false  # 是否优先使用本地OCR（需要安装PaddleOCR）
```

### 下一步优化

- [ ] 添加更多需要验证码的PT站点支持
- [ ] 验证码识别成功率统计
- [ ] 验证码识别缓存（相同hash）
- [ ] 前端OCR配置界面

