#!/usr/bin/env python3
"""
Docker MySQL의 products 테이블에서 description 데이터를 가져와
성별, 색상, 사이즈 관련 단어를 제거한 후 name 필드에 업데이트하는 스크립트
"""

import pymysql
import re
import os
from typing import List, Tuple
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()


# 제거할 단어 목록
GENDER_WORDS = [
    '남성', '여성', '남자', '여자', '남녀공용', '공용', '소년' , '소녀', '남녀' , '남여',
    'men', 'women', 'male', 'female', 'unisex', 'mens', 'womens'
]

COLOR_WORDS = [
    # 한글 색상
    '빨강', '빨간', '주황', '주황색', '노랑', '노란', '노란색', '초록', '초록색',
    '파랑', '파란', '파란색', '남색', '보라', '보라색', '자주', '자주색',
    '검정', '검은', '검은색', '흰색', '흰', '회색', '회', '은색', '은',
    '베이지', '네이비', '카키', '핑크', '레드', '블루', '그린', '옐로우', '오렌지',
    '차콜', '샌드', '아이보리', '크림', '와인', '버건디', '코랄', '민트', '라벤더',
    '올리브', '머스타드', '터키', '스카이', '로얄', '다크', '라이트', '브라운',
    # 영어 색상
    'red', 'blue', 'green', 'yellow', 'black', 'white', 'gray', 'grey', 'pink', 'purple', 'orange',
    'navy', 'beige', 'khaki', 'brown', 'ivory', 'cream', 'maroon', 'olive', 'teal',
    'coral', 'mint', 'lavender', 'turquoise', 'sky', 'royal', 'dark', 'light', 'burgundy',
    'wine', 'sand', 'charcoal', 'salmon', 'peach', 'lime', 'cyan', 'magenta', 'indigo',
    'violet', 'amber', 'bronze', 'copper', 'gold', 'silver', 'platinum', 'tan', 'camel'
]

# 색상 줄임말 (blk, wht, blu 등) - re.IGNORECASE로 대소문자 구분 없음
COLOR_ABBREVIATIONS = [
    'blk', 'wht', 'blu', 'grn', 'yel', 'red', 'pnk', 'prp', 'org', 'brn', 
    'gry', 'nvy', 'bge', 'khk', 'ivr', 'crm', 'mrn', 'olv', 'tel'
]

SIZE_WORDS = [
    'xs', 's', 'm', 'l', 'xl', 'xxl', 'xxxl',  # re.IGNORECASE로 대소문자 구분 없음
    '사이즈', '크기', 'size',  # re.IGNORECASE로 대소문자 구분 없음
    '90', '95', '100', '105', '110',  # 옷 사이즈
    '230', '240', '250', '260', '270', '280',  # 신발 사이즈
]

# 숫자+사이즈 패턴 (3xl, 2xl, 4xl 등)
SIZE_PATTERNS = [
    r'\d+xs', r'\d+s', r'\d+m', r'\d+l', r'\d+xl', r'\d+xxl', r'\d+xxxl',  # 3xl, 2xl 등
]

# 정규표현식 컴파일 (성능 최적화)
_compiled_patterns = {
    'color_suffix': re.compile(r'[가-힣]+색'),
    'size_patterns': [re.compile(pattern, re.IGNORECASE) for pattern in SIZE_PATTERNS],
    'whitespace': re.compile(r'\s+'),
    'brackets': re.compile(r'\[[^\]]*\]|\([^)]*\)|\{[^}]*\}'),  # [], (), {} 제거
    'single_digit_spaces': re.compile(r'\b\d(\s+\d)+\b')  # 단일 숫자 띄어쓰기 연속 (예: "1 1", "1 1 1")
}


def remove_words(text: str, words_to_remove: List[str]) -> str:
    """
    텍스트에서 특정 단어들을 부분 문자열로 제거하는 함수
    단어 경계 없이 포함된 부분만 제거 (예: "검은색원피스" → "원피스")
    
    Args:
        text: 원본 텍스트
        words_to_remove: 제거할 단어 리스트
    
    Returns:
        단어가 제거된 텍스트
    """
    if not text:
        return text
    
    result = text
    for word in words_to_remove:
        # 단어 경계 없이 부분 문자열로 제거 (대소문자 구분 없음)
        pattern = re.escape(word)
        result = re.sub(pattern, '', result, flags=re.IGNORECASE)
    
    # 여러 공백을 하나로 정리 (컴파일된 패턴 사용)
    result = _compiled_patterns['whitespace'].sub(' ', result)
    # 앞뒤 공백 제거
    result = result.strip()
    
    return result


