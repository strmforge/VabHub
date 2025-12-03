from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "vabhub-mesh-scheduler"
    APP_ENV: str = "production"

    # Railway/Supabase/Neon 提供的 Postgres 连接串
    DB_URL: str = "postgresql+asyncpg://user:password@host:5432/vabhub_mesh"

    # 简单共享密钥（用于 worker 与调度中心之间的认证）
    NETWORK_SHARED_KEY: str = "CHANGE_ME_TO_A_RANDOM_SECRET"

    MAX_WORKERS_PER_SITE: int = 3
    LEASE_DURATION_SECONDS: int = 300

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

