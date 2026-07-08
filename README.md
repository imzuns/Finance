# Finance — KOSPI 이격도 대시보드

KOSPI 지수 및 구성종목의 이격도(주가 / N일 이동평균 × 100)를 계산하고 시각화하는 Streamlit 대시보드.

- 데이터: [pykrx](https://github.com/sharebook-kr/pykrx) (KRX Data Marketplace 기반)
- 홈: KOSPI 지수 종가/이동평균 차트와 이격도 추이
- 종목 스크리닝: KOSPI 구성종목 전체의 이격도를 정렬·검색·필터링

## 준비

1. [data.krx.co.kr](https://data.krx.co.kr) 에서 무료 회원가입 (일반 아이디/비밀번호)
2. `.env.example`을 참고해 `.env` 파일에 발급받은 계정 정보 입력
   ```
   KRX_ID=your_id
   KRX_PW=your_password
   ```
3. 의존성 설치
   ```
   pip install -r requirements.txt
   ```

## 실행

```
streamlit run app.py
```

## 배포

Streamlit Community Cloud에서 이 저장소를 연결하면 무료로 배포할 수 있다. 배포 시 `.env`의 값은 앱 설정의 Secrets(`KRX_ID`, `KRX_PW`)에 등록한다.
