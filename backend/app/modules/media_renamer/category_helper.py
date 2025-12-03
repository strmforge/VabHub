"""
媒体分类助手
基于YAML配置文件的分类策略，支持电影、电视剧和音乐的二级分类
基于YAML配置文件的分类策略
"""

import shutil
from pathlib import Path
from typing import Union, Optional, Dict, Any, Mapping, TYPE_CHECKING
from loguru import logger

if TYPE_CHECKING:
    from app.modules.media_renamer.classifier import MediaCategory

try:
    import ruamel.yaml
    from ruamel.yaml import CommentedMap
    RUAMEL_YAML_AVAILABLE = True
except ImportError:
    RUAMEL_YAML_AVAILABLE = False
    # 定义CommentedMap为dict的别名，以便类型注解
    CommentedMap = dict
    logger.warning("ruamel.yaml库未安装，无法使用YAML分类配置。请运行: pip install ruamel.yaml")


class CategoryHelper:
    """
    二级分类助手
    基于YAML配置文件进行分类
    """

    def __init__(self, config_path: Optional[Path] = None):
        """
        初始化分类助手
        
        Args:
            config_path: 配置文件路径（可选，默认使用config/category.yaml）
        """
        if config_path is None:
            # 默认配置文件路径
            base_dir = Path(__file__).parent.parent.parent.parent
            config_path = base_dir / "config" / "category.yaml"
        
        self._category_path: Path = config_path
        self._categorys = {}
        self._movie_categorys = {}
        self._tv_categorys = {}
        self._music_categorys = {}
        self._ebook_categorys = {}
        self._audiobook_categorys = {}
        self._comic_categorys = {}
        self.init()

    def init(self):
        """
        初始化，加载配置文件
        """
        if not RUAMEL_YAML_AVAILABLE:
            logger.warning("ruamel.yaml未安装，分类功能将使用默认配置")
            return
        
        try:
            # 如果配置文件不存在，创建默认配置
            if not self._category_path.exists():
                self._create_default_config()
            
            with open(self._category_path, mode='r', encoding='utf-8') as f:
                try:
                    yaml = ruamel.yaml.YAML()
                    self._categorys = yaml.load(f) or {}
                except Exception as e:
                    logger.error(f"二级分类策略配置文件格式出现严重错误！请检查：{str(e)}")
                    self._categorys = {}
        except Exception as err:
            logger.error(f"二级分类策略配置文件加载出错：{str(err)}")
            self._categorys = {}

        if self._categorys:
            self._movie_categorys = self._categorys.get('movie', {})
            self._tv_categorys = self._categorys.get('tv', {})
            self._music_categorys = self._categorys.get('music', {})
            self._ebook_categorys = self._categorys.get('ebook', {})
            self._audiobook_categorys = self._categorys.get('audiobook', {})
            self._comic_categorys = self._categorys.get('comic', {})
        
        logger.info(f"已加载二级分类策略: {self._category_path}")
        logger.debug(f"电影分类: {list(self._movie_categorys.keys())}")
        logger.debug(f"电视剧分类: {list(self._tv_categorys.keys())}")
        logger.debug(f"音乐分类: {list(self._music_categorys.keys())}")
        logger.debug(f"电子书分类: {list(self._ebook_categorys.keys())}")
        logger.debug(f"有声书分类: {list(self._audiobook_categorys.keys())}")
        logger.debug(f"漫画分类: {list(self._comic_categorys.keys())}")

    def _create_default_config(self):
        """创建默认配置文件"""
        try:
            # 确保目录存在
            self._category_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 默认配置内容
            default_config = """####### 配置说明 #######
# 1. 该配置文件用于配置电影和电视剧的分类策略，配置后程序会按照配置的分类策略名称进行分类，配置文件采用yaml格式，需要严格附合语法规则
# 2. 配置文件中的一级分类名称：`movie`、`tv`、`music` 为固定名称不可修改，二级名称同时也是目录名称，会按先后顺序匹配，匹配后程序会按这个名称建立二级目录
# 3. 支持的分类条件：
#   `original_language` 语种，具体含义参考下方字典
#   `production_countries` 国家或地区（电影）、`origin_country` 国家或地区（电视剧），具体含义参考下方字典
#   `genre_ids` 内容类型，具体含义参考下方字典
#   `release_year` 发行年份，格式：YYYY，电影实际对应`release_date`字段，电视剧实际对应`first_air_date`字段，支持范围设定，如：`YYYY-YYYY`
#   themoviedb 详情API返回的其它一级字段
# 4. 配置多项条件时需要同时满足，一个条件需要匹配多个值是使用`,`分隔
# 5. !条件值表示排除该值

# 配置电影的分类策略
movie:
  # 分类名同时也是目录名
  动画电影:
    # 匹配 genre_ids 内容类型，16是动漫
    genre_ids: '16'
  华语电影:
    # 匹配语种
    original_language: 'zh,cn,bo,za'
  # 未匹配以上条件时，分类为外语电影
  外语电影:

# 配置电视剧的分类策略
tv:
  # 分类名同时也是目录名
  国漫:
    # 匹配 genre_ids 内容类型，16是动漫
    genre_ids: '16'
    # 匹配 origin_country 国家，CN是中国大陆，TW是中国台湾，HK是中国香港
    origin_country: 'CN,TW,HK'
  日番:
    # 匹配 genre_ids 内容类型，16是动漫
    genre_ids: '16'
    # 匹配 origin_country 国家，JP是日本
    origin_country: 'JP'
  纪录片:
     # 匹配 genre_ids 内容类型，99是纪录片
    genre_ids: '99'
  儿童:
    # 匹配 genre_ids 内容类型，10762是儿童
    genre_ids: '10762'
  综艺:
    # 匹配 genre_ids 内容类型，10764 10767都是综艺
    genre_ids: '10764,10767'
  国产剧:
    # 匹配 origin_country 国家，CN是中国大陆，TW是中国台湾，HK是中国香港
    origin_country: 'CN,TW,HK'
  欧美剧:
    # 匹配 origin_country 国家，主要欧美国家列表
    origin_country: 'US,FR,GB,DE,ES,IT,NL,PT,RU,UK'
  日韩剧:
    # 匹配 origin_country 国家，主要亚洲国家列表
    origin_country: 'JP,KP,KR,TH,IN,SG'
  # 未匹配以上分类，则命名为未分类
  未分类:

# 配置音乐的分类策略（可选）
music:
  # 分类名同时也是目录名
  华语音乐:
    # 匹配语种（音乐通常没有original_language，这里使用artist或album信息）
    # 注意：音乐分类可能需要根据实际数据源调整
    original_language: 'zh,cn'
  欧美音乐:
    original_language: 'en'
  日韩音乐:
    original_language: 'ja,ko'
  # 未匹配以上分类，则命名为其他音乐
  其他音乐:
"""
            
            with open(self._category_path, 'w', encoding='utf-8') as f:
                f.write(default_config)
            
            logger.info(f"已创建默认分类配置文件: {self._category_path}")
        except Exception as e:
            logger.error(f"创建默认分类配置文件失败: {e}")

    @property
    def is_movie_category(self) -> bool:
        """获取电影分类标志"""
        return bool(self._movie_categorys)

    @property
    def is_tv_category(self) -> bool:
        """获取电视剧分类标志"""
        return bool(self._tv_categorys)

    @property
    def is_music_category(self) -> bool:
        """获取音乐分类标志"""
        return bool(self._music_categorys)

    @property
    def movie_categorys(self) -> list:
        """获取电影分类清单"""
        return list(self._movie_categorys.keys()) if self._movie_categorys else []

    @property
    def tv_categorys(self) -> list:
        """获取电视剧分类清单"""
        return list(self._tv_categorys.keys()) if self._tv_categorys else []

    @property
    def music_categorys(self) -> list:
        """获取音乐分类清单"""
        return list(self._music_categorys.keys()) if self._music_categorys else []

    def get_movie_category(self, tmdb_info: Dict[str, Any]) -> str:
        """
        判断电影的分类
        
        Args:
            tmdb_info: TMDB信息字典
            
        Returns:
            二级分类的名称
        """
        return self.get_category(self._movie_categorys, tmdb_info)

    def get_tv_category(self, tmdb_info: Dict[str, Any]) -> str:
        """
        判断电视剧的分类
        
        Args:
            tmdb_info: TMDB信息字典
            
        Returns:
            二级分类的名称
        """
        return self.get_category(self._tv_categorys, tmdb_info)

    def get_music_category(self, music_info: Dict[str, Any]) -> str:
        """
        判断音乐的分类
        
        Args:
            music_info: 音乐信息字典（可能包含artist、album、genre等信息）
            
        Returns:
            二级分类的名称
        """
        return self.get_category(self._music_categorys, music_info)
    
    def get_ebook_category(self, ebook: Mapping[str, Any]) -> Optional["MediaCategory"]:
        """
        判断电子书的分类
        
        Args:
            ebook: 电子书信息字典，包含：
                - tags: 标签列表（字符串列表或逗号分隔字符串）
                - language: 语言代码（如 "zh-CN", "en" 等）
                - extra_metadata: 额外元数据（可选）
        
        Returns:
            MediaCategory 对象，包含 category="电子书" 和 subcategory（如 "科幻"），如果未匹配则返回 None
        """
        if not self._ebook_categorys:
            return None
        
        # 构建匹配用的信息字典
        match_info: Dict[str, Any] = {}
        
        # 处理 tags
        tags = ebook.get("tags") or []
        if isinstance(tags, str):
            # 如果是字符串，尝试解析（可能是 JSON 或逗号分隔）
            try:
                import json
                tags = json.loads(tags)
            except:
                tags = [t.strip() for t in tags.split(",") if t.strip()]
        if isinstance(tags, list):
            match_info["tags"] = tags
        
        # 处理 language
        language = ebook.get("language")
        if language:
            match_info["language"] = language
        
        # 从 extra_metadata 中提取信息
        extra_metadata = ebook.get("extra_metadata") or {}
        if isinstance(extra_metadata, dict):
            if "tags" in extra_metadata and not match_info.get("tags"):
                tags_extra = extra_metadata["tags"]
                if isinstance(tags_extra, list):
                    match_info["tags"] = tags_extra
                elif isinstance(tags_extra, str):
                    match_info["tags"] = [t.strip() for t in tags_extra.split(",") if t.strip()]
            if "language" in extra_metadata and not match_info.get("language"):
                match_info["language"] = extra_metadata["language"]
        
        # 使用自定义的匹配逻辑（支持 tags 的"至少包含一个"匹配）
        subcategory = self._get_category_with_tags(self._ebook_categorys, match_info)
        if subcategory:
            # 延迟导入以避免循环依赖
            from app.modules.media_renamer.classifier import MediaCategory
            return MediaCategory(
                category="电子书",
                subcategory=subcategory,
                tags=match_info.get("tags", []) if isinstance(match_info.get("tags"), list) else []
            )
        return None
    
    def get_audiobook_category(self, audiobook: Mapping[str, Any]) -> Optional["MediaCategory"]:
        """
        判断有声书的分类
        
        Args:
            audiobook: 有声书信息字典，包含：
                - tags: 标签列表
                - language: 语言代码
                - duration_seconds: 时长（秒，可选）
                - extra_metadata: 额外元数据（可选）
        
        Returns:
            MediaCategory 对象，包含 category="有声书" 和 subcategory（如 "科幻有声"），如果未匹配则返回 None
        """
        if not self._audiobook_categorys:
            return None
        
        # 构建匹配用的信息字典（与电子书类似）
        match_info: Dict[str, Any] = {}
        
        # 处理 tags
        tags = audiobook.get("tags") or []
        if isinstance(tags, str):
            try:
                import json
                tags = json.loads(tags)
            except:
                tags = [t.strip() for t in tags.split(",") if t.strip()]
        if isinstance(tags, list):
            match_info["tags"] = tags
        
        # 处理 language
        language = audiobook.get("language")
        if language:
            match_info["language"] = language
        
        # 从 extra_metadata 中提取信息
        extra_metadata = audiobook.get("extra_metadata") or {}
        if isinstance(extra_metadata, dict):
            if "tags" in extra_metadata and not match_info.get("tags"):
                tags_extra = extra_metadata["tags"]
                if isinstance(tags_extra, list):
                    match_info["tags"] = tags_extra
                elif isinstance(tags_extra, str):
                    match_info["tags"] = [t.strip() for t in tags_extra.split(",") if t.strip()]
            if "language" in extra_metadata and not match_info.get("language"):
                match_info["language"] = extra_metadata["language"]
        
        # 使用自定义的匹配逻辑
        subcategory = self._get_category_with_tags(self._audiobook_categorys, match_info)
        if subcategory:
            # 延迟导入以避免循环依赖
            from app.modules.media_renamer.classifier import MediaCategory
            return MediaCategory(
                category="有声书",
                subcategory=subcategory,
                tags=match_info.get("tags", []) if isinstance(match_info.get("tags"), list) else []
            )
        return None
    
    def get_comic_category(self, comic: Mapping[str, Any]) -> Optional["MediaCategory"]:
        """
        判断漫画的分类
        
        Args:
            comic: 漫画信息字典，包含：
                - region: 地区代码（如 "CN", "JP", "US" 等）
                - language: 语言代码
                - extra_metadata: 额外元数据（可选，可能包含 region）
        
        Returns:
            MediaCategory 对象，包含 category="漫画" 和 subcategory（如 "日漫"），如果未匹配则返回 None
        """
        if not self._comic_categorys:
            return None
        
        # 构建匹配用的信息字典
        match_info: Dict[str, Any] = {}
        
        # 处理 region
        region = comic.get("region")
        if not region:
            # 尝试从 extra_metadata 中获取
            extra_metadata = comic.get("extra_metadata") or {}
            if isinstance(extra_metadata, dict):
                region = extra_metadata.get("region")
        if region:
            match_info["region"] = str(region).upper()
        
        # 处理 language
        language = comic.get("language")
        if not language:
            extra_metadata = comic.get("extra_metadata") or {}
            if isinstance(extra_metadata, dict):
                language = extra_metadata.get("language")
        if language:
            match_info["language"] = language
        
        # 使用标准的 get_category 方法（支持 region 和 language 匹配）
        subcategory = self.get_category(self._comic_categorys, match_info)
        if subcategory:
            # 延迟导入以避免循环依赖
            from app.modules.media_renamer.classifier import MediaCategory
            return MediaCategory(
                category="漫画",
                subcategory=subcategory,
                tags=[]
            )
        return None
    
    def _get_category_with_tags(self, categorys: Union[dict, CommentedMap], info: Dict[str, Any]) -> Optional[str]:
        """
        根据信息与分类配置文件进行比较，确定所属分类（支持 tags 的"至少包含一个"匹配）
        
        Args:
            categorys: 分类配置字典
            info: 媒体信息字典
        
        Returns:
            分类的名称，如果未匹配则返回 None
        """
        if not info:
            return None
        if not categorys:
            return None
        
        # 按顺序匹配分类规则
        for key, item in categorys.items():
            if not item:
                # 空规则是默认分类，直接返回
                return key
            
            match_flag = True
            
            # 检查每个条件
            for attr, value in item.items():
                if not value:
                    continue
                
                info_value = info.get(attr)
                if not info_value:
                    match_flag = False
                    continue
                
                # 特殊处理 tags 字段：支持"至少包含一个"匹配
                if attr == "tags":
                    if isinstance(info_value, list):
                        info_tags = [str(tag).lower() for tag in info_value]
                    elif isinstance(info_value, str):
                        info_tags = [info_value.lower()]
                    else:
                        match_flag = False
                        continue
                    
                    # 解析配置值（支持逗号分隔）
                    config_tags = [str(tag).strip().lower() for tag in str(value).split(",") if tag.strip()]
                    
                    # 检查是否有交集（至少包含一个）
                    if not set(config_tags).intersection(set(info_tags)):
                        match_flag = False
                else:
                    # 其他字段使用标准匹配逻辑
                    if isinstance(info_value, list):
                        info_values = [str(val).upper() for val in info_value]
                    else:
                        info_values = [str(info_value).upper()]
                    
                    # 解析配置值
                    config_values = [str(val).strip().upper() for val in str(value).split(",") if val.strip()]
                    
                    # 检查匹配
                    if not set(config_values).intersection(set(info_values)):
                        match_flag = False
            
            # 如果所有条件都匹配，返回此分类
            if match_flag:
                return key
        
        # 如果没有匹配到任何分类，返回 None
        return None

    @staticmethod
    def get_category(categorys: Union[dict, CommentedMap], info: dict) -> str:
        """
        根据信息与分类配置文件进行比较，确定所属分类
        
        Args:
            categorys: 分类配置字典
            info: 媒体信息字典（TMDB信息或音乐信息）
            
        Returns:
            分类的名称，如果未匹配则返回空字符串
        """
        if not info:
            return ""
        if not categorys:
            return ""

        # 按顺序匹配分类规则
        for key, item in categorys.items():
            if not item:
                # 空规则是默认分类，直接返回
                return key
            
            match_flag = True
            
            # 检查每个条件
            for attr, value in item.items():
                if not value:
                    continue
                
                # 处理release_year特殊字段
                if attr == "release_year":
                    # 发行年份
                    info_value = info.get("release_date") or info.get("first_air_date")
                    if info_value:
                        info_value = str(info_value)[:4]
                    else:
                        match_flag = False
                        continue
                else:
                    info_value = info.get(attr)
                
                if not info_value:
                    match_flag = False
                    continue
                
                # 处理production_countries特殊字段（电影）
                if attr == "production_countries":
                    # 制片国家（列表格式）
                    if isinstance(info_value, list):
                        info_values = [str(val.get("iso_3166_1", "")).upper() for val in info_value if isinstance(val, dict)]
                    else:
                        match_flag = False
                        continue
                else:
                    # 其他字段
                    if isinstance(info_value, list):
                        info_values = [str(val).upper() for val in info_value]
                    else:
                        info_values = [str(info_value).upper()]

                # 解析配置值（支持逗号分隔、范围、排除等）
                values = []
                invert_values = []

                # 如果有 "," 进行分割
                config_values = [str(val).strip() for val in str(value).split(",") if val.strip()]

                expanded_values = []
                for v in config_values:
                    if "-" not in v:
                        expanded_values.append(v)
                        continue

                    # - 表示范围
                    value_begin, value_end = v.split("-", 1)

                    prefix = ""
                    if value_begin.startswith('!'):
                        prefix = '!'
                        value_begin = value_begin[1:]

                    if value_begin.isdigit() and value_end.isdigit():
                        # 数字范围
                        expanded_values.extend(
                            f"{prefix}{val}" for val in range(int(value_begin), int(value_end) + 1)
                        )
                    else:
                        # 字符串范围（不支持，直接添加）
                        expanded_values.extend([f"{prefix}{value_begin}", f"{prefix}{value_end}"])

                # 转换为大写并分离正常值和排除值
                expanded_values = [str(val).upper() for val in expanded_values]
                invert_values = [val[1:] for val in expanded_values if val.startswith('!')]
                values = [val for val in expanded_values if not val.startswith('!')]

                # 检查匹配
                if values and not set(values).intersection(set(info_values)):
                    match_flag = False
                if invert_values and set(invert_values).intersection(set(info_values)):
                    match_flag = False
            
            # 如果所有条件都匹配，返回此分类
            if match_flag:
                return key
        
        # 如果没有匹配到任何分类，返回空字符串
        return ""

    def reload(self):
        """重新加载配置文件"""
        self.init()

