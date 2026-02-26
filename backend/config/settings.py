# config.py
import os
from dotenv import load_dotenv

load_dotenv()  # Load .env

class Config:
    DB_HOSTNAME = os.getenv('DB_HOSTNAME')
    DB_PORT = int(os.getenv('DB_PORT', 3306))
    DB_USERNAME = os.getenv('DB_USERNAME')
    DB_PASSWORD = os.getenv('DB_PASSWORD')
    DB_DATNAME = os.getenv('DB_DATNAME')