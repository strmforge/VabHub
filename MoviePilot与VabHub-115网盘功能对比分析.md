# MoviePilot与VabHub 115网盘功能对比分析

## 📋 概述

本文档对比分析MoviePilot和VabHub在115网盘功能实现上的差异，包括文件列表、上传、下载、分片上传、移动、复制、重命名等核心功能。

## 🔍 功能对比

### 1. 文件列表 (list/list_files)

#### MoviePilot实现
```python
def list(self, fileitem: schemas.FileItem) -> List[schemas.FileItem]:
    """目录遍历实现"""
    if fileitem.path == "/":
        cid = '0'
    else:
        cid = fileitem.fileid
    
    items = []
    offset = 0
    
    while True:
        resp = self._request_api(
            "GET",
            "/open/ufile/files",
            "data",
            params={"cid": int(cid), "limit": 1000, "offset": offset, "cur": True, "show_dir": 1}
        )
        # 处理分页
        for item in resp:
            items.append(schemas.FileItem(...))
        
        if len(resp) < 1000:
            break
        offset += len(resp)
    
    return items
```

**特点**:
- ✅ 使用`schemas.FileItem`统一数据模型
- ✅ 支持分页（每页1000条）
- ✅ 自动处理目录和文件
- ✅ 返回标准化的FileItem对象

#### VabHub实现
```python
async def list_files(self, path: str = "/", recursive: bool = False) -> List[CloudFileInfo]:
    """列出文件"""
    folder_id = await self._get_folder_id_by_path(path)
    files = []
    offset = 0
    limit = 1000
    
    while True:
        data = await self._request(
            "GET",
            f"{self.base_url}/open/ufile/files",
            params={
                "cid": int(folder_id),
                "limit": limit,
                "offset": offset,
                "cur": True,
                "show_dir": 1
            }
        )
        # 处理分页
        for item in data["data"]:
            files.append(CloudFileInfo(...))
        
        if len(data["data"]) < limit:
            break
        offset += len(data["data"])
    
    return files
```

**特点**:
- ✅ 异步实现
- ✅ 使用`CloudFileInfo`数据模型
- ✅ 支持分页（每页1000条）
- ✅ 支持递归选项（但未实现）

**对比**:
| 特性 | MoviePilot | VabHub | 说明 |
|------|-----------|--------|------|
| 异步 | ❌ 同步 | ✅ 异步 | VabHub使用async/await |
| 数据模型 | `schemas.FileItem` | `CloudFileInfo` | 两者功能类似 |
| 分页 | ✅ 1000条/页 | ✅ 1000条/页 | 相同 |
| 递归 | ❌ 不支持 | ⚠️ 声明但未实现 | 需要完善 |

---

### 2. 文件上传 (upload/upload_file)

