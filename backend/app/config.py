import os

class Settings:
    PROJECT_NAME: str = "Connector Inventory API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    
    # MySQL Database connection
    DB_USER: str = os.getenv("DB_USER", "root")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    DB_HOST: str = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT: str = os.getenv("DB_PORT", "3306")
    DB_NAME: str = os.getenv("DB_NAME", "connector_inventory")
    
    @property
    def DATABASE_URL(self) -> str:
        # Handles empty password correctly
        if self.DB_PASSWORD:
            return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset=utf8mb4"
        return f"mysql+pymysql://{self.DB_USER}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset=utf8mb4"
    
    # JWT Auth
    JWT_SECRET: str = os.getenv("JWT_SECRET", "super-secret-connector-key-998877665544332211")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day

    # Email & SMTP Settings
    SMTP_ENABLED: bool = os.getenv("SMTP_ENABLED", "false").lower() in ("true", "1", "yes")
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM_EMAIL: str = os.getenv("SMTP_FROM_EMAIL", "noreply@connector-inventory.local")
    SMTP_FROM_NAME: str = os.getenv("SMTP_FROM_NAME", "Connector Inventory System")
    ADMIN_NOTIFICATION_EMAIL: str = os.getenv("ADMIN_NOTIFICATION_EMAIL", "admin@connector.local")

settings = Settings()
