from flask import Flask, jsonify, request
from flask_cors import CORS
from crawler import start_crawling
from sentiment_analysis import analyze_and_map_sentiments
from summarizer import summarize_with_sentiment

app = Flask(__name__)
CORS(app)

@app.route('/topic-search', methods=['POST'])
def topic_search():
    try:
        # 클라이언트 요청 데이터 가져오기
        data = request.get_json()
        search_content = data.get('topic')
        max_news = 4  # 고정값

        if not search_content:
            return jsonify({"error": "검색어를 입력해주세요."}), 400

        # 크롤링 실행
        startday = ["2024.11.14"]
        endday = ["2024.12.14"]
        news_data = start_crawling(search_content, startday, endday, max_news)

        # 감정 분석 및 단순화 매핑 통합 호출
        texts = [news.get('title', '') for news in news_data]
        sentiments = analyze_and_map_sentiments(texts)

        # 감정 결과 매핑
        sentiment_mapping = {
            "POSITIVE": "긍정",
            "NEGATIVE": "부정",
            "NEUTRAL": "중립"
        }
        mapped_sentiments = [sentiment_mapping.get(sentiment, "중립") for sentiment in sentiments]

        # 요약 및 감정 결과 추가
        for i, news in enumerate(news_data):
            news["sentiment"] = mapped_sentiments[i]
            content = news.get("content", "")
            sentiment = mapped_sentiments[i]
            news["content_summarized"] = summarize_with_sentiment(content, sentiment)

        # JSON 형식으로 반환
        return jsonify({"news": news_data})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)

@app.route("/", methods=["GET"])
def home():
    return "서버 잘 작동 중!", 200

