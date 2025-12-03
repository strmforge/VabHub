"""
漫画导入 Schema
"""
from typing import List, Literal, Optional
from pydantic import BaseModel


class MangaImportOptions(BaseModel):
    """漫画导入选项"""
    mode: Literal["ALL", "LATEST_N", "SELECTED"] = "ALL"
    latest_n: Optional[int] = None  # 当 mode=LATEST_N 时使用
    chapter_ids: Optional[List[str]] = None  # 当 mode=SELECTED 时使用

