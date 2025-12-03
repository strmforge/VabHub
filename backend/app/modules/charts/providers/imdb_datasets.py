"""
IMDb Datasets 数据提供者
"""

import gzip
import io
import aiohttp
import pandas as pd
from typing import Dict, List, Any, Optional
from loguru import logger


class IMDBDatasetsProvider:
    """IMDb Datasets 数据提供者"""
    
    def __init__(self):
        self.name = "imdb_datasets"
        self.description = "IMDb 数据集排行榜数据"
        self.ratings_url = "https://datasets.imdbws.com/title.ratings.tsv.gz"
        self.basics_url = "https://datasets.imdbws.com/title.basics.tsv.gz"
    
    async def fetch_data(
        self,
        join_basics: bool = True,
        min_votes: int = 10000,
        top_n: int = 500,
        title_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """获取IMDb数据集数据"""
        try:
            # 下载评分数据
            async with aiohttp.ClientSession() as session:
                async with session.get(self.ratings_url, timeout=300) as response:
                    if response.status != 200:
                        logger.error(f"下载IMDb评分数据失败: HTTP {response.status}")
                        return []
                    
                    ratings_data = await response.read()
                    ratings_df = self._parse_tsv_gz(ratings_data)
                
                # 过滤最低投票数
                ratings_df = ratings_df[ratings_df['numVotes'] >= min_votes]
                
                if join_basics:
                    # 下载基本信息数据
                    async with session.get(self.basics_url, timeout=300) as response:
                        if response.status != 200:
                            logger.error(f"下载IMDb基本信息数据失败: HTTP {response.status}")
                            return []
                        
                        basics_data = await response.read()
                        basics_df = self._parse_tsv_gz(basics_data)
                    
                    # 合并数据
                    merged_df = pd.merge(ratings_df, basics_df, on='tconst', how='inner')
                    
                    # 过滤类型
                    if title_type:
                        merged_df = merged_df[merged_df['titleType'] == title_type]
                    else:
                        # 默认只显示电影
                        merged_df = merged_df[merged_df['titleType'] == 'movie']
                    
                    # 按评分和投票数排序
                    merged_df = merged_df.sort_values(
                        ['averageRating', 'numVotes'],
                        ascending=[False, False]
                    )
                    
                    return self._parse_imdb_data(merged_df.head(top_n))
                else:
                    # 仅使用评分数据
                    ratings_df = ratings_df.sort_values(
                        ['averageRating', 'numVotes'],
                        ascending=[False, False]
                    )
                    return self._parse_ratings_data(ratings_df.head(top_n))
                    
        except Exception as e:
            logger.error(f"获取IMDb数据失败: {e}")
            return []
    
    def _parse_tsv_gz(self, gz_data: bytes) -> pd.DataFrame:
        """解析gzip压缩的TSV数据"""
        try:
            # 解压数据
            decompressed = gzip.decompress(gz_data)
            
            # 使用pandas解析TSV
            # 使用low_memory=False以避免类型推断问题
            df = pd.read_csv(
                io.BytesIO(decompressed),
                sep='\t',
                low_memory=False,
                na_values=['\\N']  # IMDb使用\N表示空值
            )
            
            return df
        except Exception as e:
            logger.error(f"解析IMDb TSV数据失败: {e}")
            return pd.DataFrame()
    
    def _parse_imdb_data(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """解析IMDb完整数据"""
        results = []
        
        try:
            for i, (_, row) in enumerate(df.iterrows(), 1):
                # 获取年份
                year = None
                if 'startYear' in row and pd.notna(row['startYear']):
                    try:
                        year = int(row['startYear'])
                    except (ValueError, TypeError):
                        year = None
                
                # 获取类型
                title_type = row.get('titleType', 'movie')
                media_type = 'movie' if title_type == 'movie' else 'tv'
                
                # 获取类型列表
                genres = []
                if 'genres' in row and pd.notna(row['genres']):
                    genres = [g.strip() for g in str(row['genres']).split(',') if g.strip()]
                
                result = {
                    "rank": i,
                    "id": row.get('tconst', ''),
                    "title": row.get('primaryTitle', ''),
                    "original_title": row.get('originalTitle', ''),
                    "type": media_type,
                    "title_type": title_type,
                    "year": year,
                    "genres": genres,
                    "rating": float(row.get('averageRating', 0)),
                    "votes": int(row.get('numVotes', 0)),
                    "runtime_minutes": int(row.get('runtimeMinutes', 0)) if pd.notna(row.get('runtimeMinutes')) else None,
                    "source": "imdb_datasets",
                    "poster_url": None,  # IMDb数据集不包含海报URL
                    "external_url": f"https://www.imdb.com/title/{row.get('tconst', '')}"
                }
                results.append(result)
        except Exception as e:
            logger.error(f"解析IMDb数据失败: {e}")
        
        return results
    
    def _parse_ratings_data(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """解析仅评分数据"""
        results = []
        
        try:
            for i, (_, row) in enumerate(df.iterrows(), 1):
                result = {
                    "rank": i,
                    "id": row.get('tconst', ''),
                    "title": f"IMDb ID: {row.get('tconst', '')}",
                    "original_title": "",
                    "type": "movie",
                    "year": None,
                    "genres": [],
                    "rating": float(row.get('averageRating', 0)),
                    "votes": int(row.get('numVotes', 0)),
                    "runtime_minutes": None,
                    "source": "imdb_datasets",
                    "poster_url": None,
                    "external_url": f"https://www.imdb.com/title/{row.get('tconst', '')}"
                }
                results.append(result)
        except Exception as e:
            logger.error(f"解析IMDb评分数据失败: {e}")
        
        return results

