import json
import random
import time
from openai import OpenAI

client = OpenAI(api_key="OPENAI_API_KEY")

def get_labels(text):
    prompt = f"""
다음 텍스트를 읽고 Plutchik 8가지 기본 감정을 분석해.
해당하는 감정은 1, 아니면 0으로 표기해. 여러 감정이 동시에 해당할 수 있어.
반드시 아래 JSON 형식으로만 응답해.

텍스트: "{text}"

{{
  "joy": 0, "trust": 0, "fear": 0, "surprise": 0,
  "sadness": 0, "disgust": 0, "anger": 0, "anticipation": 0
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
    
    with open("sampled_texts.json", "r", encoding="utf-8") as f:
        texts = json.load(f)
        
    LIMIT = 5000
    texts_to_process = texts[:LIMIT]
    
    final_dataset = []
    
    for i, text in enumerate(texts_to_process, 1):
        print(f"[{i}/{LIMIT}] 분석 중...")
        labels = get_labels(text)
        
        if labels:
            final_dataset.append({
                "text": text,
                "labels": labels
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
    
    print(f"\n✅ 완료! train({len(train_data)}), val({len(val_data)}), test({len(test_data)}) 생성됨.")

if __name__ == "__main__":
    main()