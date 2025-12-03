"""
文件树管理器
实现文件树扫描、对比和更新
参考MoviePilot插件的文件树管理
利用115网盘开发者API实现实时文件对比
"""

from typing import Dict, List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.models.strm import STRMFileTree, STRMLifeEvent


class FileTreeManager:
    """文件树管理器"""
    
    def __init__(self, db: AsyncSession, cloud_115_api: Optional[Any] = None):
        self.db = db
        self.cloud_115_api = cloud_115_api
    
    async def scan_cloud_storage(
        self,
        cloud_storage: str,
        root_path: str = '/',
        file_type: Optional[int] = 4  # 4:视频
    ) -> Dict[str, Any]:
        """
        扫描云存储文件树
        
        Args:
            cloud_storage: 云存储类型（115/123）
            root_path: 根路径
            file_type: 文件类型（4:视频）
        
        Returns:
            文件树结构
        """
        logger.info(f"扫描云存储文件树: {cloud_storage} - {root_path}")
        
        if cloud_storage == '115' and self.cloud_115_api:
            # 使用115网盘API扫描文件树
            return await self._scan_115_storage(root_path, file_type)
        else:
            # 其他云存储或未配置API
            logger.warning(f"未配置{cloud_storage}的API客户端")
            return {}
    
    async def _scan_115_storage(
        self,
        root_path: str,
        file_type: Optional[int] = 4
    ) -> Dict[str, Any]:
        """扫描115网盘文件树"""
        try:
            # 获取目录信息
            dir_info = await self.cloud_115_api.get_file_info(path=root_path)
            
            if not dir_info:
                return {}
            
            # 构建文件树结构
            file_tree = {
                "file_id": dir_info.get("file_id"),
                "file_name": dir_info.get("file_name", root_path),
                "file_category": dir_info.get("file_category", "0"),
                "path": root_path,
                "size": dir_info.get("size"),
                "size_byte": dir_info.get("size_byte"),
                "count": dir_info.get("count"),
                "folder_count": dir_info.get("folder_count"),
                "children": []
            }
            
            # 如果指定了文件类型，使用搜索API获取文件列表
            if file_type:
                # 搜索该目录下的所有视频文件
                # 注意：115网盘搜索API可能需要目录ID
                # 暂时返回目录信息
                pass
            
            return file_tree
            
        except Exception as e:
            logger.error(f"扫描115网盘文件树失败: {e}")
            return {}
    
    async def compare_file_trees(
        self,
        cloud_storage: str,
        local_tree: Dict[str, Any],
        cloud_tree: Dict[str, Any]
    ) -> Dict[str, List[str]]:
        """
        对比本地和云存储文件树
        
        Args:
            cloud_storage: 云存储类型
            local_tree: 本地文件树
            cloud_tree: 云存储文件树
        
        Returns:
            差异结果：新增、更新、删除的文件列表
        """
        differences = {
            'added': [],
            'updated': [],
            'deleted': []
        }
        
        # 对比文件树
        local_files = self._flatten_tree(local_tree)
        cloud_files = self._flatten_tree(cloud_tree)
        
        local_file_map = {f['path']: f for f in local_files}
        cloud_file_map = {f['path']: f for f in cloud_files}
        
        # 找出新增和更新的文件
        for cloud_path, cloud_file in cloud_file_map.items():
            if cloud_path not in local_file_map:
                differences['added'].append(cloud_path)
            else:
                local_file = local_file_map[cloud_path]
                if cloud_file.get('sha1') != local_file.get('sha1'):
                    differences['updated'].append(cloud_path)
        
        # 找出删除的文件
        for local_path in local_file_map:
            if local_path not in cloud_file_map:
                differences['deleted'].append(local_path)
        
        return differences
    
    def _flatten_tree(self, tree: Dict[str, Any]) -> List[Dict[str, Any]]:
        """扁平化文件树"""
        files = []
        
        def traverse(node: Dict[str, Any], parent_path: str = ''):
            if node.get('type') == 'file':
                file_path = f"{parent_path}/{node['name']}" if parent_path else node['name']
                files.append({
                    'path': file_path,
                    'name': node['name'],
                    'size': node.get('size'),
                    'sha1': node.get('sha1'),
                    'mtime': node.get('mtime')
                })
            elif node.get('type') == 'folder':
                folder_path = f"{parent_path}/{node['name']}" if parent_path else node['name']
                for child in node.get('children', []):
                    traverse(child, folder_path)
        
        if isinstance(tree, dict):
            traverse(tree)
        elif isinstance(tree, list):
            for node in tree:
                traverse(node)
        
        return files