#### MoviePilot实现
```python
def upload(self, target_dir: schemas.FileItem, local_path: Path,
           new_name: Optional[str] = None) -> Optional[schemas.FileItem]:
    """实现带秒传、断点续传和二次认证的文件上传"""
    
    # Step 1: 初始化上传
    init_data = {
        "file_name": target_name,
        "file_size": file_size,
        "target": target_param,
        "fileid": file_sha1,
        "preid": file_preid
    }
    init_resp = self._request_api("POST", "/open/upload/init", data=init_data)
    
    # Step 2: 处理二次认证
    if init_result.get("code") in [700, 701] and sign_check:
        # 计算指定区间的SHA1
        sign_val = hashlib.sha1(chunk).hexdigest().upper()
        # 重新初始化请求
        init_data.update({"pick_code": pick_code, "sign_key": sign_key, "sign_val": sign_val})
        init_resp = self._request_api("POST", "/open/upload/init", data=init_data)
    
    # Step 3: 秒传检测
    if init_result.get("status") == 2:
        logger.info(f"【115】{target_name} 秒传成功")
        return self._delay_get_item(target_path)
    
    # Step 4: 获取上传凭证
    token_resp = self._request_api("GET", "/open/upload/get_token", "data")
    
    # Step 5: 断点续传
    resume_resp = self._request_api("POST", "/open/upload/resume", "data", data={...})
    
    # Step 6: OSS分片上传
    auth = oss2.StsAuth(access_key_id=AccessKeyId, ...)
    bucket = oss2.Bucket(auth, endpoint, bucket_name)
    part_size = determine_part_size(file_size, preferred_size=10 * 1024 * 1024)
    
    upload_id = bucket.init_multipart_upload(object_name, params={...}).upload_id
    parts = []
    
    with open(local_path, 'rb') as fileobj:
        part_number = 1
        offset = 0
        while offset < file_size:
            num_to_upload = min(part_size, file_size - offset)
            result = bucket.upload_part(object_name, upload_id, part_number,
                                        data=SizedFileAdapter(fileobj, num_to_upload))
            parts.append(PartInfo(part_number, result.etag))
            offset += num_to_upload
            part_number += 1
            progress_callback((offset * 100) / file_size)
    
    # 完成上传
    headers = {
        'X-oss-callback': encode_callback(callback["callback"]),
        'x-oss-callback-var': encode_callback(callback["callback_var"]),
        'x-oss-forbid-overwrite': 'false'
    }
    result = bucket.complete_multipart_upload(object_name, upload_id, parts, headers=headers)
    
    return self._delay_get_item(target_path)
```

**特点**:
- ✅ 完整的6步上传流程
- ✅ 支持秒传检测
- ✅ 支持二次认证
- ✅ 支持断点续传
- ✅ 使用oss2进行分片上传
- ✅ 进度回调支持
- ✅ 同步实现，使用`requests.Session`

#### VabHub实现
```python
async def upload_file(self, local_path: str, remote_path: str, 
                     progress_callback: Optional[callable] = None) -> bool:
    """上传文件（支持秒传、断点续传和分片上传）"""
    
    # Step 1: 初始化上传
    init_data = {...}
    init_resp = await self._request("POST", f"{self.base_url}/open/upload/init", data=init_data)
    
    # Step 2: 处理二次认证
    if init_result.get("code") in [700, 701] and sign_check:
        sign_val = hashlib.sha1(chunk).hexdigest().upper()
        init_data.update({...})
        init_resp = await self._request("POST", f"{self.base_url}/open/upload/init", data=init_data)
    
    # Step 3: 秒传检测
    if init_result.get("status") == 2:
        logger.info(f"{target_name} 秒传成功")
        return True
    
    # Step 4: 获取上传凭证
    token_resp = await self._request("GET", f"{self.base_url}/open/upload/get_token")
    
    # Step 5: 断点续传
    resume_resp = await self._request("POST", f"{self.base_url}/open/upload/resume", data={...})
    
    # Step 6: OSS分片上传（使用同步方式，因为oss2是同步库）
    def _sync_upload():
        auth = oss2.StsAuth(...)
        bucket = oss2.Bucket(auth, endpoint, bucket_name)
        part_size = determine_part_size(file_size, preferred_size=10 * 1024 * 1024)
        
        upload_id = bucket.init_multipart_upload(object_name, params={...}).upload_id
        parts = []
        
        with open(local_file, 'rb') as fileobj:
            part_number = 1
            offset = 0
            while offset < file_size:
                num_to_upload = min(part_size, file_size - offset)
                result = bucket.upload_part(object_name, upload_id, part_number,
                                            data=SizedFileAdapter(fileobj, num_to_upload))
                parts.append(PartInfo(part_number, result.etag))
                offset += num_to_upload
                part_number += 1
                if progress_callback:
                    progress = (offset * 100) / file_size
                    progress_callback(progress)
        
        headers = {...}
        result = bucket.complete_multipart_upload(object_name, upload_id, parts, headers=headers)
        return result.status == 200
    
    loop = asyncio.get_event_loop()
    success = await loop.run_in_executor(None, _sync_upload)
    return success
```

