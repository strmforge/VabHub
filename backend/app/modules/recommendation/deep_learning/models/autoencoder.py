"""
自编码器推荐模型
"""

from typing import List
from loguru import logger

try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning("PyTorch not available, AutoEncoder model will not work")


if TORCH_AVAILABLE:
    class AutoEncoder(nn.Module):
        """自编码器推荐模型"""
        
        def __init__(
            self, 
            num_items: int, 
            hidden_dims: List[int] = None,
            dropout_rate: float = 0.5
        ):
            super().__init__()
            
            if hidden_dims is None:
                hidden_dims = [128, 64, 32]
            
            self.num_items = num_items
            
            # 编码器
            encoder_layers = []
            input_dim = num_items
            
            for hidden_dim in hidden_dims:
                encoder_layers.append(nn.Linear(input_dim, hidden_dim))
                encoder_layers.append(nn.ReLU())
                encoder_layers.append(nn.Dropout(dropout_rate))
                input_dim = hidden_dim
            
            self.encoder = nn.Sequential(*encoder_layers)
            
            # 解码器
            decoder_layers = []
            for hidden_dim in reversed(hidden_dims[:-1]):
                decoder_layers.append(nn.Linear(input_dim, hidden_dim))
                decoder_layers.append(nn.ReLU())
                decoder_layers.append(nn.Dropout(dropout_rate))
                input_dim = hidden_dim
            
            decoder_layers.append(nn.Linear(input_dim, num_items))
            decoder_layers.append(nn.Sigmoid())  # 输出0-1之间的值
            
            self.decoder = nn.Sequential(*decoder_layers)
            
            self._init_weights()
        
        def _init_weights(self):
            """初始化权重"""
            for layer in self.encoder:
                if isinstance(layer, nn.Linear):
                    nn.init.xavier_uniform_(layer.weight)
                    nn.init.constant_(layer.bias, 0)
            
            for layer in self.decoder:
                if isinstance(layer, nn.Linear):
                    nn.init.xavier_uniform_(layer.weight)
                    nn.init.constant_(layer.bias, 0)
        
        def forward(self, x: torch.Tensor) -> torch.Tensor:
            """前向传播"""
            encoded = self.encoder(x)
            decoded = self.decoder(encoded)
            return decoded
        
        def encode(self, x: torch.Tensor) -> torch.Tensor:
            """编码（获取用户潜在表示）"""
            return self.encoder(x)
        
        def decode(self, encoded: torch.Tensor) -> torch.Tensor:
            """解码（重构用户-物品交互）"""
            return self.decoder(encoded)
else:
    # PyTorch不可用时的占位类
    class AutoEncoder:
        def __init__(self, *args, **kwargs):
            raise ImportError("PyTorch is not installed. Please install PyTorch to use AutoEncoder model.")

