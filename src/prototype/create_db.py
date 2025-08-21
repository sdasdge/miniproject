import pandas as pd
import random
from datetime import datetime, timedelta

# 50개의 샘플 상품명 리스트 (원하는 상품으로 자유롭게 변경 가능)
product_names = [
    "농심 신라면", "오뚜기 진라면(매운맛)", "삼양 불닭볶음면", "팔도 비빔면", "짜파게티",
    "햇반", "오뚜기밥", "비비고 왕교자", "동원참치", "스팸 클래식",
    "서울우유", "매일우유", "바나나맛 우유", "덴마크 드링킹요구르트", "액티비아",
    "코카콜라", "칠성사이다", "펩시콜라", "삼다수", "포카리스웨트",
    "참이슬 후레쉬", "처음처럼", "카스", "테라", "하이트",
    "빼빼로", "새우깡", "포카칩", "초코파이", "홈런볼",
    "월드콘", "메로나", "투게더", "붕어싸만코", "빵빠레",
    "맥심 모카골드", "카누 미니 다크", "제주감귤주스", "델몬트 오렌지주스", "옥수수수염차",
    "해표 식용유", "청정원 순창고추장", "백설 설탕", "곰표 밀가루", "몽고간장",
    "페리오 치약", "리스테린", "도브 비누", "질레트 면도기", "깨끗한나라 휴지"
]

# 이미 사용된 바코드를 추적하기 위한 집합(set)
used_codes = set()

def generate_unique_barcode():
    """대한민국 국가코드(880)로 시작하는 13자리 유니크 바코드를 생성합니다."""
    while True:
        # 880 + 랜덤 10자리 숫자
        code = "880" + str(random.randint(1000000000, 9999999999))
        if code not in used_codes:
            used_codes.add(code)
            return code

def generate_random_exp_date():
    """오늘 날짜로부터 30일에서 500일 사이의 유통기한을 YYYY-MM-DD 형식으로 생성합니다."""
    days_to_add = random.randint(30, 500)
    future_date = datetime.now() + timedelta(days=days_to_add)
    return future_date.strftime('%Y-%m-%d')

# 데이터를 저장할 리스트
data = []

# 상품명 리스트를 기반으로 데이터 생성
for name in product_names:
    product_data = {
        "code": generate_unique_barcode(),
        "name": name,
        "exp": generate_random_exp_date()
    }
    data.append(product_data)

# 리스트를 Pandas DataFrame으로 변환
df = pd.DataFrame(data)

# CSV 파일로 저장
output_filename = "product_db.csv"
df.to_csv(output_filename, index=False, encoding='utf-8-sig')

print(f"✅ 총 {len(df)}개의 샘플 데이터가 포함된 '{output_filename}' 파일이 성공적으로 생성되었습니다.")