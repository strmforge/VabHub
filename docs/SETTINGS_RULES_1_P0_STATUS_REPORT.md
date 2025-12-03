# SETTINGS-RULES-1 P0 现状巡检报告

## 项目概述
**项目名称**: SETTINGS-RULES-1：全局 HR 策略 + 分辨率档位 + 三档模式（含 STRM/移动联动）  
**实施范围**: 设定模块下的规则 / 订阅 & 下载 分页  
**核心目标**: 提供统一的全局下载规则，HR/H&R策略、分辨率档位、三档模式联动STRM/移动整理

---

## P0-1 项目目标明确

### 核心功能需求
1. **全局 HR 策略**: IGNORE / SAFE_SKIP / STRICT_SKIP 三种策略
2. **三档模式**: A_SAFE（保种安全） / B_BALANCED（平衡） / C_PRO（老司机）
3. **分辨率档位**: LOW_720P / MID_1080P / HIGH_4K
4. **画质 & 语言偏好**: 源质量、HDR、编码、字幕、音轨、3D控制
5. **STRM/移动联动**: C档强制关闭移动整理避免保种炸雷

### 技术实现范围
- 后端：新增枚举、GlobalRuleSettings模型、API接口、统一过滤函数
- 前端：设定模块UI、三档模式选择、画质偏好配置
- 联动：STRM生成、本地移动、网盘移动的行为决策

---

## P0-2 现状系统巡检结果

### 🔍 HR/H&R 相关解析与过滤逻辑

#### 现有实现位置
- **API响应模型**: `app/api/download.py:45` - `hr_level: Optional[str] = None`
- **下载服务**: `app/modules/download/service.py:459` - `enriched_download["hr_level"] = self._map_hr_level(intel_hr_status)`
- **HR映射函数**: `app/modules/download/service.py:497-508` - 将Local Intel HR状态映射为显示等级

#### HR状态映射逻辑
```python
def _map_hr_level(self, intel_hr_status: str) -> str:
    mapping = {
        "SAFE": "NONE",
        "RISK": "H&R", 
        "ACTIVE": "HR",
        "UNKNOWN": "NONE"
    }
    return mapping.get(intel_hr_status, "NONE")
```

#### 现状分析
- ✅ **HR数据源**: 来自Local Intel系统，已有完整的HR状态检测
- ✅ **数据传递**: HR信息已通过API传递到前端显示
- ⚠️ **过滤逻辑**: 目前只有显示功能，缺少基于HR策略的过滤逻辑
- ⚠️ **策略配置**: 缺少全局HR策略配置和统一过滤入口

---

### 🔍 下载规则配置存放位置

#### 现有设置系统
- **设置模型**: `app/models/settings.py` - `SystemSetting`表结构
- **设置服务**: `app/modules/settings/service.py` - 通用设置管理服务
- **设置分类**: basic, downloader, notification, tmdb, advanced

#### 现状分析
- ✅ **设置基础设施**: 完整的key-value设置系统，支持JSON存储
- ✅ **分类管理**: 支持按category组织设置项
- ⚠️ **全局规则表**: 缺少专门的GlobalRuleSettings模型
- ⚠️ **规则结构**: 当前设置为扁平结构，缺少复杂规则的组织

---

### 🔍 STRM生成/本地移动/网盘移动的配置入口与实现

#### STRM生成系统
- **STRM生成器**: `app/modules/strm/generator.py` - 完整的STRM文件生成功能
- **STRM配置**: `app/modules/strm/config.py` - STRM相关配置管理
- **文件操作模式**: `app/modules/strm/file_operation_mode.py` - 支持移动/复制/硬链接等模式

#### 文件转移系统
- **转移服务**: `app/modules/file_operation/transfer_service.py` - 统一的文件整理服务
- **转移处理器**: `app/modules/file_operation/transfer_handler.py` - 具体的文件操作实现
- **转移历史**: `app/models/transfer_history.py` - 转移操作记录

#### 现状分析
- ✅ **STRM功能**: 完整的STRM生成和文件操作功能
- ✅ **移动模式**: 支持移动、复制、硬链接等多种操作模式
- ✅ **云存储**: 支持115网盘等云存储操作
- ⚠️ **联动控制**: 缺少基于全局规则的移动行为控制
- ⚠️ **安全机制**: 缺少C档模式下的移动限制保护

---

### 🔍 设定模块中的规则/订阅&下载对应的前端页面与API

#### 后端API现状
- **设置API**: `app/api/settings.py` - 通用设置管理接口
- **订阅API**: `app/api/subscription.py` - 订阅相关接口
- **下载API**: `app/api/download.py` - 下载相关接口

#### 前端结构现状
- **设置类型**: `frontend/src/types/settings.ts` - 前端设置类型定义
- **路由配置**: `frontend/src/router/index.ts` - 前端路由配置
- **API服务**: `frontend/src/services/api.ts` - API调用服务

#### 现状分析
- ✅ **API基础**: 完整的设置、订阅、下载API接口
- ✅ **前端框架**: Vue3 + TypeScript + Vuetify技术栈
- ⚠️ **规则UI**: 缺少全局规则配置的前端界面
- ⚠️ **三档模式UI**: 缺少三档模式选择和提示界面

---

## 📋 现状总结

### ✅ 已具备的基础设施
1. **HR数据系统**: 完整的Local Intel HR检测和API传递
2. **设置系统**: 成熟的key-value设置管理框架
3. **文件操作**: 完整的STRM生成和文件转移功能
4. **API框架**: 统一的REST API和前端类型定义

### ⚠️ 需要新增的功能
1. **GlobalRuleSettings模型**: 专门的全局规则数据结构
2. **统一过滤函数**: 基于全局规则的HR/质量过滤逻辑
3. **三档模式UI**: 前端三档模式选择和C档安全提示
4. **联动控制**: STRM/移动行为与全局规则的联动机制

### 🎯 实施策略建议
1. **P1阶段**: 新增枚举和GlobalRuleSettings模型，建立数据基础
2. **P2阶段**: 实现HR策略和三档模式的映射关系
3. **P3阶段**: 开发统一的质量过滤函数
4. **P4阶段**: 实现与现有流程的联动集成
5. **P5阶段**: 开发前端配置界面
6. **P6阶段**: 完善测试和文档

### 🚨 关键风险点
1. **C档模式**: 强制关闭移动整理可能影响现有用户工作流
2. **向后兼容**: 新的全局规则需要与现有订阅规则兼容
3. **性能影响**: 统一过滤函数可能影响搜索和订阅性能

---

## 📝 下一步行动

基于现状巡检结果，建议按P0-P6顺序逐步实施：
1. **立即开始P1**: 新增枚举定义和GlobalRuleSettings模型
2. **数据库迁移**: 创建全局规则表并填充默认值
3. **API接口**: 提供全局规则的CRUD接口
4. **前端集成**: 在设定模块添加全局规则配置界面

这个项目具有良好的基础设施基础，主要工作在于新增统一规则管理和联动控制功能。
