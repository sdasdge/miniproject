import cv2  
from pyzbar import pyzbar  
import time  

# 예시 매핑 데이터(실제 상황에서는 DB나 CSV로 관리)  
PRODUCT_DB = {  
    "0123456789012": {"name": "김치", "exp": "2025-09-15"},  
    "123456789012": {"name": "우유", "exp": "2025-08-25"},  
    # 필요 시 추가  
}  

def decode_barcode(frame):  
    # 프레임에서 바코드 인식  
    barcodes = pyzbar.decode(frame)  
    results = []  
    for b in barcodes:  
        data = b.data.decode('utf-8')  
        typ = b.type  
        results.append({"data": data, "type": typ, "rect": b.rect})  
    return results  

def format_display(info):  
    if not info:  
        return "인식 데이터 없음"  
    name = info.get("name", "Unknown")  
    exp = info.get("exp", "N/A")  
    code = info.get("code", "")  
    return f"{name} | 유통기한: {exp} | 코드: {code}"  

def main():  
    cap = cv2.VideoCapture(0)  
    if not cap.isOpened():  
        print("카메라를 열 수 없습니다.")  
        return  

    # 중복 등록 방지용 시간 기록  
    seen = {}  
    READ_INTERVAL = 2.0  # 초  
    last_print = 0.0  

    while True:  
        ret, frame = cap.read()  
        if not ret:  
            break  

        # 바코드 디코딩  
        bars = decode_barcode(frame)  
        for b in bars:  
            code = b["data"]  
            now = time.time()  
            # 중복 검사  
            if code in seen and now - seen[code] < READ_INTERVAL:  
                continue  
            seen[code] = now  

            # 매핑 데이터 조회  
            info = None  
            if code in PRODUCT_DB:  
                info = {  
                    "name": PRODUCT_DB[code]["name"],  
                    "exp": PRODUCT_DB[code]["exp"],  
                    "code": code  
                }  
            else:  
                info = {"name": "Unknown", "exp": "N/A", "code": code}  

            # 텍스트로 화면에 표시  
            text = format_display(info)  

            # 바코드 위치에 사각형과 텍스트 오버레이  
            (x, y, w, h) = b["rect"]  
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)  
            cv2.putText(frame, text, (x, y - 10),  
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)  

            # 콘솔 출력 (선택)  
            if now - last_print > 1.0:  
                print(text)  
                last_print = now  

        cv