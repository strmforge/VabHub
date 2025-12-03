"""
深度学习模型训练器
"""

import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from loguru import logger
import pandas as pd
import numpy as np

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import Dataset, DataLoader
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning("PyTorch not available, deep learning trainer will not work")

from app.modules.recommendation.deep_learning.models import (
    NeuralCollaborativeFiltering,
    DeepFactorizationMachine,
    AutoEncoder
)
from app.modules.recommendation.deep_learning.gpu_utils import get_device, check_gpu_available


class InteractionDataset(Dataset):
    """用户-物品交互数据集"""
    
    def __init__(
        self, 
        interactions: pd.DataFrame, 
        user_to_idx: Dict[str, int], 
        item_to_idx: Dict[str, int]
    ):
        self.interactions = interactions
        self.user_to_idx = user_to_idx
        self.item_to_idx = item_to_idx
        
        # 准备训练数据
        self.user_ids = []
        self.item_ids = []
        self.ratings = []
        
        for _, row in interactions.iterrows():
            user_id = str(row['user_id'])
            item_id = str(row['item_id'])
            rating = float(row.get('rating', 1.0))
            
            if user_id in user_to_idx and item_id in item_to_idx:
                self.user_ids.append(user_to_idx[user_id])
                self.item_ids.append(item_to_idx[item_id])
                self.ratings.append(rating)
    
    def __len__(self):
        return len(self.user_ids)
    
    def __getitem__(self, idx):
        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch is not installed")
        
        return {
            'user_id': torch.tensor(self.user_ids[idx], dtype=torch.long),
            'item_id': torch.tensor(self.item_ids[idx], dtype=torch.long),
            'rating': torch.tensor(self.ratings[idx], dtype=torch.float32)
        }


