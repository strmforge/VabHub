# 🚀 VabHub 快速开始

## 第一步：测试认证系统（推荐从这里开始）

### 方法1：使用测试脚本（最简单）

```bash
# Windows
test_auth.bat

# Linux/Mac
cd backend
python test_auth.py
```

这个脚本会自动测试所有认证功能。

### 方法2：手动测试

#### 1. 安装依赖
```bash
pip install -r requirements.txt
```

#### 2. 启动后端
```bash
# Windows
start_backend.bat

# Linux/Mac
cd backend
python main.py
```

#### 3. 打开API文档
访问 http://localhost:8000/docs

#### 4. 测试API
- 注册用户：`/api/v1/auth/register`
- 登录：`/api/v1/auth/login`
- 获取用户信息：`/api/v1/auth/me`

详细步骤请查看：[快速测试指南.md](快速测试指南.md)

---

## 第二步：前端测试

### 1. 启动前端
```bash
cd frontend
npm install
npm run dev
```

### 2. 访问登录页面
打开 http://localhost:5173/login

### 3. 测试登录
使用刚才注册的用户名和密码登录

---

## ✅ 测试检查清单

完成以下测试：

- [ ] 运行 `test_auth.py` 测试脚本
- [ ] 后端服务可以启动
- [ ] API文档可以访问
- [ ] 可以注册用户
- [ ] 可以登录获取token
- [ ] 可以使用token获取用户信息
- [ ] 前端可以正常登录

---

## 🎯 如果测试通过

**下一步：实现仪表盘API**

详细计划请查看：[开发启动计划.md](开发启动计划.md)

---

## 📚 相关文档

- [快速测试指南.md](快速测试指南.md) - 详细的测试步骤
- [开发启动计划.md](开发启动计划.md) - 完整的开发计划
- [第一步：认证系统实现.md](第一步：认证系统实现.md) - 认证系统详细说明
- [立即开始.md](立即开始.md) - 快速启动指南

---

**准备好了吗？让我们开始测试！** 🚀

