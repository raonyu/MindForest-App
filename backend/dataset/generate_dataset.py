import json
import random
import time
import os
from openai import OpenAI

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def get_labels(text):
    # [진짜 최종] A님 피드백(anticipation 완화, trust 기준 추가) 완벽 반영 프롬프트
    prompt = f"""
당신은 감정 분석 데이터 라벨링 전문가입니다.
주어진 텍스트를 읽고, 문맥상 존재하는 모든 Plutchik 8가지 기본 감정을 찾아 각각 0(없음) 또는 1(있음)로 판단해 주세요.

[🚨 라벨링 세부 기준 (필독) 🚨]
1. 다중 감정 허용 (Multi-label): 텍스트에 드러난 감정이 여러 개라면 주저하지 말고 해당하는 모든 감정에 1을 부여하세요. (예: 기대감과 신뢰감이 동시에 느껴지면 둘 다 1)
2. anticipation (기대) - 기준 완화: "앞으로 잘 되길 바라는 마음, 긍정적인 기대, 설렘, 희망"이 조금이라도 느껴진다면 1을 부여하세요. (단, 감정이 실리지 않은 '단순한 미래 계획, 다짐, 질문'은 여전히 0입니다.)
3. trust (신뢰) - 기준 추가: "누군가(또는 자신)를 믿거나 굳게 의지하는 마음, 안도감, 든든함, 신뢰감"이 느껴진다면 1을 부여하세요.
4. 뚜렷한 감정만 1 부여: 텍스트에 감정이 명확하게 드러난 경우에만 1로 표시하세요. 모호하거나 억지로 추측해야 한다면 0을 부여합니다.
5. 감정 없음(Neutral) 허용: 뚜렷한 감정이 없거나 단순한 일상, 행동, 객관적 사실 나열뿐이라면 8개 감정 모두 0이어야 합니다. 억지로 감정을 만들어내지 마세요.

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
    print("🚀 GPT 라벨링 및 데이터셋 재생성 시작 (anticipation/trust 타겟팅 최적화)...")
    
    # 1. 감성대화 말뭉치 불러오기
    try:
        with open("sampled_texts.json", "r", encoding="utf-8") as f:
            texts = json.load(f)
    except FileNotFoundError:
        print("🚨 sampled_texts.json 파일이 없습니다. extract_texts.py를 먼저 실행하세요.")
        return
        
    # 2. 진짜 무감정 데이터 불러오기
    try:
        with open("neutral_texts.json", "r", encoding="utf-8") as f:
            neutral_sentences = json.load(f)
            print(f"✅ 무감정(Neutral) 텍스트 {len(neutral_sentences)}개 로드 완료!")
    except FileNotFoundError:
        print("🚨 neutral_texts.json 파일이 없습니다! 파일을 생성해주세요.")
        return
    
    # 3. 데이터 합치기
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
                "labels": labels["labels"]
            })
        
        # API 속도 제한 방지용 딜레이
        time.sleep(0.2)
        
    # 8:1:1 비율 분할
    random.shuffle(final_dataset)
    total = len(final_dataset)
    train_end = int(total * 0.8)
    val_end = int(total * 0.9)
    
    train_data = final_dataset[:train_end]
    val_data = final_dataset[train_end:val_end]
    test_data = final_dataset[val_end:]
    
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