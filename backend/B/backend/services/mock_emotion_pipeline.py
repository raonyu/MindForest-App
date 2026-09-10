def analyze_emotion_pipeline(text: str):
    """
    C 파트 개발용 임시 감정 분석 함수.

    나중에 B 파트의 실제 analyze_emotion_pipeline()이 완성되면
    이 Mock 파일 대신 실제 함수를 import하면 된다.
    """

    return {
        "emotions": {
            "joy": 25.0,
            "trust": 35.0,
            "fear": 20.0,
            "surprise": 15.0,
            "sadness": 70.0,
            "disgust": 10.0,
            "anger": 55.0,
            "anticipation": 30.0
        },
        "confidence": 0.84,
        "needs_bws": True,
        "bws_used": True,
        "status": "completed"
    }