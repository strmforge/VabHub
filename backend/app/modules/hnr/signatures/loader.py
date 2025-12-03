"""
HNR签名包加载器 - 支持YAML文件热更新
整合自acq-guardian项目
"""

import yaml
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from loguru import logger
from pydantic import BaseModel, Field, field_validator


class SignaturePattern(BaseModel):
    """签名模式"""
    text: List[str] = Field(default_factory=list, description="文本匹配模式")
    regex: List[str] = Field(default_factory=list, description="正则表达式模式")


class Signature(BaseModel):
    """签名定义"""
    id: str
    name: str
    category: str
    patterns: SignaturePattern
    confidence: float = 0.8
    penalties: Dict[str, Any] = Field(default_factory=dict)


class SignaturePack(BaseModel):
    """签名包"""
    version: int = 1
    signatures: List[Signature] = Field(default_factory=list)
    site_overrides: Dict[str, Dict[str, Any]] = Field(default_factory=dict)

    @field_validator("site_overrides", mode="before")
    @classmethod
    def _ensure_site_overrides(cls, value: Optional[Dict[str, Dict[str, Any]]]) -> Dict[str, Dict[str, Any]]:
        """允许 YAML 中 site_overrides 为 null"""
        return value or {}


class SignaturePackLoader:
    """签名包加载器"""
    
    def __init__(self, pack_path: Optional[str] = None):
        """
        初始化签名包加载器
        
        Args:
            pack_path: YAML签名包文件路径，如果为None则使用默认签名
        """
        self.pack_path = Path(pack_path) if pack_path else None
        self.pack: Optional[SignaturePack] = None
        self._compiled_regexes: Dict[str, List[re.Pattern]] = {}
        self.known_badges: set = set()
        
        if self.pack_path and self.pack_path.exists():
            self.load()
        else:
            # 使用默认签名
            self.pack = self._create_default_pack()
            self._compile_patterns()
    
    def _create_default_pack(self) -> SignaturePack:
        """创建默认签名包"""
        return SignaturePack(
            version=1,
            signatures=[
                Signature(
                    id="hnr_basic",
                    name="基本HNR检测",
                    category="HNR_BASIC",
                    patterns=SignaturePattern(
                        text=["H&R", "H-R", "H R", "hit and run", "hit&run", "Hit and Run"],
                        regex=[
                            r"\bH\s*[-/&]?\s*R\b",
                            r"\bhit\s*[-/&]?\s*run\b",
                            r"\bHNR\b"
                        ]
                    ),
                    confidence=0.9,
                    penalties={"base": -50, "per_level": -10}
                ),
                Signature(
                    id="h3_rule",
                    name="H3规则检测",
                    category="HNR_LEVEL",
                    patterns=SignaturePattern(
                        text=["H3", "H-3", "H 3"],
                        regex=[r"\bH\s*[-/]?\s*3\b"]
                    ),
                    confidence=0.8,
                    penalties={"base": -30, "per_level": -5}
                ),
                Signature(
                    id="h5_rule",
                    name="H5规则检测",
                    category="HNR_LEVEL",
                    patterns=SignaturePattern(
                        text=["H5", "H-5", "H 5"],
                        regex=[r"\bH\s*[-/]?\s*5\b"]
                    ),
                    confidence=0.8,
                    penalties={"base": -50, "per_level": -10}
                ),
                Signature(
                    id="h7_rule",
                    name="H7规则检测",
                    category="HNR_LEVEL",
                    patterns=SignaturePattern(
                        text=["H7", "H-7", "H 7"],
                        regex=[r"\bH\s*[-/]?\s*7\b"]
                    ),
                    confidence=0.85,
                    penalties={"base": -70, "per_level": -15}
                ),
            ],
            site_overrides={}
        )
    
    def load(self, pack_path: Optional[str] = None) -> bool:
        """
        加载YAML签名包
        
        Args:
            pack_path: 签名包文件路径，如果为None则使用初始化时的路径
        
        Returns:
            是否加载成功
        """
        try:
            if pack_path:
                self.pack_path = Path(pack_path)
            
            if not self.pack_path or not self.pack_path.exists():
                logger.warning(f"签名包文件不存在: {self.pack_path}")
                return False
            
            with open(self.pack_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            # 验证和转换数据
            self.pack = SignaturePack(**data)
            self._compile_patterns()
            
            logger.info(f"成功加载签名包 v{self.pack.version} ({len(self.pack.signatures)} 个签名)")
            return True
            
        except Exception as e:
            logger.error(f"加载签名包失败: {e}")
            # 如果加载失败，使用默认签名
            self.pack = self._create_default_pack()
            self._compile_patterns()
            return False
    
    def reload(self) -> bool:
        """重新加载签名包（热更新）"""
        if self.pack_path:
            return self.load()
        return False
    
    def _compile_patterns(self):
        """编译正则表达式模式以提高性能"""
        if not self.pack:
            return
        
        self._compiled_regexes = {}
        self.known_badges = set()
        
        # 编译所有正则表达式
        for sig in self.pack.signatures:
            category = sig.category
            if category not in self._compiled_regexes:
                self._compiled_regexes[category] = []
            
            for pattern in sig.patterns.regex:
                try:
                    compiled = re.compile(pattern, re.IGNORECASE)
                    self._compiled_regexes[category].append(compiled)
                except re.error as e:
                    logger.warning(f"编译正则表达式失败: {pattern} - {e}")
            
            # 收集已知标签文本
            for text in sig.patterns.text:
                self.known_badges.add(text.lower())
    
    def get_signatures(self) -> List[Signature]:
        """获取所有签名"""
        return self.pack.signatures if self.pack else []
    
    def get_signature(self, sig_id: str) -> Optional[Signature]:
        """获取指定ID的签名"""
        if not self.pack:
            return None
        for sig in self.pack.signatures:
            if sig.id == sig_id:
                return sig
        return None
    
    def get_site_overrides(self, site_id: str) -> Dict[str, Any]:
        """
        获取站点特定规则覆盖
        
        Args:
            site_id: 站点ID或站点名称
        
        Returns:
            站点特定规则配置
        """
        if not self.pack:
            return {}
        return self.pack.site_overrides.get(site_id, {})
    
    def get_site_selectors(self, site_id: str) -> List[str]:
        """
        获取站点CSS选择器
        
        Args:
            site_id: 站点ID或站点名称
        
        Returns:
            CSS选择器列表
        """
        site_overrides = self.get_site_overrides(site_id)
        return site_overrides.get("selectors", [])
    
    def match_patterns(self, text: str, category: Optional[str] = None) -> List[Signature]:
        """
        匹配文本中的签名模式
        
        Args:
            text: 要匹配的文本
            category: 签名类别，如果为None则匹配所有类别
        
        Returns:
            匹配到的签名列表
        """
        if not self.pack:
            return []
        
        matched = []
        text_lower = text.lower()
        
        for sig in self.pack.signatures:
            if category and sig.category != category:
                continue
            
            # 文本匹配
            for pattern_text in sig.patterns.text:
                if pattern_text.lower() in text_lower:
                    matched.append(sig)
                    break
            
            # 正则表达式匹配
            if sig.category in self._compiled_regexes:
                for compiled_regex in self._compiled_regexes[sig.category]:
                    if compiled_regex.search(text):
                        matched.append(sig)
                        break
        
        return matched
    
    def is_known_badge(self, text: str) -> bool:
        """检查文本是否为已知标签"""
        return text.lower() in self.known_badges