def remove_color_suffix(text: str) -> str:
    """
    "~색" 패턴을 전체적으로 제거하는 함수
    단어 경계 없이 부분 문자열로 제거 (예: "검은색원피스" → "원피스")
    
    Args:
        text: 원본 텍스트
    
    Returns:
        "~색" 패턴이 제거된 텍스트
    """
    if not text:
        return text
    
    # 한글 + "색" 패턴 제거 (컴파일된 패턴 사용)
    # 예: "빨간색", "파란색", "검은색", "검은색원피스" 등
    result = _compiled_patterns['color_suffix'].sub('', text)
    
    # 여러 공백을 하나로 정리
    result = _compiled_patterns['whitespace'].sub(' ', result)
    # 앞뒤 공백 제거
    result = result.strip()
    
    return result


def remove_size_patterns(text: str) -> str:
    """
    숫자+사이즈 패턴을 제거하는 함수 (예: 3xl, 2xl 등)
    
    Args:
        text: 원본 텍스트
    
    Returns:
        숫자+사이즈 패턴이 제거된 텍스트
    """
    if not text:
        return text
    
    result = text
    # 컴파일된 패턴 사용
    for compiled_pattern in _compiled_patterns['size_patterns']:
        result = compiled_pattern.sub('', result)
    
    # 여러 공백을 하나로 정리
    result = _compiled_patterns['whitespace'].sub(' ', result)
    # 앞뒤 공백 제거
    result = result.strip()
    
    return result


def remove_special_chars(text: str) -> str:
    """
    특수문자(대괄호, 소괄호, 중괄호)와 그 안의 내용을 제거하는 함수
    예: [검은색] → (빈 문자열), (사이즈) → (빈 문자열)
    
    Args:
        text: 원본 텍스트
    
    Returns:
        특수문자가 제거된 텍스트
    """
    if not text:
        return text
    
    # 대괄호, 소괄호, 중괄호와 그 안의 내용 제거
    result = _compiled_patterns['brackets'].sub('', text)
    
    # 여러 공백을 하나로 정리
    result = _compiled_patterns['whitespace'].sub(' ', result)
    # 앞뒤 공백 제거
    result = result.strip()
    
    return result


def remove_single_digit_spaces(text: str) -> str:
    """
    단일 숫자 사이의 띄어쓰기 연속을 제거하는 함수
    예: "1 1 1" → "", "1 1" → ""
    
    Args:
        text: 원본 텍스트
    
    Returns:
        단일 숫자 띄어쓰기가 제거된 텍스트
    """
    if not text:
        return text
    
    # 단일 숫자 띄어쓰기 연속 제거 (예: "1 1 1", "1 1")
    result = _compiled_patterns['single_digit_spaces'].sub('', text)
    
    # 여러 공백을 하나로 정리
    result = _compiled_patterns['whitespace'].sub(' ', result)
    # 앞뒤 공백 제거
    result = result.strip()
    
    return result


def clean_description(description: str) -> str:
    """
    description에서 성별, 색상, 사이즈 관련 단어를 제거
    단어 경계 없이 부분 문자열로 제거 (예: "검은색원피스" → "원피스")
    
    Args:
        description: 원본 description
    
    Returns:
        전처리된 description
    """
    if not description:
        return description
    
    # 특수문자 제거 (대괄호, 소괄호, 중괄호와 그 안의 내용)
    cleaned = remove_special_chars(description)
    
    # 성별 단어 제거
    cleaned = remove_words(cleaned, GENDER_WORDS)
    
    # "~색" 패턴 전체 제거 (예: "빨간색", "파란색", "검은색원피스" 등)
    cleaned = remove_color_suffix(cleaned)
    
    # 색상 단어 제거
    cleaned = remove_words(cleaned, COLOR_WORDS)
    
    # 색상 줄임말 제거
    cleaned = remove_words(cleaned, COLOR_ABBREVIATIONS)
    
    # 숫자+사이즈 패턴 제거 (3xl, 2xl 등)
    cleaned = remove_size_patterns(cleaned)
    
    # 사이즈 단어 제거
    cleaned = remove_words(cleaned, SIZE_WORDS)
    
    # 단일 숫자 띄어쓰기 연속 제거 (예: "1 1 1", "1 1")
    cleaned = remove_single_digit_spaces(cleaned)
    
    return cleaned


