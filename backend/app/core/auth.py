"""
认证模块
提供用户认证相关功能
"""

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


async def get_current_user(
    db: AsyncSession,
    user_id: int = 1  # 简化实现，默认用户ID为1
) -> User:
    """获取当前用户（简化实现）"""
    try:
        # 这里简化实现，实际应该从token中获取用户信息
        user = await User.get_by_id(db, user_id)
        if not user:
            # 如果用户不存在，创建默认用户
            user = User(
                id=user_id,
                username="test_user",
                email="test@example.com",
                is_active=True
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
        
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无法获取用户信息"
        )