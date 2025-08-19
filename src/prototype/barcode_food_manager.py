import cv2  
from pyzbar import pyzbar  
from PIL import Image  
import numpy as np  
import pandas as pd  
import time  
import re  
import os  

try:  
    import easyocr  
    HAVE_EASYOCR = True  
except Exception:  
    HAVE_EASYOCR = False  

PRODUCT_DB_PATH = "product_db.csv"  
if not os.path.exists(PRODUCT_DB_PATH):  
    df_init = pd.DataFrame({  
        "code": ["0123456789012", "123456789012"],  
        "name": ["김치", "우유"],  
        "exp": ["2025-09-15", "2025-08-25"]  
    })  
    df_init.to_csv(PRODUCT_DB_PATH, index=False)  

def load_product_db(path):  
    return pd.read_csv(path)  

def query_product(db, code):  
    row = db.loc[db["code"] == code]  
    if not row.empty:  
        return {"code": code, "name": str(row.iloc[0]["name"]), "exp": str(row.iloc[0]["exp"])}  
    return None  

def extract_exp_from_text(text):  
    patterns = [  
        r'(\d{4}-\d{1,2}-\d{1,2})',  
        r'(\d{2}/\d{2}/\d{4})',  
        r'(\d{4}/\d{1,2}/\d{1,2})'  
    ]  
    for pat in patterns:  
        m = re.search(pat, text)  
        if m:  
            return m.group(1)  
    return None  

def decode_barcode(frame):  
    barcodes = pyzbar.decode(frame)  
    results = []  
    for b in barcodes:  
        data = b.data.decode('utf-8')  
        typ = b.type  
        results.append({"data": data, "type": typ, "rect": b.rect})  
    return results  

def main():  
    product_db = load_product_db(PRODUCT_DB_PATH)  

    reader = None  
    if HAVE_EASYOCR:  
        try:  
            reader = easyocr.Reader(['en','ko'], gpu=False)  
        except Exception as e:  
            print("EasyOCR 로드 실패:", e)  
            reader = None  

    cap = cv2.VideoCapture(0)  
    if not cap.isOpened():  
        print("카메라를 열 수 없습니다.")  
        return  

    seen = {}  
    READ_INTERVAL = 2.0  

    try:  
        while True:  
            ret, frame = cap.read()  
            if not ret:  
                print("프레임을 읽을 수 없습니다. 카메라 상태를 확인하세요.")  
                break  

            bars = decode_barcode(frame)  
            for b in bars:  
                code = b["data"]  
                now = time.time()  
                if code in seen and now - seen[code] < READ_INTERVAL:  
                    continue  
                seen[code] = now  

                info = query_product(product_db, code)  
                if info is None:  
                    info = {"code": code, "name": "Unknown", "exp": "N/A"}  

                if reader is not None:  
                    # OCR 보완 로직(선택적)  
                    pass  

                (x, y, w, h) = b["rect"]  
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)  
                text = f"{info['name']} | 유통기한: {