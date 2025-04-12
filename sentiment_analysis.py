from transformers import pipeline
from tqdm import tqdm

# Hugging Face에서 제공하는 한국어 감정 분석 모델 로드
classifier = pipeline("sentiment-analysis", model="nlp04/korean_sentiment_analysis_dataset3")

# 감정 분석 및 단순화 매핑 통합 함수
def analyze_and_map_sentiments(texts):
    results = []
    for text in tqdm(texts, desc="Processing Sentiments"):
        try:
            result = classifier(text)
            label = result[0]['label']  # 감정 레이블 추출

            # 감정 레이블 단순화
            if label in ['긍정', '행복', '기쁨', '기대감', '즐거움']:
                simple_label = 'POSITIVE'
            elif label in ['부정', '분노', '슬픔', '당황', '불안', '혐오']:
                simple_label = 'NEGATIVE'
            else:
                simple_label = 'NEUTRAL'

            results.append(simple_label)
        except Exception as e:
            results.append("ERROR")  # 에러 처리 시 "ERROR" 추가
    return results