**特点**:
- ✅ 完整的6步上传流程
- ✅ 支持秒传检测
- ✅ 支持二次认证
- ✅ 支持断点续传
- ✅ 使用oss2进行分片上传
- ✅ 进度回调支持
- ✅ 异步实现，使用`aiohttp`，但oss2使用`run_in_executor`包装

**对比**:
| 特性 | MoviePilot | VabHub | 说明 |
|------|-----------|--------|------|
| 异步 | ❌ 同步 | ✅ 异步 | VabHub使用async/await |
| 秒传 | ✅ 支持 | ✅ 支持 | 相同 |
| 二次认证 | ✅ 支持 | ✅ 支持 | 相同 |
| 断点续传 | ✅ 支持 | ✅ 支持 | 相同 |
| 分片上传 | ✅ oss2 | ✅ oss2 | 相同 |
| 进度回调 | ✅ 支持 | ✅ 支持 | 相同 |
| 错误处理 | ✅ 完整 | ✅ 完整 | 相同 |
| 延迟获取 | ✅ `_delay_get_item` | ❌ 未实现 | MoviePilot有自动重试机制 |

---

### 3. 文件下载 (download/download_file)

#### MoviePilot实现
```python
def download(self, fileitem: schemas.FileItem, path: Path = None) -> Optional[Path]:
    """带实时进度显示的下载"""
    detail = self.get_item(Path(fileitem.path))
    if not detail:
        return None
    
    # 获取下载链接
    download_info = self._request_api(
        "POST",
        "/open/ufile/downurl",
        "data",
        data={"pick_code": detail.pickcode}
    )
    
    download_url = list(download_info.values())[0].get("url", {}).get("url")
    local_path = path or settings.TEMP_PATH / fileitem.name
    
    # 流式下载
    with self.session.get(download_url, stream=True) as r:
        r.raise_for_status()
        downloaded_size = 0
        
        with open(local_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=self.chunk_size):
                if global_vars.is_transfer_stopped(fileitem.path):
                    return None
                if chunk:
                    f.write(chunk)
                    downloaded_size += len(chunk)
                    if file_size:
                        progress = (downloaded_size * 100) / file_size
                        progress_callback(progress)
        
        progress_callback(100)
    
    return local_path
```

**特点**:
- ✅ 使用`pick_code`获取下载链接
- ✅ 流式下载，支持大文件
- ✅ 进度回调
- ✅ 支持取消下载
- ✅ 错误处理完整

#### VabHub实现
```python
async def download_file(self, file_id: str, save_path: str, 
                       progress_callback: Optional[callable] = None) -> bool:
    """下载文件"""
    # 获取文件信息
    file_info = await self.get_file_info(file_id)
    if not file_info:
        return False
    
    # 获取下载链接
    data = await self._request(
        "POST",
        f"{self.base_url}/open/ufile/downurl",
        data={"pick_code": file_info.metadata.get("pick_code")}
    )
    
    download_url = list(data["data"].values())[0].get("url", {}).get("url")
    
    # 异步下载
    async with self.session.get(download_url) as response:
        response.raise_for_status()
        file_size = int(response.headers.get("Content-Length", 0))
        downloaded_size = 0
        
        with open(save_path, "wb") as f:
            async for chunk in response.content.iter_chunked(self.chunk_size):
                if chunk:
                    f.write(chunk)
                    downloaded_size += len(chunk)
                    if progress_callback and file_size:
                        progress = (downloaded_size * 100) / file_size
                        progress_callback(progress)
        
        if progress_callback:
            progress_callback(100)
    
    return True
```

**特点**:
- ✅ 异步实现
- ✅ 使用`pick_code`获取下载链接
- ✅ 流式下载
- ✅ 进度回调
- ❌ 未实现取消下载

