import cv2
import easyocr
import re
from datetime import datetime, date, timezone, timedelta
from typing import List, Optional, Dict, Any

# OCR 리더 초기화 (필요한 언어만 로드)
reader = easyocr.Reader(['en', 'ko'], gpu=False)

def preprocess(img: 'np.ndarray') -> 'np.ndarray':
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    l_clahe = clahe.apply(l)
    lab_out = cv2.merge([l_clahe, a, b])
    rgb = cv2.cvtColor(lab_out, cv2.COLOR_LAB2BGR)

    rgb = cv2.bilateralFilter(rgb, d=7, sigmaColor=75, sigmaSpace=75)

    gray = cv2.cvtColor(rgb, cv2.COLOR_BGR2GRAY)
    gray_blur = cv2.GaussianBlur(gray, (3, 3), 0)

    # 두 가지 방식 중 하나를 선택해 비교
    thresh_ada = cv2.adaptiveThreshold(gray_blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    _, thresh_otsu = cv2.threshold(gray_blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # 상황에 따라 선택
    return thresh_ada  # 혹은 thresh_otsu

def extract_date(texts: List[str]) -> Optional[date]:
    date_patterns = [
        r'(19|20)\d{2}[년\-\/\.](0?[1-9]|1[0-2])[월\-\/\.](0?[1-9]|[12]\d|3[01])[일]?',
        r'(0?[1-9]|1[0-2])[월\-\/\.](0?[1-9]|[12]\d|3[01])[일]?[\.]?(19|20)\d{2}',
        r'(19|20)\d{2}[./\-](0?[1-9]|1[0-2])[./\-](0?[1-9]|[12]\d|3[01])',
        r'(19|20)\d{2}[년](0?[1-9]|1[0-2])[월](0?[1-9]|[12]\d|3[01])[일]?'
    ]
    for t in texts:
        for pat in date_patterns:
            m = re.search(pat, t)
            if m:
                raw = m.group(0)
                cleaned = raw.replace('년','').replace('월','').replace('일','')
                # 여러 포맷 시도
                for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d", "%m-%d-%Y", "%d-%m-%Y", "%m/%d/%Y", "%d/%m/%Y", "%Y년%m월%d일"]:
                    try:
                        dt = datetime.strptime(cleaned, fmt)
                        return dt.date()
                    except ValueError:
                        pass
    return None

# OCR 수행: 결과 포맷 확정 및 신뢰도 필터링
def perform_ocr(img: 'np.ndarray', min_conf: float = 0.4) -> (List[Dict[str, Any]], List[str]):
    # EasyOCR의 반환 포맷: [(bbox, text, conf), ...]
    results = reader.readtext(img, paragraph=False)
    filtered = [r for r in results if (r[2] if isinstance(r, list) else 0) >= min_conf]
    texts = [r[1] for r in filtered]
    return filtered, texts

def format_output(texts: List[str], date_found: Optional[date], min_conf: float = 0.4, avg_conf: Optional[float] = None) -> Dict[str, Any]:
    delta = None
    status = "정보 없음"

    if date_found:
        today = date.today()
        delta = (date_found - today).days
        if delta < 0:
            status = "만료됨"
        elif delta <= 7:
            status = "임박! 알림 필요"
        else:
            status = "정상 구간"

    return {
        "texts": texts,
        "date_found": date_found.isoformat() if date_found else None,
        "delta_days": delta,
        "status": status,
        "average_confidence": avg_conf if avg_conf is not None else None,
        "summary": {
            "text_count": len(texts),
            "date_present": date_found is not None
        }
    }
# 메인 실행 함수: 옵션 인자 포함
def main(image_path: str, min_conf: float = 0.4) -> Dict[str, Any]:
    img = load_image(image_path)
    pre = preprocess(img)

    # OCR 수행(신뢰도 기반 필터링)
    results, texts = perform_ocr(pre, min_conf=min_conf)

    # 날짜 추출
    date_found = extract_date(texts)

    # 결과 포맷
    output = format_output(texts, date_found)

    # 보조 정보: 원본 결과에서 텍스트들/결과 수 정보도 삽입
    output["raw_texts"] = texts
    output["raw_results_count"] = len(results)

    return output

if __name__ == "__main__":
    # 예시 경로를 실제 이미지로 바꿔 실행
    path = "path/to/your/product_label.jpg"
    res = main(path, min_conf=0.45)
    print(res)