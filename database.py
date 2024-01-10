# database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from urllib.parse import quote_plus

username = "root"
password = quote_plus("Secret@12345")
hostname = "mysql57"
database_name = "mypayment_mocking_api"

SQLALCHEMY_DATABASE_URL = f"mysql://{username}:{password}@{hostname}/{database_name}?charset=utf8mb4"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)