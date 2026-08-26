# A1-2 국내 여행지 추천 프로그램

## 1. 프로젝트 소개

사용자가 여행 날짜를 입력하면 OpenAI API를 활용하여 국내 여행지를 추천하고,
추천된 지역을 기반으로 Kakao Local API에서 맛집 정보를 검색한 뒤
최종 여행 계획을 Markdown 리포트로 생성하는 Python 프로그램입니다.

## 2. 주요 기능

- `--date "YYYY-MM-DD"` 형식으로 여행 날짜 입력
- 입력 날짜 형식 검증
- OpenAI API를 이용한 국내 여행지 추천
- AI 응답을 JSON 형식으로 파싱
- JSON 파싱 실패 시 최대 1회 재시도
- Kakao Local API를 이용한 추천 지역 맛집 검색
- 맛집 최대 5곳 검색
- 검색 결과를 원본 JSON 파일로 저장
- OpenAI API를 이용한 최종 여행 리포트 생성
- 최종 결과를 Markdown 파일로 저장
- API 오류 발생 시 오류 메시지 출력

## 3. 사용 기술

- Python
- OpenAI API
- Kakao Local API
- python-dotenv
- requests
- JSON
- Markdown

## 4. 환경 설정

프로젝트 루트 폴더에 `.env` 파일을 만들고 API 키를 설정합니다.

```text
OPENAI_API_KEY=본인의_OpenAI_API_Key
KAKAO_REST_API_KEY=본인의_Kakao_REST_API_Key
```

> 실제 API 키는 GitHub에 업로드하지 않습니다.

필요한 패키지를 설치합니다.

```bash
pip install openai python-dotenv requests
```

## 5. 실행 방법

VS Code 터미널에서 다음과 같이 실행합니다.

```bash
python travel_planner.py --date "2026-09-20"
```

날짜는 반드시 `YYYY-MM-DD` 형식으로 입력합니다.

## 6. 프로그램 동작 과정

```text
여행 날짜 입력
      ↓
[1/3] OpenAI API
국내 여행지 추천
      ↓
AI 응답 JSON 변환
      ↓
[2/3] Kakao Local API
추천 지역 맛집 검색
      ↓
원본 JSON 저장
      ↓
[3/3] OpenAI API
최종 여행 리포트 생성
      ↓
Markdown 파일 저장
```

## 7. 생성 파일

프로그램 실행 결과는 `results` 폴더에 저장됩니다.

```text
results/
├── 2026-09-20_raw.json
└── 2026-09-20_travel_plan.md
```

### 원본 JSON 파일

`YYYY-MM-DD_raw.json`

- 여행 날짜
- 추천 지역
- 날씨 요약
- 행사/축제
- 추천 이유
- 맛집 검색 결과
- 오류 기록

### 최종 여행 리포트

`YYYY-MM-DD_travel_plan.md`

- 추천 지역
- 추천 이유
- 날씨 요약
- 행사/축제
- 맛집 추천
- 오전/오후/저녁 1일 일정

## 8. 오류 처리

다음과 같은 오류 상황을 처리합니다.

- 날짜 형식 오류
- OpenAI API Key 미설정
- Kakao REST API Key 미설정
- OpenAI API 호출 오류
- AI 응답 JSON 파싱 오류
- Kakao Local API 호출 오류
- 맛집 검색 결과 0건

Kakao 맛집 검색에 실패하더라도 가능한 경우 빈 맛집 데이터로 처리하여
후속 리포트 생성을 계속 진행합니다.

## 9. 보안

API Key가 저장된 `.env` 파일은 GitHub에 업로드하지 않습니다.

`.gitignore`에 다음 항목을 등록했습니다.

```text
.env
.venv/
__pycache__/
```

## 10. 실행 예시

```text
입력한 여행 날짜: 2026-09-20

[1/3] 1차 여행지 추천 생성 중(LLM)...
AI 추천 결과:
추천 지역: ...
날씨 요약: ...
행사/축제: ...
추천 이유: ...

[2/3] 맛집 검색 중(Kakao Local API)...
맛집 5곳 검색 완료

원본 JSON 저장 완료: results/2026-09-20_raw.json

[3/3] 최종 여행 리포트 생성 중(LLM)...
최종 여행 리포트 생성 완료!
Markdown 저장 완료: results/2026-09-20_travel_plan.md
```