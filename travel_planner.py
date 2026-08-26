import os
import json
import argparse
import requests
from datetime import datetime

from dotenv import load_dotenv
from openai import OpenAI


# --------------------------------------------------
# 1. 여행 날짜 입력
# --------------------------------------------------
def get_travel_date():
    parser = argparse.ArgumentParser(
        description="국내 여행지 추천 프로그램"
    )

    parser.add_argument(
        "--date",
        required=True,
        help='여행 날짜를 "YYYY-MM-DD" 형식으로 입력하세요.'
    )

    args = parser.parse_args()

    try:
        datetime.strptime(args.date, "%Y-%m-%d")
    except ValueError:
        print("오류: 날짜 형식이 올바르지 않습니다.")
        print('예시: python travel_planner.py --date "2026-09-20"')
        exit()

    return args.date


# --------------------------------------------------
# 2. AI 1차 여행지 추천 + JSON 재시도
# --------------------------------------------------
def get_ai_recommendation(client, travel_date):
    prompt = f"""
여행 날짜는 {travel_date}입니다.

이 날짜에 여행하기 좋은 대한민국 국내 여행지 한 곳을 추천해주세요.

반드시 아래 JSON 형식으로만 답해주세요.
설명이나 마크다운은 추가하지 마세요.

{{
    "recommended_city": "추천 도시 또는 지역",
    "weather": "해당 시기의 일반적인 날씨 요약",
    "events": [
        "행사 또는 축제 후보 1",
        "행사 또는 축제 후보 2"
    ],
    "reason": "추천 근거를 2~4문장으로 작성"
}}
"""

    for attempt in range(2):
        response = client.responses.create(
            model="gpt-4.1-mini",
            input=prompt
        )

        try:
            recommendation = json.loads(response.output_text)

            required_keys = [
                "recommended_city",
                "weather",
                "events",
                "reason"
            ]

            for key in required_keys:
                if key not in recommendation:
                    raise ValueError(f"필수 키 누락: {key}")

            return recommendation

        except (json.JSONDecodeError, ValueError) as e:
            if attempt == 0:
                print("AI JSON 파싱 실패. 1회 재시도합니다.")

                prompt += """
이전 응답을 JSON으로 파싱할 수 없었습니다.

설명은 절대 추가하지 말고,
아래 4개 키만 포함한 올바른 JSON으로 다시 출력해주세요.

recommended_city
weather
events
reason
"""
            else:
                raise e


# --------------------------------------------------
# 3. Kakao Local API 맛집 검색
# --------------------------------------------------
def search_restaurants(city, kakao_api_key):
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"

    headers = {
        "Authorization": f"KakaoAK {kakao_api_key}"
    }

    params = {
        "query": f"{city} 맛집",
        "size": 5
    }

    response = requests.get(
        url,
        headers=headers,
        params=params,
        timeout=10
    )

    response.raise_for_status()

    data = response.json()
    restaurants = []

    for place in data.get("documents", []):
        restaurants.append({
            "name": place.get("place_name", ""),
            "address": (
                place.get("road_address_name")
                or place.get("address_name", "")
            ),
            "category": place.get("category_name", ""),
            "url": place.get("place_url", ""),
            "x": place.get("x", ""),
            "y": place.get("y", "")
        })

    return restaurants


# --------------------------------------------------
# 4. 원본 JSON 저장
# --------------------------------------------------
def save_raw_result(
    travel_date,
    recommendation,
    restaurants,
    errors
):
    os.makedirs("results", exist_ok=True)

    result_data = {
        "date": travel_date,
        "recommendation": recommendation,
        "restaurants": restaurants,
        "errors": errors
    }

    file_path = f"results/{travel_date}_raw.json"

    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(
            result_data,
            file,
            ensure_ascii=False,
            indent=2
        )

    return file_path


# --------------------------------------------------
# 5. 최종 여행 리포트 생성
# --------------------------------------------------
def create_final_report(
    client,
    travel_date,
    recommendation,
    restaurants
):
    restaurant_text = ""

    if restaurants:
        for index, restaurant in enumerate(restaurants, start=1):
            restaurant_text += (
                f"{index}. {restaurant['name']} "
                f"- {restaurant['address']}\n"
            )
    else:
        restaurant_text = "데이터 없음"

    prompt = f"""
아래 정보를 이용해서 국내 여행 추천 리포트를 작성해주세요.

여행 날짜:
{travel_date}

추천 정보:
{json.dumps(recommendation, ensure_ascii=False, indent=2)}

맛집 정보:
{restaurant_text}

반드시 Markdown 형식으로 작성해주세요.

아래 항목을 포함해주세요.

# {travel_date} 국내 여행 추천 리포트

## 추천 지역
## 추천 이유
## 날씨 요약
## 행사/축제
## 맛집 추천
## 1일 일정 제안

1일 일정은 오전 / 오후 / 저녁으로 나누어 작성해주세요.

맛집 정보가 없으면 "데이터 없음"이라고 표시해주세요.
"""

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt
    )

    return response.output_text


