from pydantic_settings import BaseSettings
from pydantic import AnyUrl, AnyHttpUrl, Field
from dotenv import load_dotenv
load_dotenv() 

class Settings(BaseSettings):
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    DATABASE_URL: AnyUrl

    FRONTEND_URL: str
    GOOGLE_APPLICATION_CREDENTIALS: str
    class Config:
        env_file = ".env"

settings = Settings()
