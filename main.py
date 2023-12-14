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
            response_str = ET.tostring(response_xml, encoding="utf-8", method="xml")
            return Response(
                content=response_str, media_type="application/xml", status_code=400
            )

        res_sdiv = data["REQUEST"]["DATA_INFO"]["RES_SDIV"]

        response_xml = ET.Element("REQUEST")
        corp_id_element = ET.SubElement(response_xml, "CORPID")
        corp_id_element.text = corp_id
        password_element = ET.SubElement(response_xml, "PASSWORD")
        password_element.text = password
        res_sdiv_element = ET.SubElement(response_xml, "RES_SDIV")
        res_sdiv_element.text = res_sdiv
        response_str = ET.tostring(response_xml, encoding="utf-8", method="xml")

        return Response(content=response_str, media_type="application/xml")
    else:
        raise HTTPException(
            status_code=400, detail=f"Content type {content_type} not supported"
        )


def encrypt_password(password: str) -> str:
    # Use MD5 algorithm to encrypt the password
    encrypted_password = hashlib.md5(password.encode()).hexdigest()
    return encrypted_password
