"""
Netflix Top 10 数据提供者
"""

import io
import aiohttp
import pandas as pd
from typing import Dict, List, Any, Optional
from loguru import logger


class NetflixTop10Provider:
    """Netflix Top 10 数据提供者"""
    
    def __init__(self):
        self.name = "netflix_top10"
        self.description = "Netflix Top 10 排行榜数据"
        self.base_url = "https://www.netflix.com/tudum/top10/data/all-weeks-global.xlsx"
    
    async def fetch_data(
        self,
        region: str = "global",
        week: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """获取Netflix Top 10数据"""
        try:
            # 下载Excel文件
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, timeout=60) as response:
                    if response.status != 200:
                        logger.error(f"下载Netflix Top 10数据失败: HTTP {response.status}")
                        return []
                    
                    # 读取Excel数据
                    excel_data = await response.read()
                    # 使用openpyxl引擎读取Excel文件
                    try:
                        df = pd.read_excel(io.BytesIO(excel_data), engine='openpyxl')
                    except Exception:
                        # 如果没有openpyxl，尝试使用xlrd
                        try:
                            df = pd.read_excel(io.BytesIO(excel_data), engine='xlrd')
                        except Exception:
                            logger.error("无法读取Excel文件，请安装openpyxl或xlrd")
                            return []
                    
                    # 解析数据
                    return self._parse_excel_data(df, region, week, limit)
                    
        except Exception as e:
            logger.error(f"获取Netflix Top 10数据失败: {e}")
            return []
    
    def _parse_excel_data(
        self,
        df: pd.DataFrame,
        region: str,
        week: Optional[str],
        limit: int
    ) -> List[Dict[str, Any]]:
        """解析Excel数据"""
        results = []
        
        try:
            # 如果指定了周数，过滤该周的数据
            if week:
                if 'week' in df.columns:
                    df_filtered = df[df['week'] == week]
                else:
                    logger.warning("Excel文件中没有week列，使用全部数据")
                    df_filtered = df
            else:
                # 获取最新一周的数据
                if 'week' in df.columns:
                    latest_week = df['week'].max()
                    df_filtered = df[df['week'] == latest_week]
                    week = str(latest_week)
                else:
                    logger.warning("Excel文件中没有week列，使用全部数据")
                    df_filtered = df
                    week = "latest"
            
            # 按排名排序
            if 'rank' in df_filtered.columns:
                df_filtered = df_filtered.sort_values('rank')
            elif 'weekly_rank' in df_filtered.columns:
                df_filtered = df_filtered.sort_values('weekly_rank')
            
            # 限制数量
            df_filtered = df_filtered.head(limit)
            
            # 解析每一行
            for _, row in df_filtered.iterrows():
                # 获取标题（可能是show_title或movie_title）
                title = row.get('show_title') or row.get('movie_title') or row.get('title', '')
                
                # 获取类型
                content_type = row.get('category', '')
                if not content_type:
                    # 根据列名判断
                    if 'show_title' in row and pd.notna(row['show_title']):
                        content_type = 'TV Show'
                    elif 'movie_title' in row and pd.notna(row['movie_title']):
                        content_type = 'Movie'
                
                # 获取排名
                rank = int(row.get('rank', row.get('weekly_rank', 0)))
                
                # 获取观看时长
                weekly_hours_viewed = int(row.get('weekly_hours_viewed', 0))
                
                # 获取累计周数
                cumulative_weeks = int(row.get('cumulative_weeks_in_top_10', 0))
                
                result = {
                    "rank": rank,
                    "id": f"netflix_{region}_{week}_{rank}",
                    "title": title,
                    "type": "tv" if "TV" in content_type or "Show" in content_type else "movie",
                    "content_type": content_type,
                    "region": region,
                    "week": week,
                    "popularity": weekly_hours_viewed,  # 使用观看时长作为热度指标
                    "weekly_hours_viewed": weekly_hours_viewed,
                    "cumulative_weeks_in_top_10": cumulative_weeks,
                    "source": "netflix_top10",
                    "poster_url": None,  # Netflix不提供海报URL
                    "external_url": f"https://www.netflix.com/search?q={title.replace(' ', '%20')}"
                }
                results.append(result)
            
        except Exception as e:
            logger.error(f"解析Netflix Top 10数据失败: {e}")
        
        return results
    
    async def get_available_weeks(self) -> List[str]:
        """获取可用的周数列表"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, timeout=60) as response:
                    if response.status != 200:
                        return []
                    
                    excel_data = await response.read()
                    df = pd.read_excel(io.BytesIO(excel_data))
                    
                    if 'week' in df.columns:
                        weeks = df['week'].unique().tolist()
                        weeks.sort(reverse=True)  # 最新的在前
                        return [str(w) for w in weeks]
                    else:
                        return []
                        
        except Exception as e:
            logger.error(f"获取Netflix Top 10周数列表失败: {e}")
            return []

