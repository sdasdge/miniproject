import cv2
import easyocr
import re
from datetime import datetime

# OCR 리더 초기화
reader = easyocr.Reader(['en', 'ko'], gpu=False)

# 이미지 로드
def load_image(path):
    img = cv2.imread(path)
    if img is None:
        raise FileNotFoundError(path)
    return img

# 간단한 전처리(조명 개선 예시)
def preprocess(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # CLAHE로 대비 강화
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    enhanced = clahe.apply(gray)
    return enhanced

# 텍스트에서 날짜 패턴 추출
def extract_date(texts):
    # 다양한 형식에 대응하는 패턴
    date_patterns = [
        r'(19|20)\d{2}[-/\.](0?[1-9]|1[0-2])[-/\.](0?[1-9]|[12]\d|3[01])',
        r'(0?[1-9]|1[0-2])[-/\.](0?[1-9]|[12]\d|3[01])[-/\.](19|20)\d{2}',
        r'(19|20)\d{2}[년](0?[1-9]|1[0-2])[월](0?[1-9]|[12]\d|3[01])[일]?'
    ]
    for t in texts:
        for pat in date_patterns:
            m = re.search(pat, t)
            if m:
                raw = m.group(0)
                # 간단 파싱(J/J)/YYYY-MM-DD 등으로 맞춤
                for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%m-%d-%Y", "%m/%d/%Y"]:
                    try:
                        dt = datetime.strptime(raw.replace('년','').replace('월','').replace('일',''), fmt)
                        return dt.date()
                    except Exception:
                        pass
    return None

def main(image_path):
    img = load_image(image_path)
    pre = preprocess(img)
    # OCR 수행: 결과 포맷은 [(bbox, text, conf), ...]
    results = reader.readtext(pre)
    # 텍스트 모음
    texts = [r[1] for r in results]
    date_found = extract_date(texts)
    print("추출 텍스트:", texts)
    if date_found:
        today = datetime.today().date()
        delta = (date_found - today).days
        print(f"유통기한: {date_found}, 남은 일수: {delta}")
        if delta < 0:
            print("만료됨.")
        elif delta <= 7:
            print("임박! 알림 필요.")
        else:
            print("정상 구간.")
    else:
        print("유통기한 날짜를 감지하지 못했습니다.")

if __name__ == "__main__":
    main("path/to/your/product_label.jpg")