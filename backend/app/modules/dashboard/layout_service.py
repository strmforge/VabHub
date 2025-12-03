"""
仪表盘布局服务
支持可拖拽布局的保存和加载
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, List, Optional, Any
from loguru import logger

from app.models.dashboard import DashboardLayout, DashboardWidget


class DashboardLayoutService:
    """仪表盘布局服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_layout(self, layout_id: Optional[int] = None, user_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        获取布局
        
        Args:
            layout_id: 布局ID（如果为None，返回默认布局）
            user_id: 用户ID（单用户系统可为None）
        
        Returns:
            布局配置
        """
        try:
            if layout_id:
                result = await self.db.execute(
                    select(DashboardLayout).where(DashboardLayout.id == layout_id)
                )
                layout = result.scalar_one_or_none()
            else:
                # 获取默认布局
                result = await self.db.execute(
                    select(DashboardLayout).where(
                        DashboardLayout.is_default == True
                    ).limit(1)
                )
                layout = result.scalar_one_or_none()
            
            if not layout:
                return None
            
            return {
                "id": layout.id,
                "name": layout.name,
                "description": layout.description,
                "breakpoint": layout.breakpoint,
                "cols": layout.cols,
                "row_height": layout.row_height,
                "margin": layout.margin or [10, 10],
                "layouts": layout.layouts or {},
                "widgets": layout.widgets or [],
                "is_default": layout.is_default,
                "created_at": layout.created_at.isoformat() if layout.created_at else None,
                "updated_at": layout.updated_at.isoformat() if layout.updated_at else None
            }
        except Exception as e:
            logger.error(f"Failed to get layout: {e}")
            return None
    
    async def save_layout(
        self,
        name: str,
        breakpoint: str,
        cols: int,
        row_height: int,
        margin: List[int],
        layouts: Dict[str, Any],
        widgets: List[str],
        layout_id: Optional[int] = None,
        user_id: Optional[int] = None,
        is_default: bool = False
    ) -> Optional[int]:
        """
        保存布局
        
        Args:
            name: 布局名称
            breakpoint: 布局断点
            cols: 网格列数
            row_height: 行高
            margin: 边距
            layouts: 布局配置
            widgets: 组件列表
            layout_id: 布局ID（如果提供，则更新现有布局）
            user_id: 用户ID
            is_default: 是否为默认布局
        
        Returns:
            布局ID
        """
        try:
            if layout_id:
                # 更新现有布局
                result = await self.db.execute(
                    select(DashboardLayout).where(DashboardLayout.id == layout_id)
                )
                layout = result.scalar_one_or_none()
                
                if not layout:
                    return None
                
                layout.name = name
                layout.breakpoint = breakpoint
                layout.cols = cols
                layout.row_height = row_height
                layout.margin = margin
                layout.layouts = layouts
                layout.widgets = widgets
                layout.is_default = is_default
            else:
                # 创建新布局
                # 如果设置为默认布局，先取消其他默认布局
                if is_default:
                    await self._clear_default_layouts()
                
                layout = DashboardLayout(
                    user_id=user_id,
                    name=name,
                    breakpoint=breakpoint,
                    cols=cols,
                    row_height=row_height,
                    margin=margin,
                    layouts=layouts,
                    widgets=widgets,
                    is_default=is_default
                )
                self.db.add(layout)
            
            await self.db.commit()
            await self.db.refresh(layout)
            
            return layout.id
        except Exception as e:
            logger.error(f"Failed to save layout: {e}")
            await self.db.rollback()
            return None
    
    async def _clear_default_layouts(self):
        """清除所有默认布局标记"""
        try:
            result = await self.db.execute(
                select(DashboardLayout).where(DashboardLayout.is_default == True)
            )
            layouts = result.scalars().all()
            
            for layout in layouts:
                layout.is_default = False
            
            await self.db.commit()
        except Exception as e:
            logger.error(f"Failed to clear default layouts: {e}")
            await self.db.rollback()
    
    async def delete_layout(self, layout_id: int) -> bool:
        """删除布局"""
        try:
            result = await self.db.execute(
                select(DashboardLayout).where(DashboardLayout.id == layout_id)
            )
            layout = result.scalar_one_or_none()
            
            if not layout:
                return False
            
            await self.db.delete(layout)
            await self.db.commit()
            
            return True
        except Exception as e:
            logger.error(f"Failed to delete layout: {e}")
            await self.db.rollback()
            return False
    
    async def list_layouts(self, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """列出所有布局"""
        try:
            result = await self.db.execute(select(DashboardLayout))
            layouts = result.scalars().all()
            
            return [
                {
                    "id": layout.id,
                    "name": layout.name,
                    "description": layout.description,
                    "breakpoint": layout.breakpoint,
                    "is_default": layout.is_default,
                    "created_at": layout.created_at.isoformat() if layout.created_at else None,
                    "updated_at": layout.updated_at.isoformat() if layout.updated_at else None
                }
                for layout in layouts
            ]
        except Exception as e:
            logger.error(f"Failed to list layouts: {e}")
            return []
    
    async def get_widget(self, widget_id: str) -> Optional[Dict[str, Any]]:
        """获取组件"""
        try:
            result = await self.db.execute(
                select(DashboardWidget).where(DashboardWidget.widget_id == widget_id)
            )
            widget = result.scalar_one_or_none()
            
            if not widget:
                return None
            
            return {
                "id": widget.id,
                "widget_id": widget.widget_id,
                "name": widget.name,
                "type": widget.type,
                "description": widget.description,
                "component": widget.component,
                "config": widget.config or {},
                "enabled": widget.enabled,
                "configurable": widget.configurable,
                "refresh_interval": widget.refresh_interval
            }
        except Exception as e:
            logger.error(f"Failed to get widget: {e}")
            return None
    
    async def list_widgets(self) -> List[Dict[str, Any]]:
        """列出所有组件"""
        try:
            result = await self.db.execute(select(DashboardWidget))
            widgets = result.scalars().all()
            
            return [
                {
                    "id": widget.id,
                    "widget_id": widget.widget_id,
                    "name": widget.name,
                    "type": widget.type,
                    "description": widget.description,
                    "component": widget.component,
                    "enabled": widget.enabled,
                    "configurable": widget.configurable,
                    "refresh_interval": widget.refresh_interval
                }
                for widget in widgets
            ]
        except Exception as e:
            logger.error(f"Failed to list widgets: {e}")
            return []