**对比**:
| 特性 | MoviePilot | VabHub | 说明 |
|------|-----------|--------|------|
| 异步 | ❌ 同步 | ✅ 异步 | VabHub使用async/await |
| 流式下载 | ✅ 支持 | ✅ 支持 | 相同 |
| 进度回调 | ✅ 支持 | ✅ 支持 | 相同 |
| 取消下载 | ✅ 支持 | ❌ 未实现 | MoviePilot有取消机制 |
| 错误处理 | ✅ 完整 | ✅ 完整 | 相同 |

---

### 4. 文件移动 (move/move_file)

#### MoviePilot实现
```python
def move(self, fileitem: schemas.FileItem, path: Path, new_name: str) -> bool:
    """原子性移动操作实现"""
    if fileitem.fileid is None:
        fileitem = self.get_item(Path(fileitem.path))
    
    dest_fileitem = self.get_item(path)
    if not dest_fileitem or dest_fileitem.type != "dir":
        return False
    
    resp = self._request_api(
        "POST",
        "/open/ufile/move",
        data={
            "file_ids": int(fileitem.fileid),
            "to_cid": int(dest_fileitem.fileid),
        }
    )
    
    if resp["state"]:
        new_path = Path(path) / fileitem.name
        new_file = self._delay_get_item(new_path)
        if not new_file:
            return False
        if self.rename(new_file, new_name):
            return True
    return False
```

**特点**:
- ✅ 使用`file_ids`（单个int）和`to_cid`
- ✅ 移动后自动重命名
- ✅ 使用`_delay_get_item`延迟获取文件信息
- ✅ 原子性操作

#### VabHub实现
```python
async def move_file(self, file_id: str, target_path: str, new_name: Optional[str] = None) -> bool:
    """移动文件（115网盘，参考VabHub-1实现）"""
    target_id = await self._get_folder_id_by_path(target_path)
    if not target_id:
        return False
    
    data = await self._request(
        "POST",
        f"{self.base_url}/open/ufile/move",
        data={
            "file_ids": int(file_id),  # 单个int
            "to_cid": int(target_id)
        }
    )
    
    if not data or not data.get("state", False):
        return False
    
    # 如果需要重命名，等待移动完成后再重命名
    if new_name:
        await asyncio.sleep(2)  # 等待移动完成
        moved_files = await self.list_files(target_path)
        moved_file = None
        for f in moved_files:
            if f.id == file_id:
                moved_file = f
                break
        
        if moved_file:
            return await self.rename_file(moved_file.id, new_name)
    
    return True
```

**特点**:
- ✅ 使用`file_ids`（单个int）和`to_cid`
- ✅ 移动后可选重命名
- ✅ 使用固定延迟（2秒）等待移动完成
- ✅ 异步实现

**对比**:
| 特性 | MoviePilot | VabHub | 说明 |
|------|-----------|--------|------|
| 异步 | ❌ 同步 | ✅ 异步 | VabHub使用async/await |
| API参数 | ✅ `file_ids`(int) + `to_cid` | ✅ `file_ids`(int) + `to_cid` | 相同 |
| 重命名 | ✅ 自动 | ✅ 可选 | MoviePilot必须重命名 |
| 延迟获取 | ✅ `_delay_get_item`（智能重试） | ⚠️ 固定延迟2秒 | MoviePilot更智能 |

---

### 5. 文件复制 (copy/copy_file)

#### MoviePilot实现
```python
def copy(self, fileitem: schemas.FileItem, path: Path, new_name: str) -> bool:
    """企业级复制实现（支持目录递归复制）"""
    if fileitem.fileid is None:
        fileitem = self.get_item(Path(fileitem.path))
    
    dest_fileitem = self.get_item(path)
    if not dest_fileitem or dest_fileitem.type != "dir":
        return False
    
    resp = self._request_api(
        "POST",
        "/open/ufile/copy",
        data={
            "file_id": int(fileitem.fileid),
            "pid": int(dest_fileitem.fileid),
        }
    )
    
    if resp["state"]:
        new_path = Path(path) / fileitem.name
        new_item = self._delay_get_item(new_path)
        if not new_item:
            return False
        if self.rename(new_item, new_name):
            return True
    return False
```

