# API Key 配置策略实现总结

**生成时间**: 2025-01-XX  
**目的**: 总结TMDB、TVDB、Fanart API Key的配置策略实现

---

## 📋 一、配置策略

### 1.1 TMDB API Key

**策略**: **用户自己填写**

- ✅ **不提供默认值** - 用户必须自己申请和配置
- ✅ **前端UI提供输入框** - 在系统设置 > 媒体标签页中
- ✅ **提供申请指南链接** - 直接链接到TMDB API申请页面
- ✅ **未配置时显示警告** - 提示用户配置API Key

**实现位置**:
- 后端配置: `VabHub/backend/app/core/config.py` - `TMDB_API_KEY: str = os.getenv("TMDB_API_KEY", "")`
- 前端UI: `VabHub/frontend/src/components/settings/MediaTab.vue` - TMDB API Key输入框和申请指南

### 1.2 TVDB API Key

**策略**: **内置MoviePilot默认值**

- ✅ **提供默认值** - 使用MoviePilot的默认API Key: `ed2aa66b-7899-4677-92a7-67bc9ce3d93a`
- ✅ **用户可覆盖** - 用户可以通过环境变量覆盖
- ✅ **不在UI中显示** - 使用默认值，不显示在系统设置UI中

**实现位置**:
- 后端配置: `VabHub/backend/app/core/config.py` - `TVDB_V4_API_KEY: str = os.getenv("TVDB_V4_API_KEY", "ed2aa66b-7899-4677-92a7-67bc9ce3d93a")`

### 1.3 Fanart API Key

**策略**: **内置MoviePilot默认值**

- ✅ **提供默认值** - 使用MoviePilot的默认API Key: `d2d31f9ecabea050fc7d68aa3146015f`
- ✅ **用户可覆盖** - 用户可以通过环境变量覆盖
- ✅ **不在UI中显示** - 使用默认值，不显示在系统设置UI中

**实现位置**:
- 后端配置: `VabHub/backend/app/core/config.py` - `FANART_API_KEY: str = os.getenv("FANART_API_KEY", "d2d31f9ecabea050fc7d68aa3146015f")`

---

## 📋 二、后端实现

### 2.1 配置文件更新

**文件**: `VabHub/backend/app/core/config.py`

```python
# TMDB API配置（用户需要自己申请和配置）
TMDB_API_KEY: str = os.getenv("TMDB_API_KEY", "")

# TVDB API配置（使用MoviePilot默认值，用户可覆盖）
TVDB_V4_API_KEY: str = os.getenv("TVDB_V4_API_KEY", "ed2aa66b-7899-4677-92a7-67bc9ce3d93a")
TVDB_V4_API_PIN: str = os.getenv("TVDB_V4_API_PIN", "")

# Fanart API配置（使用MoviePilot默认值，用户可覆盖）
FANART_API_KEY: str = os.getenv("FANART_API_KEY", "d2d31f9ecabea050fc7d68aa3146015f")
```

### 2.2 系统设置API更新

**文件**: `VabHub/backend/app/api/system_settings.py`

**更新内容**:
1. **SystemEnvResponse模型** - 添加`TMDB_API_KEY`字段
2. **get_system_env函数** - 添加`TMDB_API_KEY`的获取逻辑
3. **update_system_env函数** - 添加`TMDB_API_KEY`的更新逻辑，标记为加密字段

```python
class SystemEnvResponse(BaseModel):
    # 高级设置 - 媒体
    TMDB_API_KEY: Optional[str] = None  # TMDB API Key（用户需要自己申请）
    # ... 其他字段 ...

@router.get("/env")
async def get_system_env(db = Depends(get_db)):
    # ...
    env_data.TMDB_API_KEY = db_settings.get("TMDB_API_KEY") or app_settings.TMDB_API_KEY or ""
    # ...

@router.post("/env")
async def update_system_env(update: Dict[str, Any], db = Depends(get_db)):
    # ...
    # 确定是否为加密字段
    is_encrypted = key.endswith("_TOKEN") or key.endswith("_KEY") or key.endswith("_PASSWORD")
    # ...
```

---

## 📋 三、前端实现

### 3.1 MediaTab组件更新

**文件**: `VabHub/frontend/src/components/settings/MediaTab.vue`

