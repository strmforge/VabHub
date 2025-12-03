"""
神经协同过滤（NCF）模型
"""

from typing import List
from loguru import logger

try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning("PyTorch not available, NCF model will not work")


if TORCH_AVAILABLE:
    class NeuralCollaborativeFiltering(nn.Module):
        """神经协同过滤模型"""
        
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
            
            # 用户和物品嵌入层
            self.user_embedding = nn.Embedding(num_users, embedding_dim)
            self.item_embedding = nn.Embedding(num_items, embedding_dim)
            
            # MLP层
            layers = []
            input_dim = embedding_dim * 2
            
            for hidden_dim in hidden_dims:
                layers.append(nn.Linear(input_dim, hidden_dim))
                layers.append(nn.ReLU())
                layers.append(nn.Dropout(dropout_rate))
                input_dim = hidden_dim
            
            # 输出层
            layers.append(nn.Linear(input_dim, 1))
            
            self.mlp = nn.Sequential(*layers)
            
            # 初始化权重
            self._init_weights()
        
        def _init_weights(self):
            """初始化模型权重"""
            nn.init.normal_(self.user_embedding.weight, std=0.01)
            nn.init.normal_(self.item_embedding.weight, std=0.01)
            
            for layer in self.mlp:
                if isinstance(layer, nn.Linear):
                    nn.init.xavier_uniform_(layer.weight)
                    nn.init.constant_(layer.bias, 0)
        
        def forward(self, user_ids: torch.Tensor, item_ids: torch.Tensor) -> torch.Tensor:
            """前向传播"""
            # 获取嵌入向量
            user_emb = self.user_embedding(user_ids)
            item_emb = self.item_embedding(item_ids)
            
            # 拼接用户和物品嵌入
            concat_emb = torch.cat([user_emb, item_emb], dim=-1)
            
            # 通过MLP
            output = self.mlp(concat_emb)
            
            return output.squeeze()
else:
    # PyTorch不可用时的占位类
    class NeuralCollaborativeFiltering:
        def __init__(self, *args, **kwargs):
            raise ImportError("PyTorch is not installed. Please install PyTorch to use NCF model.")

