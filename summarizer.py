import openai

# OpenAI API 키 설정
openai.api_key = "your_key"


def summarize_with_sentiment(content, sentiment):
    if not content:
        return ""

    # 프롬프트
    prompt = f"""
    다음은 뉴스 내용과 감정 분류 결과입니다. 뉴스 내용을 주어진 감정에 맞춰 두 줄 또는 세 줄로 요약하세요. 
    '-' 또는 '뉴스 내용: '와 같은 형식이 아닌, 같은 기사 형식에 맞는 줄글 형식으로 요약하세요.
    명사형으로 끝맺지 말고 동사나 형용사와 같은 형식으로 글을 끝맺으세요.
    요약은 반드시 100자 이내로 작성하세요. 부가적인 내용 없이 글만 작성하세요.

    감정: {sentiment}
    뉴스 내용: {content}

    요약 규칙:
    1. 긍정: 긍정적인 측면을 강조하는 요약을 작성하세요.
    2. 부정: 부정적인 측면을 드러내는 요약을 작성하세요.
    3. 중립: 객관적이고 편향되지 않는 요약을 작성하세요.
    4. 불필요한 형식(감정 레이블, 괄호 등)은 포함하지 마세요.

    요약:
    """

    try:
        # GPT 호출
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant specialized in summarizing content."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300,
            temperature=0.7
        )
        # 결과 추출
        return response.choices[0].message["content"].strip()
    except Exception as e:
        print(f"GPT 요약 실패: {e}")
        return "요약 실패"