**更新内容**:
1. **添加TMDB API Key输入框** - 密码类型输入框
2. **添加申请指南链接** - 链接到TMDB API申请页面
3. **添加未配置警告** - 当API Key为空时显示警告

```vue
<!-- TMDB API Key配置 -->
<v-card variant="outlined" class="mb-4">
  <v-card-title class="text-subtitle-1 font-weight-medium">
    <v-icon icon="mdi-key" class="me-2" />
    TMDB API Key
  </v-card-title>
  <v-card-text>
    <v-text-field
      v-model="modelValue.TMDB_API_KEY"
      label="TMDB API Key"
      hint="请前往 TMDB 官网申请您的 API Key。这是使用 TMDB 功能的必需配置。"
      persistent-hint
      type="password"
      variant="outlined"
      density="compact"
      prepend-inner-icon="mdi-key-variant"
      class="mb-2"
      @update:model-value="$emit('update:modelValue', modelValue)"
    />
    <v-btn
      color="primary"
      variant="text"
      prepend-icon="mdi-open-in-new"
      href="https://www.themoviedb.org/settings/api"
      target="_blank"
      size="small"
    >
      前往 TMDB 申请 API Key
    </v-btn>
    <v-alert
      v-if="!modelValue.TMDB_API_KEY"
      type="warning"
      density="compact"
      class="mt-2"
    >
      TMDB API Key 未配置，媒体搜索和识别功能将无法使用。
    </v-alert>
  </v-card-text>
</v-card>
```

---

## 📋 四、配置策略对比

| API Key | 策略 | 默认值 | UI显示 | 用户配置 | 说明 |
|---------|------|--------|--------|----------|------|
| **TMDB** | 用户填写 | ❌ 无 | ✅ 是 | ✅ 必需 | 用户必须申请和配置 |
| **TVDB** | 内置默认 | ✅ MoviePilot | ❌ 否 | ⚠️ 可选 | 使用默认值，用户可覆盖 |
| **Fanart** | 内置默认 | ✅ MoviePilot | ❌ 否 | ⚠️ 可选 | 使用默认值，用户可覆盖 |

---

## 📋 五、用户体验

### 5.1 TMDB API Key配置流程

1. **打开系统设置** - 进入"系统设置" > "媒体"标签页
2. **查看TMDB API Key配置** - 看到输入框和申请指南链接
3. **点击申请链接** - 跳转到TMDB官网申请API Key
4. **填写API Key** - 将申请到的API Key填入输入框
5. **保存设置** - 点击"保存设置"按钮
6. **验证配置** - 如果未配置，会显示警告提示

### 5.2 TVDB和Fanart API Key

- ✅ **开箱即用** - 使用内置默认值，无需配置
- ✅ **用户可覆盖** - 如需使用自己的API Key，可通过环境变量配置
- ✅ **不在UI中显示** - 简化界面，减少用户困惑

---

## 📋 六、安全性考虑

### 6.1 API Key加密存储

- ✅ **数据库加密** - API Key在数据库中加密存储
- ✅ **密码类型输入** - 前端使用`type="password"`隐藏输入
- ✅ **加密字段识别** - 后端自动识别以`_KEY`、`_TOKEN`、`_PASSWORD`结尾的字段为加密字段

### 6.2 默认值安全性

- ⚠️ **TVDB和Fanart默认值** - 使用MoviePilot的默认值，所有用户共享
- ✅ **TMDB无默认值** - 每个用户使用自己的API Key，更安全

---

## 📋 七、总结

### 7.1 实现完成

- ✅ **后端配置** - 更新配置文件，添加TVDB和Fanart默认值
- ✅ **系统设置API** - 添加TMDB_API_KEY字段支持
- ✅ **前端UI** - 添加TMDB API Key输入框和申请指南
- ✅ **用户体验** - 提供清晰的配置流程和警告提示

### 7.2 策略优势

- ✅ **TMDB用户配置** - 每个用户使用自己的API Key，避免共享限制
- ✅ **TVDB/Fanart默认值** - 开箱即用，降低使用门槛
- ✅ **灵活性** - 用户可以通过环境变量覆盖所有API Key

---

**文档生成时间**: 2025-01-XX  
**文档版本**: 1.0

