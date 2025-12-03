"""
站点 AI 适配配置模型

定义 Cloudflare API 返回的配置结构和业务层使用的数据模型。
"""

from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from datetime import datetime


class AISearchConfig(BaseModel):
    """AI 生成的搜索配置"""
    url: str
    method: str = "GET"
    query_params: Dict[str, str] = {}
    form_data: Optional[Dict[str, str]] = None
    encoding: Optional[str] = "utf-8"
    headers: Optional[Dict[str, str]] = None


class AIDetailSelectors(BaseModel):
    """详情页选择器配置"""
    title: Optional[str] = None
    size: Optional[str] = None
    seeds: Optional[str] = None
    peers: Optional[str] = None
    download_link: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    upload_date: Optional[str] = None


class AIDetailConfig(BaseModel):
    """AI 生成的详情页配置"""
    url: Optional[str] = None
    selectors: AIDetailSelectors = AIDetailSelectors()
    encoding: Optional[str] = "utf-8"


class AIHRRule(BaseModel):
    """HR 规则定义"""
    pattern: str
    location: Optional[str] = None
    severity: str = "medium"  # low, medium, high


class AIHRConfig(BaseModel):
    """AI 生成的 HR 配置"""
    enabled: bool = False
    rules: List[AIHRRule] = []


class AIAuthSelectors(BaseModel):
    """认证表单选择器"""
    username: Optional[str] = None
    password: Optional[str] = None
    submit: Optional[str] = None
    captcha: Optional[str] = None


class AIAuthConfig(BaseModel):
    """AI 生成的认证配置"""
    login_url: Optional[str] = None
    login_method: Optional[str] = "POST"
    form_fields: Optional[Dict[str, str]] = None
    selectors: AIAuthSelectors = AIAuthSelectors()
    cookie_names: Optional[List[str]] = None
    challenge_detection: Optional[Dict[str, Any]] = None


class AISiteAdapterConfig(BaseModel):
    """完整的站点适配配置"""
    search: AISearchConfig
    detail: AIDetailConfig = AIDetailConfig()
    hr: AIHRConfig = AIHRConfig()
    auth: AIAuthConfig = AIAuthConfig()
    categories: Dict[str, Any] = {}
    metadata: Optional[Dict[str, Any]] = None
    # Phase AI-4: AI 配置可信度分数（可选，从数据库记录中读取）
    confidence_score: Optional[int] = None


class SiteAIAdapterResult(BaseModel):
    """站点 AI 适配分析结果"""
    site_id: str
    engine: str
    config: AISiteAdapterConfig
    raw_model_output: str
    created_at: datetime


# ================== Phase AI-2: 解析后的配置视图层 ==================

class ParsedAISiteSearchConfig(BaseModel):
    """解析后的搜索配置（用于下游模块）"""
    url: str
    method: str = "GET"
    query_params: Dict[str, str] = {}
    form_data: Optional[Dict[str, str]] = None
    encoding: str = "utf-8"
    headers: Optional[Dict[str, str]] = None
    
    def __init__(self, **data):
        super().__init__(**data)
        # 清理文本字段
        if self.url:
            self.url = self.url.strip()
        if self.encoding:
            self.encoding = self.encoding.strip().lower()


class ParsedAISiteDetailConfig(BaseModel):
    """解析后的详情页配置"""
    url: Optional[str] = None
    selectors: AIDetailSelectors = AIDetailSelectors()
    encoding: str = "utf-8"
    
    def __init__(self, **data):
        super().__init__(**data)
        if self.url:
            self.url = self.url.strip()
        if self.encoding:
            self.encoding = self.encoding.strip().lower()


class ParsedAISiteHRConfig(BaseModel):
    """解析后的 HR 配置"""
    enabled: bool = False
    rules: List[AIHRRule] = []
    page_path: Optional[str] = None  # HR 页面路径（从 search.url 或 detail.url 推断）
    
    def __init__(self, **data):
        super().__init__(**data)
        if self.page_path:
            self.page_path = self.page_path.strip()