**特点**:
- ✅ 使用`file_id`（单个int）和`pid`
- ✅ 复制后自动重命名
- ✅ 使用`_delay_get_item`延迟获取文件信息
- ✅ 支持目录递归复制（注释说明）

#### VabHub实现
```python
async def copy_file(self, file_id: str, target_path: str, new_name: Optional[str] = None) -> bool:
    """复制文件（115网盘，参考VabHub-1实现）"""
    target_id = await self._get_folder_id_by_path(target_path)
    if not target_id:
        return False
    
    data = await self._request(
        "POST",
        f"{self.base_url}/open/ufile/copy",
        data={
            "file_id": int(file_id),  # 单个int
            "pid": int(target_id)
        }
    )
    
    if not data or not data.get("state", False):
        return False
    
    # 如果需要重命名，等待复制完成后再重命名
    if new_name:
        await asyncio.sleep(2)  # 等待复制完成
        copied_files = await self.list_files(target_path)
        source_file = await self.get_file_info(file_id)
        if source_file:
            for f in copied_files:
                if f.name == source_file.name and f.id != file_id:
                    return await self.rename_file(f.id, new_name)
    
    return True
```

**特点**:
- ✅ 使用`file_id`（单个int）和`pid`
- ✅ 复制后可选重命名
- ✅ 使用固定延迟（2秒）等待复制完成
- ✅ 异步实现
- ❌ 未实现目录递归复制

**对比**:
| 特性 | MoviePilot | VabHub | 说明 |
|------|-----------|--------|------|
| 异步 | ❌ 同步 | ✅ 异步 | VabHub使用async/await |
| API参数 | ✅ `file_id`(int) + `pid` | ✅ `file_id`(int) + `pid` | 相同 |
| 重命名 | ✅ 自动 | ✅ 可选 | MoviePilot必须重命名 |
| 递归复制 | ✅ 支持（注释说明） | ❌ 未实现 | MoviePilot支持目录递归 |
| 延迟获取 | ✅ `_delay_get_item`（智能重试） | ⚠️ 固定延迟2秒 | MoviePilot更智能 |

---

### 6. 文件重命名 (rename/rename_file)

#### MoviePilot实现
```python
def rename(self, fileitem: schemas.FileItem, name: str) -> bool:
    """重命名文件/目录"""
    resp = self._request_api(
        "POST",
        "/open/ufile/update",
        data={
            "file_id": int(fileitem.fileid),
            "file_name": name
        }
    )
    if not resp:
        return False
    if resp["state"]:
        return True
    return False
```

**特点**:
- ✅ 使用`/open/ufile/update`端点
- ✅ 参数：`file_id`和`file_name`
- ✅ 简洁明了

#### VabHub实现
```python
async def rename_file(self, file_id: str, new_name: str) -> bool:
    """重命名文件（115网盘，参考VabHub-1实现）"""
    data = await self._request(
        "POST",
        f"{self.base_url}/open/ufile/update",
        data={
            "file_id": int(file_id),
            "file_name": new_name
        }
    )
    
    return data is not None and data.get("state", False)
```

**特点**:
- ✅ 使用`/open/ufile/update`端点
- ✅ 参数：`file_id`和`file_name`
- ✅ 异步实现

**对比**:
| 特性 | MoviePilot | VabHub | 说明 |
|------|-----------|--------|------|
| 异步 | ❌ 同步 | ✅ 异步 | VabHub使用async/await |
| API端点 | ✅ `/open/ufile/update` | ✅ `/open/ufile/update` | 相同 |
| 参数 | ✅ `file_id` + `file_name` | ✅ `file_id` + `file_name` | 相同 |

