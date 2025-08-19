import cv2
import easyocr
import re
from datetime import datetime, date, timezone, timedelta
from typing import List, Optional, Dict, Any

# OCR 리더 초기화 (필요한 언어만 로드)
reader = easyocr.Reader(['en', 'ko'], gpu=False)

# 이미지 로드
def load_image(path: str) -> 'np.ndarray':
    img = cv2.imread(path)
    if img is None:
        raise FileNotFoundError(f"Image not found: {path}")
    return img

# 확장된 전처리 함수: 다층 조합으로 안정성 증가
def preprocess(img: 'np.ndarray') -> 'np.ndarray':
    # 1) LAB 컬러 공간으로 밝기 개선
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l_clahe = clahe.apply(l)
    lab_out = cv2.merge([l_clahe, a, b])
    rgb = cv2.cvtColor(lab_out, cv2.COLOR_LAB2BGR)

    # 2) 노이즈 감소 및 선명도 유지
    rgb = cv2.bilateralFilter(rgb, d=9, sigmaColor=75, sigmaSpace=75)

    # 3) 그레이스케일로 OCR 친화적으로 변환
    gray = cv2.cvtColor(rgb, cv2.COLOR_BGR2GRAY)

    # 4) 가우시안 블러/적응 임계 조합으로 이진화
    gray_blur = cv2.GaussianBlur(gray, (3, 3), 0)
    thresh = cv2.adaptiveThreshold(
        gray_blur, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 11, 2
    )

    # 5) 필요 시 모션 보정이나 모서리 강화
    # 예: Morphological opening으로 잔여 노이즈 제거
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=1)

    return thresh

# 텍스트에서 날짜 패턴 추출 (강화 버전)
def extract_date(texts: List[str]) -> Optional[date]:
    # 다양한 형식의 날짜를 포괄하는 정규식 목록
    date_patterns = [
        # 2024-12-31, 2024/12/31, 2024.12.31
        r'(19|20)\d{2}[년\-\/\.](0?[1-9]|1[0-2])[월\-\/\.](0?[1-9]|[12]\d|3[01])[일]?',
        # 12-31-2024, 12/31/2024
        r'(0?[1-9]|1[0-2])[\-\/\.](0?[1-9]|[12]\d|3[01])[\-\/\.](19|20)\d{2}',
        # 31-12-2024, 31/12/2024
        r'(0?[1-9]|[12]\d|3[01])[\-\/\.](0?[1-9]|1[0-2])[\-\/\.](19|20)\d{2}',
        # 한국어 표기: 2024년12월31일
        r'(19|20)\d{2}[년](0?[1-9]|1[0-2])[월](0?[1-9]|[12]\d|3[01])[일]?'
    ]
    for t in texts:
        for pat in date_patterns:
            m = re.search(pat, t)
            if m:
                raw = m.group(0)
                # 다양한 포맷으로 파싱 시도
                candidates = [
                    "%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d",
                    "%m-%d-%Y", "%m/%d/%Y", "%m.%d.%Y",
                    "%d-%m-%Y", "%d/%m/%Y", "%d.%m.%Y",
                    "%Y년%m월%d일"
                ]
                # 한글 표기에서 '년','월','일' 제거
                cleaned = raw.replace('년', '').replace('월', '').replace('일', '')
                for fmt in candidates:
                    try:
                        dt = datetime.strptime(cleaned, fmt)
                        return dt.date()
                    except Exception:
                        continue
    return None

# OCR 수행: 결과 포맷 확정 및 신뢰도 필터링
def perform_ocr(img: 'np.ndarray', min_conf: float = 0.4) -> (List[Dict[str, Any]], List[str]):
    # EasyOCR의 반환 포맷: [(bbox, text, conf), ...]
    results = reader.readtext(img, paragraph=False)
    filtered = [r for r in results if (r[2] if isinstance(r, list) else 0) >= min_conf]
    texts = [r[1] for r in filtered]
    return filtered, texts

# 결과 포맷 정의
def format_output(texts: List[str], date_found: Optional[date]) -> Dict[str, Any]:
    out = {
        "texts": texts,
        "date_found": date_found.isoformat() if date_found else None,
        "delta_days": None,
        "status": "정보 없음",
        "confidence_avg": None,
        "raw_results_count": None
    }
    if date_found:
        today = date.today()
        delta = (date_found - today).days
        out["delta_days"] = delta
        if delta < 0:
            out["status"] = "만료됨"
        elif delta <= 7:
            out["status"] = "임박! 알림 필요"
        else:
            out["status"] = "정상 구간"
        # 평균 신뢰도(해당 텍스트들 기반으로 계산 가능)
    return out

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