import json
import random
import time
import os
from openai import OpenAI

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def get_labels(text):
    # [최종 고도화] 팀원 A 피드백 + 다중 라벨 + 무감정 완벽 반영 프롬프트
    prompt = f"""
당신은 감정 분석 데이터 라벨링 전문가입니다.
주어진 텍스트를 읽고, 문맥상 존재하는 모든 Plutchik 8가지 기본 감정을 찾아 각각 0(없음) 또는 1(있음)로 판단해 주세요.

[🚨 매우 엄격한 라벨링 기준 🚨]
1. 다중 감정 허용 (Multi-label): 텍스트에 드러난 감정이 여러 개라면 주저하지 말고 해당하는 모든 감정에 1을 부여하세요. (예: 슬픔과 분노가 같이 느껴지면 둘 다 1)
2. anticipation (기대) 엄격 제어: 무언가를 '설레며 기다리거나 긍정적으로 기대하는 감정'일 때만 1입니다. "내일은 일찍 일어나야지", "운동을 해야겠어", "어떻게 해야 할까?" 같은 단순한 미래 계획, 다짐, 해결책 모색, 질문은 절대로 anticipation이 아닙니다 (무조건 0으로 처리).
3. 뚜렷한 감정만 1 부여: 텍스트에 감정이 명확하고 강하게 드러난 경우에만 1로 표시하세요. 모호하거나 추측해야 한다면 무조건 0을 부여합니다.
4. 감정 없음(Neutral) 허용: 뚜렷한 감정이 없거나 단순한 일상, 행동, 객관적 사실 나열뿐이라면 8개 감정 모두 0이어야 합니다. 억지로 감정을 만들어내지 마세요.

텍스트: "{text}"

반드시 아래 JSON 형식으로만 응답하세요.
{{
  "labels": {{
    "joy": 0,
    "trust": 0,
    "fear": 0,
    "surprise": 0,
    "sadness": 0,
    "disgust": 0,
    "anger": 0,
    "anticipation": 0
  }}
}}
"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"API 에러: {e}")
        return None

def main():
    print("🚀 GPT 라벨링 및 데이터셋 생성 시작...")
    
    # 1. 감성대화 말뭉치 (마지막 발화 잘라낸 버전) 불러오기
    try:
        with open("sampled_texts.json", "r", encoding="utf-8") as f:
            texts = json.load(f)
    except FileNotFoundError:
        print("🚨 sampled_texts.json 파일이 없습니다. extract_texts.py를 먼저 실행하세요.")
        return
        
    # 2. 직접 생성한 '진짜 무감정 데이터 300개' 불러오기
    try:
        with open("neutral_texts.json", "r", encoding="utf-8") as f:
            neutral_sentences = json.load(f)
            print(f"✅ 무감정(Neutral) 텍스트 {len(neutral_sentences)}개 로드 완료!")
    except FileNotFoundError:
        print("🚨 neutral_texts.json 파일이 없습니다! 파일을 생성해주세요.")
        return
    
    # 3. 데이터 합치기 (무감정 데이터가 확실히 들어가도록 맨 앞에 배치)
    combined_texts = neutral_sentences + texts
        
    LIMIT = 5000
    texts_to_process = combined_texts[:LIMIT]
    
    final_dataset = []
    
    for i, text in enumerate(texts_to_process, 1):
        print(f"[{i}/{LIMIT}] 분석 중...")
        labels = get_labels(text)
        
        if labels and "labels" in labels:
            final_dataset.append({
                "text": text,
                "labels": labels["labels"] # JSON 응답 구조에서 labels 알맹이만 추출
            })
        
        # 토큰 제한(Rate Limit) 방지를 위해 0.2초 휴식
        time.sleep(0.2)
        
    # 8:1:1 비율로 Train / Val / Test 분할
    random.shuffle(final_dataset)
    total = len(final_dataset)
    train_end = int(total * 0.8)
    val_end = int(total * 0.9)
    
    train_data = final_dataset[:train_end]
    val_data = final_dataset[train_end:val_end]
    test_data = final_dataset[val_end:]
    
    # 파일 저장 함수
    def save_jsonl(data, filename):
        with open(filename, 'w', encoding='utf-8') as f:
            for row in data:
                f.write(json.dumps(row, ensure_ascii=False) + '\n')
                
    save_jsonl(train_data, "train.jsonl")
    save_jsonl(val_data, "val.jsonl")
    save_jsonl(test_data, "test.jsonl")
    
    print(f"\n🎉 완료! train({len(train_data)}), val({len(val_data)}), test({len(test_data)}) 생성됨.")

if __name__ == "__main__":
    main()