# --------------------------------------------------
# 6. Markdown 리포트 저장
# --------------------------------------------------
def save_markdown_report(travel_date, report_text):
    os.makedirs("results", exist_ok=True)

    file_path = f"results/{travel_date}_travel_plan.md"

    with open(file_path, "w", encoding="utf-8") as file:
        file.write(report_text)

    return file_path


# ==================================================
# 프로그램 실행 시작
# ==================================================

# 여행 날짜 입력
travel_date = get_travel_date()
print(f"입력한 여행 날짜: {travel_date}")

errors = []


# --------------------------------------------------
# 환경변수 및 API 키 확인
# --------------------------------------------------
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
kakao_api_key = os.getenv("KAKAO_REST_API_KEY")

if not api_key:
    print("오류: OPENAI_API_KEY가 설정되지 않았습니다.")
    print(".env 파일을 확인해주세요.")
    exit()

if not kakao_api_key:
    print("오류: KAKAO_REST_API_KEY가 설정되지 않았습니다.")
    print(".env 파일을 확인해주세요.")
    exit()


# OpenAI 클라이언트 생성
client = OpenAI(api_key=api_key)


# --------------------------------------------------
# [1/3] 1차 여행지 추천
# --------------------------------------------------
print()
print("[1/3] 1차 여행지 추천 생성 중(LLM)...")

try:
    recommendation = get_ai_recommendation(
        client,
        travel_date
    )

    print("AI 추천 결과:")
    print(f"추천 지역: {recommendation['recommended_city']}")
    print(f"날씨 요약: {recommendation['weather']}")
    print(f"행사/축제: {recommendation['events']}")
    print(f"추천 이유: {recommendation['reason']}")

except (json.JSONDecodeError, ValueError) as e:
    print("오류: AI 응답을 올바른 JSON으로 변환하지 못했습니다.")
    print(e)

    errors.append({
        "step": "recommendation",
        "type": "JSON_PARSE_ERROR",
        "message": str(e)
    })

    exit()

except Exception as e:
    print("OpenAI API 호출 중 오류가 발생했습니다.")
    print(e)

    errors.append({
        "step": "recommendation",
        "type": "API_ERROR",
        "message": str(e)
    })

    exit()


# --------------------------------------------------
# [2/3] Kakao 맛집 검색
# --------------------------------------------------
print()
print("[2/3] 맛집 검색 중(Kakao Local API)...")

try:
    city = recommendation["recommended_city"]

    restaurants = search_restaurants(
        city,
        kakao_api_key
    )

    if restaurants:
        print(f"맛집 {len(restaurants)}곳 검색 완료")

        for index, restaurant in enumerate(restaurants, start=1):
            print(
                f"{index}. {restaurant['name']} "
                f"- {restaurant['address']}"
            )

    else:
        print("검색 결과 0건")
        print("맛집 데이터 없음")

except Exception as e:
    restaurants = []

    print("맛집 검색 중 오류가 발생했습니다.")
    print(e)
    print("맛집 데이터 없음으로 처리합니다.")

    errors.append({
        "step": "place_search",
        "type": "API_ERROR",
        "message": str(e)
    })


# --------------------------------------------------
# 원본 JSON 저장
# --------------------------------------------------
raw_file = save_raw_result(
    travel_date,
    recommendation,
    restaurants,
    errors
)

print()
print(f"원본 JSON 저장 완료: {raw_file}")


# --------------------------------------------------
# [3/3] 최종 여행 리포트 생성
# --------------------------------------------------
print()
print("[3/3] 최종 여행 리포트 생성 중(LLM)...")

try:
    final_report = create_final_report(
        client,
        travel_date,
        recommendation,
        restaurants
    )

    markdown_file = save_markdown_report(
        travel_date,
        final_report
    )

    print("최종 여행 리포트 생성 완료!")
    print(f"Markdown 저장 완료: {markdown_file}")

except Exception as e:
    print("최종 여행 리포트 생성 중 오류가 발생했습니다.")
    print(e)