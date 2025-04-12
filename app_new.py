from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import re

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
# CORS 활성화

# 네이버 지도 API 키 설정
MAPS_CLIENT_ID = "moiswv0h0p"
MAPS_CLIENT_SECRET = "VWLR0m1RA0irvfCMi6pKmmtdMnFlDUgij9KzWRP9"

# 뉴스 수집 함수
def fetch_news(region, category):
    API_ENDPOINT = "https://openapi.naver.com/v1/search/news.json"
    CLIENT_ID = "moiswv0h0p"
    CLIENT_SECRET = "VWLR0m1RA0irvfCMi6pKmmtdMnFlDUgij9KzWRP9"

    query = f"{region} {category}"

    headers = {
        "X-Naver-Client-Id": MAPS_CLIENT_ID,
        "X-Naver-Client-Secret": MAPS_CLIENT_SECRET,
    }

    params = {
        "query": query,
        "display": 10,  # 최대 10개 뉴스
        "start": 1,
        "sort": "sim",  # 유사도 기준 정렬
    }

    response = requests.get(API_ENDPOINT, headers=headers, params=params)
    if response.status_code == 200:
        items = response.json().get("items", [])
        return [
            {
                "title": item["title"].replace("<b>", "").replace("</b>", ""),
                "link": item["link"],
                "description": item.get("description", "기사 본문의 요약문이 없습니다.").replace("<b>", "").replace("</b>", "")
            }
            for item in items
        ]
    return []

import re

# 지역명을 좌표로 변환하는 함수
def fetch_coordinates(region):
    GEOCODE_API = "https://naveropenapi.apigw.ntruss.com/map-geocode/v2/geocode"
    headers = {
        "X-NCP-APIGW-API-KEY-ID": MAPS_CLIENT_ID,
        "X-NCP-APIGW-API-KEY": MAPS_CLIENT_SECRET,
    }
    params = {"query": region}

    response = requests.get(GEOCODE_API, headers=headers, params=params)
    if response.status_code == 200:
        results = response.json().get("addresses", [])
        if results:
            location = results[0]
            print(f"{region}의 좌표: {location['y']}, {location['x']}")  # 디버깅 로그
            return {
                "lat": location["y"],
                "lng": location["x"],
            }
        print(f"{region}에 대한 좌표 결과 없음")  # 디버깅 로그
    else:
        print(f"API 요청 실패: {response.status_code}, {response.text}")  # 디버깅 로그
    return None

# 기사 본문에서 지역명을 추출하는 함수
def extract_region(description):
    # 정규식으로 지역명 추출
    match = re.search(r"([가-힣]+시|[가-힣]+군|[가-힣]+구|[가-힣]+읍|[가-힣]+면)", description)
    if match:
        print(f"추출된 지역명: {match.group(1)}")  # 디버깅 로그
        return match.group(1)
    print("지역명 추출 실패")  # 디버깅 로그
    return None


# 뉴스에 포함된 지역명을 기반으로 좌표를 추가
def enhance_news_with_coordinates(news_data):
    enhanced_news = []

    for article in news_data:
        region_name = extract_region(article["description"])
        if region_name:
            coordinates = fetch_coordinates(region_name)
            if coordinates:
                article["lat"] = coordinates["lat"]
                article["lng"] = coordinates["lng"]
            else:
                article["lat"] = None
                article["lng"] = None
        else:
            # 지역명이 없으면 기본값 할당
            article["lat"] = None
            article["lng"] = None

        enhanced_news.append(article)

    return enhanced_news

# 뉴스와 좌표 데이터를 통합
@app.route("/search_news", methods=["GET"])
def search_news():
    region = request.args.get("region")
    category = request.args.get("category")

    if not region or not category:
        return jsonify({"error": "Region and category are required"}), 400

    coordinates = fetch_coordinates(region)
    if not coordinates:
        return jsonify({"error": f"Failed to find coordinates for region: {region}"}), 404

    news_data = fetch_news(region, category)
    enhanced_news = enhance_news_with_coordinates(news_data)

    return jsonify({
        "region": region,
        "category": category,
        "coordinates": coordinates,
        "news": enhanced_news,
    })

if __name__ == "__main__":
    app.run(debug=True)