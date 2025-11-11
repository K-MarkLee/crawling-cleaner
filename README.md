# Products Description 전처리 스크립트

Docker MySQL의 `products` 테이블에서 `description` 데이터를 가져와 성별, 색상, 사이즈 관련 단어를 제거한 후 `name` 필드에 업데이트하는 스크립트입니다.

## 설치

```bash
pip install -r requirements.txt
```

## 환경 변수 설정

프로젝트 루트 디렉토리에 `.env` 파일을 생성하세요:

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=your_database_name
```

**중요**: `.env` 파일은 반드시 프로젝트 루트 디렉토리에 있어야 하며, 실제 비밀번호로 변경해야 합니다.

또는 환경 변수로 직접 설정:

```bash
export DB_HOST=localhost
export DB_PORT=3306
export DB_USER=root
export DB_PASSWORD=your_password
export DB_NAME=your_database_name
```

## 사용 방법

```bash
python clean_products.py
```

### 배치 크기 조정 (선택사항)

기본 배치 크기는 5,000입니다. 환경에 맞게 조정할 수 있습니다:

```python
# clean_products.py 파일에서
update_products_name(batch_size=10000)  # 더 큰 배치
```

**권장 배치 크기:**
- M3 Max 36GB RAM: 5,000-10,000
- 일반적인 환경: 1,000-3,000
- 메모리가 부족한 경우: 500-1,000

## 동작 방식

1. Docker MySQL의 `products` 테이블에서 `description`이 있고 `name`이 NULL이거나 빈 문자열인 레코드만 가져옵니다.
2. 각 `description`에서 다음 항목들을 제거합니다:
   - **특수문자**: `[검은색]`, `(사이즈)`, `{색상}` 등 대괄호, 소괄호, 중괄호와 그 안의 내용
   - **성별**: 남성, 여성, 남자, 여자, 남녀공용, 남녀, 남여, 소년, 소녀, men, women, unisex 등
   - **색상 패턴**: "~색" 패턴 전체 (예: "빨간색", "파란색", "검은색원피스" → "원피스")
   - **색상 단어**: 
     - 한글: 빨강, 파랑, 검정, 흰색, 회색, 베이지, 네이비, 카키, 차콜, 샌드, 아이보리, 크림, 와인, 버건디, 코랄, 민트, 라벤더 등
     - 영어: red, blue, green, yellow, black, white, gray, pink, purple, orange, navy, beige, khaki, brown, coral, mint, lavender 등
   - **색상 줄임말**: blk, wht, blu, grn, yel, pnk, prp, org, brn, gry, nvy, bge, khk 등
   - **사이즈 패턴**: 숫자+사이즈 (예: 3xl, 2xl, 4xl 등)
   - **사이즈 단어**: XS, S, M, L, XL, XXL, XXXL, 사이즈, 크기, size, 90, 95, 100, 105, 110, 230, 240, 250, 260, 270, 280 등
   - **단일 숫자 띄어쓰기**: "1 1 1", "1 1" 같은 패턴
3. 전처리된 `description`을 `name` 필드에 업데이트합니다.

## 성능 최적화

- **배치 처리**: 5,000개씩 배치로 처리하여 메모리 효율성 향상
- **Bulk Update**: `executemany()`를 사용하여 여러 업데이트를 한 번에 실행
- **ID 기반 순차 처리**: 중복 처리 방지 및 안정적인 처리
- **정규표현식 컴파일**: 자주 사용하는 패턴을 미리 컴파일하여 성능 향상

## 처리 대상

- `description`이 NULL이 아니고 빈 문자열이 아닌 경우
- `name`이 NULL이거나 빈 문자열인 경우

## 주의사항

- ⚠️ **스크립트 실행 전에 데이터베이스 백업을 권장합니다.**
- ⚠️ **업데이트 전에 테스트 데이터로 먼저 확인하세요.**
- ⚠️ **대량 데이터(30만 개 이상) 처리 시 시간이 소요될 수 있습니다.**
- ⚠️ **네트워크 연결이 불안정한 경우 배치 크기를 줄이는 것을 권장합니다.**

