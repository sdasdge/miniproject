import cv2
from pyzbar import pyzbar
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import pandas as pd
import time
import re
import os
import sys # 프로그램 종료를 위해 추가

# EasyOCR 설치 여부 확인
try:
    import easyocr
    HAVE_EASYOCR = True
except ImportError:
    HAVE_EASYOCR = False

PRODUCT_DB_PATH = "product_db.csv"

# --- 이 부분이 수정되었습니다 ---
# DB 파일이 있는지 확인하고, 없으면 안내 후 종료
if not os.path.exists(PRODUCT_DB_PATH):
    print(f"🚨 오류: '{PRODUCT_DB_PATH}' 파일을 찾을 수 없습니다.")
    print("먼저 create_db.py를 실행하여 50개 샘플 데이터베이스를 생성해주세요.")
    sys.exit() # 프로그램 종료
# --- 여기까지 수정 ---


def load_product_db(path):
    # 바코드가 숫자로만 구성된 경우, 문자열로 불러와 앞의 0이 사라지지 않게 함
    return pd.read_csv(path, dtype={"code": str}, encoding='utf-8-sig')

def query_product(db, code):
    # 'code' 컬럼이 문자열 타입이라고 가정하고 비교
    row = db.loc[db["code"] == str(code)]
    if not row.empty:
        return {"code": code, "name": str(row.iloc[0]["name"]), "exp": str(row.iloc[0]["exp"])}
    return None

def extract_exp_from_text(text):
    patterns = [
        r'(\d{4}-\d{1,2}-\d{1,2})',
        r'(\d{2}/\d{2}/\d{4})',
        r'(\d{4}/\d{1,2}/\d{1,2})',
        r'(\d{4}\.\d{1,2}\.\d{1,2})'
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
    
# OpenCV 프레임에 한글 텍스트를 추가하는 함수
def put_text_korean(frame, text, pos, font_path, font_size, color):
    img_pil = Image.fromarray(frame)
    draw = ImageDraw.Draw(img_pil)
    font = ImageFont.truetype(font_path, font_size)
    draw.text(pos, text, font=font, fill=color)
    return np.array(img_pil)

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

    # 한글 폰트 경로 설정 (Windows 기준, 다른 OS는 경로 수정 필요)
    font_path = 'C:/Windows/Fonts/malgun.ttf'
    if not os.path.exists(font_path):
        font_path = '/usr/share/fonts/truetype/nanum/NanumGothic.ttf' # Linux 예시
        if not os.path.exists(font_path):
            print("경고: 한글 폰트 파일('malgun.ttf' 또는 'NanumGothic.ttf')을 찾을 수 없습니다.")
            font_path = None

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
                    info = {"code": code, "name": "미등록 상품", "exp": "N/A"}

                (x, y, w, h) = b["rect"]
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                
                text = f"{info['name']} | 유통기한: {info['exp']}"
                
                if font_path:
                    frame = put_text_korean(frame, text, (x, y - 40), font_path, 30, (255, 255, 0))
                else:
                    cv2.putText(frame, "Product:" + info['name'], (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            cv2.imshow('Barcode Scanner', frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        print("프로그램을 종료합니다.")
        cap.release()
        cv2.destroyAllWindows()

if __name__ == '__main__':
    main()