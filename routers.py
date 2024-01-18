# routers.py
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session
import models
from database import SessionLocal
import hashlib
import xmltodict
import xml.etree.ElementTree as ET
import random
import string
import logging
from models import BillingInfo
from datetime import datetime, timedelta
import httpx
import json

router = APIRouter()

logger = logging.getLogger("uvicorn.error")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/api/v1/billing/register")
async def do_billing_register(request: Request, db: Session = Depends(get_db)):
    content_type = request.headers.get("Content-Type")
    if content_type == "application/xml":
        body = await request.body()
        data = xmltodict.parse(body)

        # Request data
        corp_id = data["REQUEST"]["HDINFO"]["CORPID"]
        password = data["REQUEST"]["HDINFO"]["PASSWORD"]
        password = encrypt_password(password)

        res_sdiv = data["REQUEST"]["DATA_INFO"]["RES_SDIV"]
        torihiki_detail = data["REQUEST"]["DATA_INFO"]["TORIHIKI_DETAIL"]
        torihiki_amount = data["REQUEST"]["DATA_INFO"]["TORIHIKI_AMOUNT"]
        payment_date = data["REQUEST"]["DATA_INFO"]["PAYMENT_DATE"]
        barcode_inf = data["REQUEST"]["DATA_INFO"]["BARCODE_INF"]
        free_col = data["REQUEST"]["DATA_INFO"]["FREE_COL"]
        link_url = data["REQUEST"]["DATA_INFO"]["LINK_URL"]
        sms_type = data["REQUEST"]["DATA_INFO"]["SMS_TYPE"]
        sms_retype = data["REQUEST"]["DATA_INFO"]["SMS_RETYPE"]
        sms_phone_num = data["REQUEST"]["DATA_INFO"]["SMS_PHONE_NUM"]
        get_user_num = data["REQUEST"]["DATA_INFO"]["GET_USER_NUM"]
        sms_msg = data["REQUEST"]["DATA_INFO"]["SMS_MSG"]

        request_data = BillingInfo(
            type="REQUEST",
            res_tcode="",
            res_scode="",
            res_sdiv=res_sdiv,
            inquiry_no="",
            torihiki_detail=torihiki_detail,
            torihiki_amount=torihiki_amount,
            payment_date=payment_date,
            barcode_inf=barcode_inf,
            free_col=free_col,
            link_url=link_url,
            sms_type=sms_type,
            sms_retype=sms_retype,
            sms_phone_num=sms_phone_num,
            get_user_num=get_user_num,
            sms_msg=sms_msg,
        )

        db.add(request_data)
        db.commit()

        # get the user from the database if it exists
        user = (
            db.query(models.User)
            .filter(models.User.corp_id == corp_id, models.User.password == password)
            .first()
        )
        if user is None:
            res_tcode = "2:00000"
            response_xml = ET.Element("REQUEST")
            hd_info = ET.SubElement(response_xml, "HD_INFO")
            res_tcode = ET.SubElement(hd_info, "RES_TCODE")
            res_tcode.text = "2:00000"

            result_data = BillingInfo(
                type="RESULT",
                res_tcode=res_tcode.text,
                res_scode="",
                res_sdiv="",
                inquiry_no="",
                torihiki_detail="",
                torihiki_amount=None,
                payment_date="",
                barcode_inf="",
                free_col="",
                link_url="",
                sms_type="",
                sms_retype="",
                sms_phone_num="",
                get_user_num="",
                sms_msg="",
            )

            db.add(result_data)
            db.commit()

            response_str = ET.tostring(
                response_xml, encoding="utf-8", method="xml", xml_declaration=True
            )

            return Response(
                content=response_str, media_type="application/xml", status_code=200
            )

        res_scodes = []

        if res_sdiv != "C":
            res_scodes.append("3:1001")
            logger.info("res_sdiv is not C")

        if torihiki_detail is None:
            res_scodes.append("3:1003")
        elif len(torihiki_detail) > 30:
            res_scodes.append("3:3003")
            logger.info("torihiki_detail is None or len(torihiki_detail) > 30")

        if torihiki_amount is None:
            res_scodes.append("3:1004")
            logger.info("torihiki_amount is None")
        else:
            torihiki_amount = int(torihiki_amount)
            if not 1 <= torihiki_amount <= 300000:
                res_scodes.append("3:3004")
                logger.info("torihiki_amount is not in range")

        if payment_date is None:
            res_scodes.append("3:1005")
            logger.info("payment_date is None")
        else:
            try:
                payment_date = datetime.strptime(payment_date, "%Y%m%d")
                today = datetime.today()
                limit = today + timedelta(days=59)
                if payment_date.date() > limit.date():
                    res_scodes.append("3:4005")
                    logger.info("payment_date is not 59 days from today")
            except ValueError:
                res_scodes.append("3:4005")
                logger.info("payment_date is not in correct format")

        if free_col != None and len(free_col) > 100:
            res_scodes.append("3:3007")
            logger.info("free_col is not None and len(free_col) > 100")

        if (
            link_url != None
            and link_url.startswith("https://") == False
            and link_url.startswith("http://") == False
        ):
            res_scodes.append("3:4008")
            logger.info(
                "link_url is not None and link_url.startswith('https://') == False or link_url.startswith('http://') == False"
            )

        response_xml = ET.Element("RESULT")
        hd_info = ET.SubElement(response_xml, "HD_INFO")
        res_tcode = ET.SubElement(hd_info, "RES_TCODE")
        res_tcode.text = "0:00000"

        # Create DATA_INFO element and its subelements
        data_info = ET.SubElement(response_xml, "DATA_INFO")

        ET.SubElement(data_info, "RES_SDIV").text = res_sdiv

        random_number = random.randint(10000000000, 99999999999)
        random_number_str = str(random_number)
        ET.SubElement(data_info, "INQUIRY_NO").text = random_number_str

        ET.SubElement(data_info, "TORIHIKI_DETAIL").text = torihiki_detail
        ET.SubElement(data_info, "TORIHIKI_AMOUNT").text = str(torihiki_amount)
        if isinstance(payment_date, datetime):
            payment_date = payment_date.strftime("%Y%m%d")
        ET.SubElement(data_info, "PAYMENT_DATE").text = payment_date
        ET.SubElement(data_info, "BARCODE_INF").text = barcode_inf
        ET.SubElement(data_info, "FREE_COL").text = free_col
        ET.SubElement(data_info, "LINK_URL").text = link_url
        ET.SubElement(data_info, "SMS_TYPE").text = sms_type
        ET.SubElement(data_info, "SMS_RETYPE").text = sms_retype
        ET.SubElement(data_info, "SMS_PHONE_NUM").text = sms_phone_num
        ET.SubElement(data_info, "GET_USER_NUM").text = get_user_num
        ET.SubElement(data_info, "SMS_MSG").text = sms_msg

        if len(res_scodes) > 0:
            ET.SubElement(data_info, "RES_SCODE").text = res_scodes[0]
            ET.SubElement(data_info, "BARCODE_URL").text = ""

            result_data = BillingInfo(
                type="RESULT",
                res_tcode=res_tcode.text,
                res_scode=",".join(res_scodes),
                res_sdiv=res_sdiv,
                inquiry_no="",
                torihiki_detail=torihiki_detail,
                torihiki_amount=torihiki_amount,
                payment_date=payment_date,
                barcode_inf=barcode_inf,
                free_col=free_col,
                link_url=link_url,
                sms_type=sms_type,
                sms_retype=sms_retype,
                sms_phone_num=sms_phone_num,
                get_user_num=get_user_num,
                sms_msg=sms_msg,
                barcode_url="",
            )

            db.add(result_data)
            db.commit()

            response_str = ET.tostring(
                response_xml, encoding="utf-8", method="xml", xml_declaration=True
            )
            return Response(
                content=response_str, media_type="application/xml", status_code=200
            )
        else:
            res_scodes.append("0:0000")
            ET.SubElement(data_info, "RES_SCODE").text = res_scodes[0]
        # Generate a unique random path
        path = "".join(random.choices(string.ascii_letters + string.digits, k=10))
        # Combine the domain with the random path
        random_url = f"https://mypayment-paymentgateway.tdkhoa.dev/p/{path}"
        ET.SubElement(data_info, "BARCODE_URL").text = random_url

        result_data = BillingInfo(
            type="RESULT",
            res_tcode=res_tcode.text,
            res_scode=",".join(res_scodes),
            res_sdiv=res_sdiv,
            inquiry_no=random_number_str,
            torihiki_detail=torihiki_detail,
            torihiki_amount=torihiki_amount,
            payment_date=payment_date,
            barcode_inf=barcode_inf,
            free_col=free_col,
            link_url=link_url,
            sms_type=sms_type,
            sms_retype=sms_retype,
            sms_phone_num=sms_phone_num,
            get_user_num=get_user_num,
            sms_msg=sms_msg,
            barcode_url=random_url,
        )

        db.add(result_data)
        db.commit()

        response_str = ET.tostring(
            response_xml, encoding="utf-8", method="xml", xml_declaration=True
        )

        return Response(content=response_str, media_type="application/xml")
    else:
        raise HTTPException(
            status_code=400, detail=f"Content type {content_type} not supported"
        )