---

## 🎯 关键差异总结

### 1. 架构差异

| 方面 | MoviePilot | VabHub |
|------|-----------|--------|
| 同步/异步 | 同步（requests） | 异步（aiohttp） |
| 数据模型 | `schemas.FileItem` | `CloudFileInfo` |
| 错误处理 | `_request_api`统一处理 | `_request`统一处理 |
| 延迟获取 | `_delay_get_item`（智能重试） | 固定延迟（2秒） |

### 2. 功能完整性

| 功能 | MoviePilot | VabHub | 差距 |
|------|-----------|--------|------|
| 文件列表 | ✅ 完整 | ✅ 完整 | 无 |
| 文件上传 | ✅ 完整 | ✅ 完整 | 无 |
| 文件下载 | ✅ 完整 | ⚠️ 缺少取消 | 小 |
| 文件移动 | ✅ 完整 | ⚠️ 延迟方式不同 | 小 |
| 文件复制 | ✅ 完整（支持递归） | ⚠️ 不支持递归 | 中 |
| 文件重命名 | ✅ 完整 | ✅ 完整 | 无 |
| 延迟获取 | ✅ 智能重试 | ❌ 固定延迟 | 中 |

### 3. 代码质量

| 方面 | MoviePilot | VabHub |
|------|-----------|--------|
| 错误处理 | ✅ 统一且完善 | ✅ 统一且完善 |
| 日志记录 | ✅ 详细 | ✅ 详细 |
| 代码复用 | ✅ 高（`_request_api`） | ✅ 高（`_request`） |
| 线程安全 | ✅ 使用锁 | ⚠️ 异步环境，无需锁 |

## 💡 改进建议

### 1. 实现智能延迟获取（高优先级）
```python
async def _delay_get_item(self, path: str, max_retries: int = 3) -> Optional[CloudFileInfo]:
    """自动延迟重试获取文件信息"""
    for i in range(1, max_retries + 1):
        await asyncio.sleep(2 ** i)  # 指数退避：2秒、4秒、8秒
        file_info = await self.get_file_info_by_path(path)
        if file_info:
            return file_info
    return None
```

### 2. 实现目录递归复制（中优先级）
参考MoviePilot的实现，支持目录的递归复制。

### 3. 实现下载取消机制（中优先级）
```python
async def download_file(self, file_id: str, save_path: str, 
                       progress_callback: Optional[callable] = None,
                       cancel_event: Optional[asyncio.Event] = None) -> bool:
    """下载文件（支持取消）"""
    # 在循环中检查cancel_event
    async for chunk in response.content.iter_chunked(self.chunk_size):
        if cancel_event and cancel_event.is_set():
            logger.info(f"下载已取消: {file_id}")
            return False
        # ... 处理chunk
```

### 4. 优化移动/复制后的文件获取（低优先级）
使用智能延迟获取替代固定延迟。

## ✅ 优势总结

### MoviePilot优势
1. ✅ 经过多次验证，稳定可靠
2. ✅ 智能延迟获取机制
3. ✅ 支持目录递归复制
4. ✅ 统一的错误处理和重试机制

### VabHub优势
1. ✅ 异步实现，性能更好
2. ✅ 现代化的async/await语法
3. ✅ 更好的并发处理能力
4. ✅ 与现有架构更匹配

## 📝 结论

VabHub的115网盘实现已经非常接近MoviePilot，主要差异在于：
1. **延迟获取机制**：MoviePilot使用智能重试，VabHub使用固定延迟
2. **递归复制**：MoviePilot支持，VabHub未实现
3. **下载取消**：MoviePilot支持，VabHub未实现

建议优先实现智能延迟获取机制，这样可以提升文件操作的可靠性。

---

**状态**: ✅ 分析完成  
**最后更新**: 2025-01-XX

