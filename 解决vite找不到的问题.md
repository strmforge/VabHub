# 解决vite找不到的问题

## 🔍 问题分析

错误信息显示：
```
Error: Cannot find module 'C:\Users\56214\AppData\Roaming\npm\node_modules\vite\bin\vite.js'
```

**原因**: npx试图从全局npm目录查找vite，但vite没有全局安装。

**解决方案**: 需要先安装项目依赖，让vite安装到本地项目的node_modules中。

---

## ✅ 解决方案

### 方案1: 使用安装依赖并启动脚本（推荐）

**双击运行**: `安装依赖并启动.bat`

这个脚本会：
1. 检查Node.js环境
2. 检查vite是否已安装
3. 如果未安装，自动安装依赖
4. 启动前端服务

### 方案2: 手动安装依赖并启动

#### 步骤1: 打开命令提示符

- 按 `Win + R`
- 输入 `cmd`
- 按回车

#### 步骤2: 进入前端目录

```bash
cd F:\VabHub项目\VabHub\frontend
```

#### 步骤3: 安装依赖

```bash
npm install --legacy-peer-deps
```

**注意**: 这可能需要几分钟，请耐心等待。

如果安装过程中有错误，可以尝试：

```bash
npm install --legacy-peer-deps --ignore-scripts
```

#### 步骤4: 启动服务

安装完成后，运行：

```bash
npm run dev
```

或者：

```bash
npx vite --host 0.0.0.0 --port 5173
```

---

## 📋 完整命令序列

### 方法1: 使用npm run dev（推荐）

```bash
cd F:\VabHub项目\VabHub\frontend
npm install --legacy-peer-deps
npm run dev
```

### 方法2: 使用npx

```bash
cd F:\VabHub项目\VabHub\frontend
npm install --legacy-peer-deps
npx vite --host 0.0.0.0 --port 5173
```

### 方法3: 使用本地vite

```bash
cd F:\VabHub项目\VabHub\frontend
npm install --legacy-peer-deps
node_modules\.bin\vite --host 0.0.0.0 --port 5173
```

---

## 🐛 如果安装依赖失败

### 错误1: "npm不是内部或外部命令"

**解决**: Node.js未安装或未添加到PATH

1. 安装Node.js: https://nodejs.org/
2. 安装时选择"Add to PATH"
3. 重启命令提示符

### 错误2: 安装过程中出错

**解决**: 使用忽略脚本的方式安装

```bash
npm install --legacy-peer-deps --ignore-scripts
```

### 错误3: 网络问题

**解决**: 
1. 检查网络连接
2. 尝试使用国内镜像：
   ```bash
   npm config set registry https://registry.npmmirror.com
   npm install --legacy-peer-deps
   ```

---

## ✅ 验证安装

安装完成后，检查vite是否已安装：

```bash
dir node_modules\vite
```

或者：

```bash
dir node_modules\.bin\vite.cmd
```

如果能看到这些文件，说明安装成功。

---

## 🚀 启动服务

安装完成后，使用以下任一方式启动：

### 方式1: 使用npm脚本

```bash
npm run dev
```

### 方式2: 使用npx

```bash
npx vite --host 0.0.0.0 --port 5173
```

### 方式3: 使用本地vite

```bash
node_modules\.bin\vite --host 0.0.0.0 --port 5173
```

---

## 📝 成功标志

如果看到以下内容，说明启动成功：

```
VITE v5.x.x  ready in xxx ms

➜  Local:   http://localhost:5173/
➜  Network: http://192.168.x.x:5173/
```

然后：
1. 打开浏览器
2. 访问 http://localhost:5173
3. 应该能看到VabHub登录页面

---

## 🎯 推荐操作

**立即执行**：

1. **双击运行**: `安装依赖并启动.bat`
   - 这会自动安装依赖并启动服务

2. **或者手动执行**：
   ```bash
   cd F:\VabHub项目\VabHub\frontend
   npm install --legacy-peer-deps
   npm run dev
   ```

---

**按照以上步骤操作，应该可以解决问题！** 🚀

