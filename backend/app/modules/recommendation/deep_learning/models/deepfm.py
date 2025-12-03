"""
深度因子分解机（DeepFM）模型
"""

from typing import List
from loguru import logger

try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning("PyTorch not available, DeepFM model will not work")


if TORCH_AVAILABLE:
    class DeepFactorizationMachine(nn.Module):
        """深度因子分解机模型"""
        
        def __init__(
            self, 
            num_users: int, 
            num_items: int, 
            embedding_dim: int = 64,
            hidden_dims: List[int] = None,
            dropout_rate: float = 0.2
        ):
            super().__init__()
            
            if hidden_dims is None:
                hidden_dims = [128, 64, 32]
            
            self.num_users = num_users
            self.num_items = num_items
            self.embedding_dim = embedding_dim
            
            # 嵌入层
            self.user_embedding = nn.Embedding(num_users, embedding_dim)
            self.item_embedding = nn.Embedding(num_items, embedding_dim)
            
            # 线性部分（偏置）
            self.user_bias = nn.Embedding(num_users, 1)
            self.item_bias = nn.Embedding(num_items, 1)
            self.global_bias = nn.Parameter(torch.zeros(1))
            
            # 深度部分
            layers = []
            input_dim = embedding_dim * 2
            
            for hidden_dim in hidden_dims:
                layers.append(nn.Linear(input_dim, hidden_dim))
                layers.append(nn.ReLU())
                layers.append(nn.Dropout(dropout_rate))
                input_dim = hidden_dim
            
            layers.append(nn.Linear(input_dim, 1))
            self.deep_layers = nn.Sequential(*layers)
            
            self._init_weights()
        
        def _init_weights(self):
            """初始化权重"""
            nn.init.normal_(self.user_embedding.weight, std=0.01)
            nn.init.normal_(self.item_embedding.weight, std=0.01)
            nn.init.constant_(self.user_bias.weight, 0)
            nn.init.constant_(self.item_bias.weight, 0)
        
        def forward(self, user_ids: torch.Tensor, item_ids: torch.Tensor) -> torch.Tensor:
            """前向传播"""
            # 嵌入向量
            user_emb = self.user_embedding(user_ids)
            item_emb = self.item_embedding(item_ids)
            
            # 线性部分
            user_bias = self.user_bias(user_ids).squeeze()
            item_bias = self.item_bias(item_ids).squeeze()
            linear_part = self.global_bias + user_bias + item_bias
            
            # FM交互部分
            fm_interaction = torch.sum(user_emb * item_emb, dim=-1)
            
            # 深度部分
            concat_emb = torch.cat([user_emb, item_emb], dim=-1)
            deep_part = self.deep_layers(concat_emb).squeeze()
            
            # 组合所有部分
            output = linear_part + fm_interaction + deep_part
            
            return output
else:
    # PyTorch不可用时的占位类
    class DeepFactorizationMachine:
        def __init__(self, *args, **kwargs):
            raise ImportError("PyTorch is not installed. Please install PyTorch to use DeepFM model.")

