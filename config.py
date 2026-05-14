import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URI', 'mysql+pymysql://admin:CleanStream475%23@98.86.106.226/cleanstream_db?charset=utf8mb4')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