@router.get("/api/v1/billing/info/{key}")
async def get_billing_info(key: str, db: Session = Depends(get_db)):
    billing_info = db.query(BillingInfo).filter(BillingInfo.barcode_url.endswith(key)).first()

    if not billing_info:
        raise HTTPException(status_code=404, detail="Billing info not found")
    return billing_info


@router.post("/api/v1/purchase")
async def do_purchase(request: Request, db: Session = Depends(get_db)):
    body = await request.body()
    data = json.loads(body.decode('utf-8'))

    request_xml = ET.Element("RESULT")
    data_info = ET.SubElement(request_xml, "DATA_INFO")
    ET.SubElement(data_info, "PAYSTS").text = "10"
    ET.SubElement(data_info, "INQNO").text = str(data["inquiry_no"])
    ET.SubElement(data_info, "BARCODE").text = ""
    ET.SubElement(data_info, "FREECMNT").text = ""
    ET.SubElement(data_info, "PAIDMNY").text = "333333333"
    ET.SubElement(data_info, "RCPDATE").text = data["rcpdate"]
    ET.SubElement(data_info, "CVSCODE").text = data["cvscode"]
    ET.SubElement(data_info, "CVSNAME").text = data["cvsname"]
    ET.SubElement(data_info, "STOCODE").text = data["stocode"]
    ET.SubElement(data_info, "KTDATE").text = ""
    ET.SubElement(data_info, "SPSDATE").text = ""

    request_xml_string = ET.tostring(request_xml)

    headers = {
        "Content-Type": "application/xml"
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post('http://fonfunsms-admin/api/v1/breaking-news-notification', data=request_xml_string, headers=headers)
    except httpx.ConnectError:
        raise HTTPException(status_code=400, detail={"message": "Error communicating with fonfunSMS"})
    if response.status_code != 200:
        raise HTTPException(status_code=400, detail={"message": "Error communicating with fonfunSMS"})

    response_xml = ET.fromstring(response.content)

    return {"message": "Purchase successful"}

def encrypt_password(password: str) -> str:
    # Use MD5 algorithm to encrypt the password
    encrypted_password = hashlib.md5(password.encode()).hexdigest()
    return encrypted_password
