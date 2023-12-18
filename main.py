from typing import Union
import aiomysql
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import Response
import xml.etree.ElementTree as ET
import logging
import asyncio
import hashlib
import xmltodict
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

app = FastAPI()
logger = logging.getLogger("uvicorn.error")


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}


async def get_pool():
    pool = await aiomysql.create_pool(
        host="mysql57",
        port=3306,
        user="root",
        password="Secret@12345",
        db="mypayment_mocking_api",
        loop=asyncio.get_event_loop(),
    )
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            yield cur
    pool.close()
    await pool.wait_closed()


@app.post("/api/payment-info")
async def payment_info(request: Request, cur=Depends(get_pool)):
    content_type = request.headers.get("Content-Type")
    if content_type == "application/xml":
        body = await request.body()
        data = xmltodict.parse(body)

        corp_id = data["REQUEST"]["HDINFO"]["CORPID"]
        password = data["REQUEST"]["HDINFO"]["PASSWORD"]
        password = encrypt_password(password)
        await cur.execute(
            "SELECT * FROM users WHERE corp_id = %s AND password = %s",
            (corp_id, password),
        )
        result = await cur.fetchone()
        if result is None:
            response_xml = ET.Element("REQUEST")
            hd_info = ET.SubElement(response_xml, "HD_INFO")
            res_tcode = ET.SubElement(hd_info, "RES_TCODE")
            res_tcode.text = "2:00000"
            response_str = ET.tostring(response_xml, encoding="utf-8", method="xml", xml_declaration=True)
            return Response(
                content=response_str, media_type="application/xml", status_code=400
            )

        validation_status = True

        res_sdiv = data["REQUEST"]["DATA_INFO"]["RES_SDIV"]
        if res_sdiv != "C":
            validation_status = False

        inquiry_no = data["REQUEST"]["DATA_INFO"]["INQUIRY_NO"]
        if inquiry_no != None:
            validation_status = False

        # <TORIHIKI_DETAIL>TORIHIKI_DETAILありがとうございます。</TORIHIKI_DETAIL>
        torihiki_detail = data["REQUEST"]["DATA_INFO"]["TORIHIKI_DETAIL"]
        if len(torihiki_detail) > 30:
            validation_status = False

        # <TORIHIKI_AMOUNT>20000</TORIHIKI_AMOUNT>
        torihiki_amount = int(data["REQUEST"]["DATA_INFO"]["TORIHIKI_AMOUNT"])
        if not 1 <= torihiki_amount <= 300000:
            validation_status = False

        # <PAYMENT_DATE>20180331</PAYMENT_DATE>
        try:
            payment_date = data["REQUEST"]["DATA_INFO"]["PAYMENT_DATE"]
            payment_date = datetime.strptime(payment_date, "%Y%m%d")
        except ValueError:
            validation_status = False
        today = datetime.today()
        limit = today + timedelta(days=59)
        if payment_date.date() != limit.date():
            validation_status = False

        # # <BARCODE_INF>91912345012345678901234567890117123100200001</BARCODE_INF>
        # barcode_inf = data["REQUEST"]["DATA_INFO"]["BARCODE_INF"]

        # # <FREE_COL>FREE_COLありがとうございます。</FREE_COL>
        # free_col = data["REQUEST"]["DATA_INFO"]["FREE_COL"]

        # <LINK_URL>https://xxx.xxx.co.jp/</LINK_URL>
        link_url = data["REQUEST"]["DATA_INFO"]["LINK_URL"]
        # link_url must start with http:// or https://
        if not link_url.startswith("http://") and not link_url.startswith("https://"):
            validation_status = False

        # <SMS_TYPE>3</SMS_TYPE>
        sms_type = data["REQUEST"]["DATA_INFO"]["SMS_TYPE"]
        if sms_type != "3":
            validation_status = False

        # <SMS_RETYPE/>
        sms_retype = data["REQUEST"]["DATA_INFO"]["SMS_RETYPE"]

        # <SMS_PHONE_NUM>090000000002</SMS_PHONE_NUM>
        sms_phone_num = data["REQUEST"]["DATA_INFO"]["SMS_PHONE_NUM"]
        # check sms_phone_num must start with 070, 080, 090
        if not sms_phone_num.startswith("070") and not sms_phone_num.startswith("080") and not sms_phone_num.startswith("090"):
            validation_status = False

        # <GET_USER_NUM>20170401</GET_USER_NUM>
        get_user_num = data["REQUEST"]["DATA_INFO"]["GET_USER_NUM"]

        # <SMS_TYPE>3</SMS_TYPE>
        sms_type = data["REQUEST"]["DATA_INFO"]["SMS_TYPE"]

        # <SMS_RETYPE/>
        sms_retype = data["REQUEST"]["DATA_INFO"]["SMS_RETYPE"]

        # <SMS_PHONE_NUM>090000000002</SMS_PHONE_NUM>
        sms_phone_num = data["REQUEST"]["DATA_INFO"]["SMS_PHONE_NUM"]

        # <GET_USER_NUM>20170401</GET_USER_NUM>
        get_user_num = data["REQUEST"]["DATA_INFO"]["GET_USER_NUM"]

        # <SMS_MSG>SMS_MSGありがとうございます。</SMS_MSG>
        sms_msg = data["REQUEST"]["DATA_INFO"]["SMS_MSG"]

        if validation_status is False:
            response_xml = ET.Element("REQUEST")
            hd_info = ET.SubElement(response_xml, "HD_INFO")
            res_tcode = ET.SubElement(hd_info, "RES_TCODE")
            res_tcode.text = "2:00000"
            response_str = ET.tostring(response_xml, encoding="utf-8", method="xml", xml_declaration=True)
            return Response(
                content=response_str, media_type="application/xml", status_code=400
            )

        response_xml = ET.Element("REQUEST")
        corp_id_element = ET.SubElement(response_xml, "CORPID")
        corp_id_element.text = corp_id
        password_element = ET.SubElement(response_xml, "PASSWORD")
        password_element.text = password
        res_sdiv_element = ET.SubElement(response_xml, "RES_SDIV")
        res_sdiv_element.text = res_sdiv
        response_str = ET.tostring(response_xml, encoding="utf-8", method="xml", xml_declaration=True)

        return Response(content=response_str, media_type="application/xml")
    else:
        raise HTTPException(
            status_code=400, detail=f"Content type {content_type} not supported"
        )


def encrypt_password(password: str) -> str:
    # Use MD5 algorithm to encrypt the password
    encrypted_password = hashlib.md5(password.encode()).hexdigest()
    return encrypted_password
