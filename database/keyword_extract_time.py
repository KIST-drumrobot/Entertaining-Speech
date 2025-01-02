import requests
import openai
import re
import time
from konlpy.tag import Okt

# OpenAI API 키 설정
openai.api_key = "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"
# 텍스트 파일에서 내용을 읽는 함수
def read_text_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

# GPT에게 텍스트 파일 내용을 보내고 응답을 받는 함수
def get_gpt_response(file_path):
    start_time = time.time()  # 시작 시간 기록
    user_input = read_text_file(file_path)
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "상황을 제시하면 그에 맞는 적절한 대답을 하면 돼. A와 B는 친구야. 예를 들면, A : 오늘 눈이 올까? B : '눈이 오면 좋겠다.' 이런식으로 B의 대답은 A의 질문에 적절하게 이루어질거야. 단, B의 대답에서 명사형 키워드를 추출하기 적합하게 대답해줘. 반문은 하지 않아도 되고, 질문 키워드가 들어가게 대답해줘."},
            {"role": "assistant", "content": "user가 A의 질문을 제시할거야."},
            {"role": "user", "content": user_input}
        ]
    )
    gpt_response = response['choices'][0]['message']['content']
    gpt_time = time.time() - start_time  # 소요 시간 계산
    return gpt_response, gpt_time

# 형태소 분석기 객체 생성
okt = Okt()

# GPT 응답에서 키워드를 추출하는 함수 (모든 명사 및 동사 어근 추출)
def extract_okt_keywords(response_text):
    start_time = time.time()  # 시작 시간 기록
    keywords = []
    morphs = okt.pos(response_text, stem=True)
    for word, tag in morphs:
        if tag in ['Noun', 'Verb']:
            keywords.append(word)
    english_words = re.findall(r'[a-zA-Z]+', response_text)
    keywords.extend(english_words)
    okt_time = time.time() - start_time  # 소요 시간 계산
    return ', '.join(keywords), okt_time

# GPT에서 상황 키워드를 5개만 추출하는 함수
def extract_main_keywords(response_text):
    start_time = time.time()  # 시작 시간 기록
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "문장에서 상황을 나타내는 주요 명사형 키워드 5개만 콤마로 구분해서 추출해줘."},
            {"role": "user", "content": response_text}
        ]
    )
    main_keywords = response['choices'][0]['message']['content']
    main_keywords_time = time.time() - start_time  # 소요 시간 계산
    return main_keywords, main_keywords_time

# PC의 API 서버로 키워드를 전송하는 함수
def send_keywords_to_server(okt_keywords, main_keywords, gpt_response_text):
    start_time = time.time()  # 시작 시간 기록
    # PC의 API 서버 주소를 localhost로 설정
    server_url = 'http://127.0.0.1:5000/search'

    # keywords, main_keywords, gpt_response_text를 함께 전송
    response = requests.get(server_url, params={
        'okt_keywords': okt_keywords,
        'gpt_keywords': main_keywords,
        'gpt_response_text': gpt_response_text
    })
    server_time = time.time() - start_time  # 소요 시간 계산
    if response.status_code == 200:
        mp3_files = response.json().get('files', [])
        if mp3_files:
            print(f"검색된 mp3 파일: {mp3_files}")
        else:
            print("해당 키워드로 mp3 파일을 찾을 수 없습니다.")
    else:
        print(f"Error: {response.status_code}, {response.text}")
    return server_time

# 메인 실행
if __name__ == '__main__':
    text_file_path = "./requestA.txt"

    # GPT 응답 생성
    gpt_response_text, gpt_time = get_gpt_response(text_file_path)
    print(f"GPT Response: {gpt_response_text}")

    # 형태소 분석 키워드 추출
    okt_keywords, okt_time = extract_okt_keywords(gpt_response_text)
    print(f"OKT Keywords: {okt_keywords}")

    # GPT 주요 키워드 추출
    main_keywords, main_keywords_time = extract_main_keywords(gpt_response_text)
    print(f"GPT Keywords: {main_keywords}")

    # 키워드로 서버 호출
    server_time = send_keywords_to_server(okt_keywords, main_keywords, gpt_response_text)

    # 총 소요 시간 계산
    total_time = gpt_time + okt_time + main_keywords_time + server_time

    # 각 단계의 시간 출력
    print("\n--- Timing ---")
    print(f"GPT Response Time: {gpt_time:.2f} seconds")
    print(f"OKT Keyword Extraction Time: {okt_time:.2f} seconds")
    print(f"Main Keyword Extraction Time: {main_keywords_time:.2f} seconds")
    print(f"Server Request Time: {server_time:.2f} seconds")
    print(f"Total Execution Time: {total_time:.2f} seconds")