class DeepLearningTrainer:
    """深度学习模型训练器"""
    
    def __init__(
        self,
        model_type: str = "ncf",
        embedding_dim: int = 64,
        hidden_dims: List[int] = None,
        dropout_rate: float = 0.2,
        learning_rate: float = 0.001,
        batch_size: int = 256,
        epochs: int = 100,
        early_stopping_patience: int = 10,
        enable_gpu: bool = True,
        device_id: Optional[int] = None
    ):
        """
        初始化训练器
        
        Args:
            model_type: 模型类型（ncf, deepfm, autoencoder）
            embedding_dim: 嵌入维度
            hidden_dims: 隐藏层维度
            dropout_rate: Dropout比率
            learning_rate: 学习率
            batch_size: 批次大小
            epochs: 训练轮数
            early_stopping_patience: 早停耐心值
            enable_gpu: 是否启用GPU（配置开关）
            device_id: GPU设备ID
        """
        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch is not installed. Please install PyTorch to use deep learning features.")
        
        self.model_type = model_type
        self.embedding_dim = embedding_dim
        self.hidden_dims = hidden_dims or [128, 64, 32]
        self.dropout_rate = dropout_rate
        self.learning_rate = learning_rate
        self.batch_size = batch_size
        self.epochs = epochs
        self.early_stopping_patience = early_stopping_patience
        
        # GPU配置
        self.enable_gpu = enable_gpu
        self.device_id = device_id
        self.device = get_device(enable_gpu, device_id)
        
        # 模型和映射
        self.model = None
        self.user_to_idx = {}
        self.item_to_idx = {}
        self.idx_to_user = {}
        self.idx_to_item = {}
        
        # 训练状态
        self.is_trained = False
        self.last_training_time = None
        self.training_history = []
    
    def create_model(self, num_users: int, num_items: int):
        """创建模型"""
        if self.model_type == "ncf":
            self.model = NeuralCollaborativeFiltering(
                num_users=num_users,
                num_items=num_items,
                embedding_dim=self.embedding_dim,
                hidden_dims=self.hidden_dims,
                dropout_rate=self.dropout_rate
            )
        elif self.model_type == "deepfm":
            self.model = DeepFactorizationMachine(
                num_users=num_users,
                num_items=num_items,
                embedding_dim=self.embedding_dim,
                hidden_dims=self.hidden_dims,
                dropout_rate=self.dropout_rate
            )
        elif self.model_type == "autoencoder":
            self.model = AutoEncoder(
                num_items=num_items,
                hidden_dims=self.hidden_dims,
                dropout_rate=self.dropout_rate
            )
        else:
            raise ValueError(f"Unknown model type: {self.model_type}")
        
        self.model = self.model.to(self.device)
        logger.info(
            f"Created {self.model_type} model on {self.device} with "
            f"{sum(p.numel() for p in self.model.parameters())} parameters"
        )
    
    def create_mappings(self, interactions: pd.DataFrame):
        """创建用户和物品的索引映射"""
        unique_users = interactions['user_id'].unique()
        unique_items = interactions['item_id'].unique()
        
        self.user_to_idx = {str(user): idx for idx, user in enumerate(unique_users)}
        self.item_to_idx = {str(item): idx for idx, item in enumerate(unique_items)}
        self.idx_to_user = {idx: user for user, idx in self.user_to_idx.items()}
        self.idx_to_item = {idx: item for item, idx in self.item_to_idx.items()}
        
        logger.info(f"Created mappings: {len(self.user_to_idx)} users, {len(self.item_to_idx)} items")
    
    async def train(
        self, 
        interactions: pd.DataFrame,
        validation_data: Optional[pd.DataFrame] = None
    ):
        """训练模型"""
        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch is not installed")
        
        try:
            logger.info(f"Starting training {self.model_type} model...")
            
            # 创建映射
            self.create_mappings(interactions)
            
            # 创建模型
            num_users = len(self.user_to_idx)
            num_items = len(self.item_to_idx)
            self.create_model(num_users, num_items)
            
            # 准备数据
            dataset = InteractionDataset(interactions, self.user_to_idx, self.item_to_idx)
            dataloader = DataLoader(
                dataset, 
                batch_size=self.batch_size, 
                shuffle=True,
                num_workers=0  # 避免多进程问题
            )
            
            # 准备验证数据
            val_dataloader = None
            if validation_data is not None and len(validation_data) > 0:
                val_dataset = InteractionDataset(
                    validation_data, 
                    self.user_to_idx, 
                    self.item_to_idx
                )
                val_dataloader = DataLoader(
                    val_dataset,
                    batch_size=self.batch_size,
                    shuffle=False,
                    num_workers=0
                )
            
            # 训练模型
            await self._train_model(dataloader, val_dataloader)
            
            self.is_trained = True
            self.last_training_time = datetime.now()
            
            logger.info(
                f"Training completed. Model: {self.model_type}, "
                f"Users: {num_users}, Items: {num_items}, "
                f"Device: {self.device}"
            )
            
        except Exception as e:
            logger.error(f"Training failed: {e}")
            raise
    
    async def _train_model(
        self, 
        dataloader: DataLoader,
        val_dataloader: Optional[DataLoader] = None
    ):
        """训练模型核心逻辑"""
        optimizer = optim.Adam(self.model.parameters(), lr=self.learning_rate)
        criterion = nn.MSELoss()
        
        best_loss = float('inf')
        patience_counter = 0
        
        for epoch in range(self.epochs):
            # 训练阶段
            self.model.train()
            total_loss = 0.0
            num_batches = 0
            
            for batch in dataloader:
                user_ids = batch['user_id'].to(self.device)
                item_ids = batch['item_id'].to(self.device)
                ratings = batch['rating'].to(self.device)
                
                optimizer.zero_grad()
                
                if self.model_type == "autoencoder":
                    # 自编码器需要不同的输入格式
                    # 这里简化处理，需要构建用户-物品矩阵
                    logger.warning("Autoencoder training not fully implemented, skipping batch")
                    continue
                else:
                    predictions = self.model(user_ids, item_ids)
                    loss = criterion(predictions, ratings)
                
                loss.backward()
                optimizer.step()
                
                total_loss += loss.item()
                num_batches += 1
            
            avg_loss = total_loss / num_batches if num_batches > 0 else 0.0
            
            # 验证阶段
            val_loss = None
            if val_dataloader is not None:
                self.model.eval()
                val_total_loss = 0.0
                val_num_batches = 0
                
                with torch.no_grad():
                    for batch in val_dataloader:
                        user_ids = batch['user_id'].to(self.device)
                        item_ids = batch['item_id'].to(self.device)
                        ratings = batch['rating'].to(self.device)
                        
                        if self.model_type != "autoencoder":
                            predictions = self.model(user_ids, item_ids)
                            loss = criterion(predictions, ratings)
                            val_total_loss += loss.item()
                            val_num_batches += 1
                
                val_loss = val_total_loss / val_num_batches if val_num_batches > 0 else None
            
            # 记录训练历史
            history_entry = {
                "epoch": epoch,
                "train_loss": avg_loss,
                "val_loss": val_loss
            }
            self.training_history.append(history_entry)
            
            # 早停检查
            current_loss = val_loss if val_loss is not None else avg_loss
            if current_loss < best_loss:
                best_loss = current_loss
                patience_counter = 0
            else:
                patience_counter += 1
            
            # 日志输出
            if epoch % 10 == 0 or epoch == self.epochs - 1:
                log_msg = f"Epoch {epoch}, Train Loss: {avg_loss:.4f}"
                if val_loss is not None:
                    log_msg += f", Val Loss: {val_loss:.4f}"
                logger.info(log_msg)
            
            # 早停
            if patience_counter >= self.early_stopping_patience:
                logger.info(f"Early stopping at epoch {epoch}")
                break
            
            # 让出控制权，避免阻塞
            await asyncio.sleep(0)
    
    def save_model(self, filepath: str):
        """保存模型"""
        if self.model is None:
            raise ValueError("Model is not trained yet")
        
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'model_type': self.model_type,
            'user_to_idx': self.user_to_idx,
            'item_to_idx': self.item_to_idx,
            'idx_to_user': self.idx_to_user,
            'idx_to_item': self.idx_to_item,
            'embedding_dim': self.embedding_dim,
            'hidden_dims': self.hidden_dims,
            'dropout_rate': self.dropout_rate,
            'training_history': self.training_history,
            'last_training_time': self.last_training_time.isoformat() if self.last_training_time else None
        }, filepath)
        
        logger.info(f"Model saved to {filepath}")
    
    def load_model(self, filepath: str):
        """加载模型"""
        checkpoint = torch.load(filepath, map_location=self.device)
        
        self.model_type = checkpoint['model_type']
        self.user_to_idx = checkpoint['user_to_idx']
        self.item_to_idx = checkpoint['item_to_idx']
        self.idx_to_user = checkpoint['idx_to_user']
        self.idx_to_item = checkpoint['idx_to_item']
        self.embedding_dim = checkpoint['embedding_dim']
        self.hidden_dims = checkpoint['hidden_dims']
        self.dropout_rate = checkpoint['dropout_rate']
        self.training_history = checkpoint.get('training_history', [])
        
        if checkpoint.get('last_training_time'):
            self.last_training_time = datetime.fromisoformat(checkpoint['last_training_time'])
        
        # 创建模型
        num_users = len(self.user_to_idx)
        num_items = len(self.item_to_idx)
        self.create_model(num_users, num_items)
        
        # 加载权重
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.model.eval()
        
        self.is_trained = True
        logger.info(f"Model loaded from {filepath}")
    
    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        info = {
            "model_type": self.model_type,
            "is_trained": self.is_trained,
            "device": self.device,
            "gpu_enabled": self.enable_gpu,
            "gpu_available": check_gpu_available(self.enable_gpu),
            "last_training_time": self.last_training_time.isoformat() if self.last_training_time else None,
            "user_count": len(self.user_to_idx),
            "item_count": len(self.item_to_idx),
            "embedding_dim": self.embedding_dim,
            "hidden_dims": self.hidden_dims,
            "dropout_rate": self.dropout_rate,
            "training_history_length": len(self.training_history)
        }
        
        if self.model is not None:
            info.update({
                "total_parameters": sum(p.numel() for p in self.model.parameters()),
                "trainable_parameters": sum(p.numel() for p in self.model.parameters() if p.requires_grad)
            })
        
        return info