class ParsedAISiteAuthConfig(BaseModel):
    """解析后的认证配置"""
    login_url: Optional[str] = None
    login_method: str = "POST"
    form_fields: Optional[Dict[str, str]] = None
    selectors: AIAuthSelectors = AIAuthSelectors()
    cookie_names: Optional[List[str]] = None
    
    def __init__(self, **data):
        super().__init__(**data)
        if self.login_url:
            self.login_url = self.login_url.strip()
        if self.login_method:
            self.login_method = self.login_method.strip().upper()


class ParsedAISiteCategoriesConfig(BaseModel):
    """解析后的分类配置"""
    mapping: Dict[str, Any] = {}  # 分类 ID -> 分类信息
    names: Dict[str, str] = {}  # 分类 ID -> 分类名称（中文）


class ParsedAISiteAdapterConfig(BaseModel):
    """解析后的完整站点适配配置（用于下游模块）"""
    site_id: str
    engine: str
    search: ParsedAISiteSearchConfig
    detail: ParsedAISiteDetailConfig = ParsedAISiteDetailConfig()
    hr: ParsedAISiteHRConfig = ParsedAISiteHRConfig()
    auth: ParsedAISiteAuthConfig = ParsedAISiteAuthConfig()
    categories: ParsedAISiteCategoriesConfig = ParsedAISiteCategoriesConfig()
    metadata: Optional[Dict[str, Any]] = None
    # Phase AI-4: AI 配置可信度分数
    confidence_score: Optional[int] = None
    
    @classmethod
    def from_ai_config(
        cls,
        site_id: str,
        engine: str,
        config: AISiteAdapterConfig,
    ) -> "ParsedAISiteAdapterConfig":
        """
        从 AISiteAdapterConfig 转换为 ParsedAISiteAdapterConfig
        
        Args:
            site_id: 站点 ID
            engine: 站点框架类型
            config: 原始 AI 配置
            
        Returns:
            解析后的配置对象
        """
        # 转换搜索配置
        search = ParsedAISiteSearchConfig(
            url=config.search.url,
            method=config.search.method,
            query_params=config.search.query_params or {},
            form_data=config.search.form_data,
            encoding=config.search.encoding or "utf-8",
            headers=config.search.headers,
        )
        
        # 转换详情配置
        detail = ParsedAISiteDetailConfig(
            url=config.detail.url,
            selectors=config.detail.selectors,
            encoding=config.detail.encoding or "utf-8",
        )
        
        # 转换 HR 配置
        # 尝试从 search.url 或 detail.url 推断 HR 页面路径
        hr_page_path = None
        if config.search.url:
            # 尝试从搜索 URL 推断（例如：torrents.php -> hr.php）
            if "torrents.php" in config.search.url:
                hr_page_path = "hr.php"
            elif "browse.php" in config.search.url:
                hr_page_path = "hr.php"
        
        hr = ParsedAISiteHRConfig(
            enabled=config.hr.enabled if config.hr else False,
            rules=config.hr.rules if config.hr else [],
            page_path=hr_page_path,
        )
        
        # 转换认证配置
        auth = ParsedAISiteAuthConfig(
            login_url=config.auth.login_url if config.auth else None,
            login_method=config.auth.login_method if config.auth else "POST",
            form_fields=config.auth.form_fields if config.auth else None,
            selectors=config.auth.selectors if config.auth else AIAuthSelectors(),
            cookie_names=config.auth.cookie_names if config.auth else None,
        )
        
        # 转换分类配置
        categories_data = config.categories or {}
        categories = ParsedAISiteCategoriesConfig(
            mapping=categories_data,
            names={k: str(v) for k, v in categories_data.items() if isinstance(v, (str, dict))},
        )
        
        return cls(
            site_id=site_id,
            engine=engine,
            search=search,
            detail=detail,
            hr=hr,
            auth=auth,
            categories=categories,
            metadata=config.metadata,
        )

