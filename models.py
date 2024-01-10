from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    corp_id = Column(String(255), unique=True, index=True)
    password = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

class BillingInfo(Base):
    __tablename__ = "billing_info"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(255))
    res_tcode = Column(String(255))
    res_scode = Column(String(255))
    res_sdiv = Column(String(255))
    inquiry_no = Column(String(255))
    torihiki_detail = Column(String(255))
    torihiki_amount = Column(Integer)
    payment_date = Column(String(255))
    barcode_inf = Column(String(255))
    free_col = Column(String(255))
    link_url = Column(String(255))
    sms_type = Column(String(255))
    sms_retype = Column(String(255))
    sms_phone_num = Column(String(255))
    get_user_num = Column(String(255))
    sms_msg = Column(String(255))
    barcode_url = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
