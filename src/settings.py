from pydantic_settings import BaseSettings, SettingsConfigDict


class PGSettings(BaseSettings):
    PG_HOST: str
    PG_USER: str
    PG_PASSWORD: str
    PG_PORT: int
    PG_DB: str

    @property
    def pg_conn_string(self) -> str:
        return (
            f"postgresql://:@?dsn=postgresql://:@{self.PG_HOST}/"
            f"{self.PG_DB}&port={self.PG_PORT}&user={self.PG_USER}&password={self.PG_PASSWORD}"
        )

    @property
    def async_pg_conn_string(self) -> str:
        return (
            f"postgresql+asyncpg://:@{self.PG_HOST}/"
            f"{self.PG_DB}?port={self.PG_PORT}&user={self.PG_USER}&password={self.PG_PASSWORD}"
        )


class EKassaSettings(BaseSettings):
    EKASSA_BASE_URL: str
    EKASSA_LOGIN: str
    EKASSA_PASSWORD: str
    EKASSA_PAYMENT_CODE: int
    EKASSA_GROUP_CODE: int
    EKASSA_CALLBACK_URL: str


class UKassaSettings(BaseSettings):
    UKASSA_BASE_URL: str
    UKASSA_SHOP_ID: str
    UKASSA_API_KEY: str


class AuthSettings(BaseSettings):
    CREATE_TOKEN_URI: str
    VERIFY_TOKEN_URI: str


class RedisSettings(BaseSettings):
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_PASSWORD: str
    REDIS_DB: int

    @property
    def redis_conn_string(self) -> str:
        return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"


class AdminSettings(BaseSettings):
    ADMIN_USER_MODEL: str
    ADMIN_USER_MODEL_USERNAME_FIELD: str
    ADMIN_SECRET_KEY: str
    ADMIN_USERNAME: str = 'admin'
    ADMIN_PASSSWORD: str = 'admin'


class CompanySettings(BaseSettings):
    COMPANY_EMAIL: str
    COMPANY_INN: str
    COMPANY_WEBSITE_URL: str


class BackendSettings(BaseSettings):
    BACKEND_UNLOCK_CANDIDATE_URL: str
    BACKEND_API_KEY: str


class Settings(
    PGSettings,
    EKassaSettings,
    AuthSettings,
    # RedisSettings,
    AdminSettings,
    CompanySettings,
    UKassaSettings,
    BackendSettings
):
    PAYMENT_MONITORING_INTERVAL_SEC: int = 3
    PAYING_TIME_LIMIT_SEC: int = 15*60
    model_config = SettingsConfigDict(
        extra="allow",
    )


settings = Settings()
print(settings)