def get_db_connection():
    """
    Docker MySQL 데이터베이스 연결 생성
    
    Returns:
        데이터베이스 연결 객체
    """
    # 환경 변수에서 설정 가져오기 (기본값 제공)
    host = os.getenv('DB_HOST', 'localhost')
    port = int(os.getenv('DB_PORT', 3306))
    user = os.getenv('DB_USER', 'root')
    password = os.getenv('DB_PASSWORD', '')
    database = os.getenv('DB_NAME', 'test')
    
    connection = pymysql.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )
    
    return connection


def update_products_name(batch_size: int = 5000):
    """
    products 테이블의 description을 전처리하여 name 필드에 업데이트
    배치 처리로 최적화 (30만 개 이상의 데이터 처리 가능)
    
    Args:
        batch_size: 배치 크기 (기본값: 5000)
                    - M3 Max 36GB RAM: 5000-10000 권장
                    - 일반적인 환경: 1000-3000 권장
                    - 메모리가 부족한 경우: 500-1000 권장
                    - 네트워크가 느린 경우: 더 작은 값 권장
    """
    connection = None
    try:
        # 데이터베이스 연결
        connection = get_db_connection()
        # autocommit 비활성화 (배치 커밋을 위해)
        connection.autocommit(False)
        print("데이터베이스 연결 성공")
        
        with connection.cursor() as cursor:
            # 전체 개수 확인 (name이 NULL이거나 빈 문자열인 것만)
            cursor.execute("SELECT COUNT(*) as total FROM products WHERE description IS NOT NULL AND description != '' AND (name IS NULL OR name = '')")
            total_count = cursor.fetchone()['total']
            print(f"총 {total_count:,}개의 제품을 처리합니다. (배치 크기: {batch_size:,})")
            
            updated_count = 0
            processed_count = 0
            last_id = 0  # 마지막 처리한 ID 추적
            
            while True:
                # ID 순서로 정렬하여 마지막 처리한 ID 이후부터 가져오기
                cursor.execute(
                    "SELECT id, description, name FROM products WHERE description IS NOT NULL AND description != '' AND (name IS NULL OR name = '') AND id > %s ORDER BY id LIMIT %s",
                    (last_id, batch_size)
                )
                products = cursor.fetchall()
                
                if not products:
                    break
                
                batch_updates = []
                
                for product in products:
                    product_id = product['id']
                    description = product['description']
                    current_name = product['name']
                    
                    # description 전처리
                    cleaned_description = clean_description(description)
                    
                    # name이 NULL이고 전처리된 description이 있으면 업데이트
                    if cleaned_description:
                        batch_updates.append((cleaned_description, product_id))
                    
                    last_id = product_id  # 마지막 처리한 ID 업데이트
                    processed_count += 1
                
                # 배치 업데이트 실행
                if batch_updates:
                    cursor.executemany(
                        "UPDATE products SET name = %s WHERE id = %s",
                        batch_updates
                    )
                    updated_count += len(batch_updates)
                
                # 배치 단위로 커밋
                connection.commit()
                
                # 진행 상황 표시
                if total_count > 0:
                    progress = (processed_count / total_count) * 100
                    print(f"진행 중... {processed_count:,}/{total_count:,} ({progress:.1f}%) - 업데이트: {updated_count:,}개")
                else:
                    print(f"진행 중... {processed_count:,}개 처리 - 업데이트: {updated_count:,}개")
                
                # 더 이상 처리할 데이터가 없으면 종료
                if len(products) < batch_size:
                    break
            
            print(f"\n처리 완료!")
            print(f"  - 총 처리: {processed_count:,}개")
            print(f"  - 업데이트: {updated_count:,}개")
            
    except Exception as e:
        if connection:
            connection.rollback()
        print(f"오류 발생: {e}")
        raise
    
    finally:
        if connection:
            connection.close()
            print("데이터베이스 연결 종료")


if __name__ == "__main__":
    print("=" * 50)
    print("Products 테이블 description 전처리 및 name 업데이트")
    print("=" * 50)
    update_products_name()

