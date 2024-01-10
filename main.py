from fastapi import FastAPI
import logging
from sqlalchemy import create_engine
import models
import routers
from database import SessionLocal
from urllib.parse import quote_plus

username = "root"
password = quote_plus("Secret@12345")
hostname = "mysql57"
database_name = "mypayment_mocking_api"

SQLALCHEMY_DATABASE_URL = f"mysql://{username}:{password}@{hostname}/{database_name}?charset=utf8mb4"

engine = create_engine(SQLALCHEMY_DATABASE_URL)

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(routers.router)

logger = logging.getLogger("uvicorn.error")
