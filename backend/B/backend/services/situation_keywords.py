"""Deterministic Korean topic matching; no external API and no diagnostic claims."""
import json
import re

TOPICS = {
    "시험": ("시험", "고사", "수능", "퀴즈"),
    "팀플": ("팀플", "조별", "팀 프로젝트", "팀프로젝트"),
    "수면": ("수면", "불면", "잠을", "잠이", "잠도", "잠들", "밤샘", "밤을 샜", "늦잠"),
    "친구": ("친구", "동기", "절친"),
    "가족": ("가족", "부모", "엄마", "아빠", "어머니", "아버지", "동생", "언니", "오빠", "누나", "형제"),
    "취업": ("취업", "면접", "자소서", "자기소개서", "입사", "채용"),
    "직장": ("직장", "회사", "상사", "야근", "출근", "퇴근", "업무"),
    "학업": ("공부", "과제", "수업", "학교", "학점", "졸업", "강의"),
    "건강": ("건강", "병원", "통증", "아팠", "아프", "감기", "진료"),
    "운동": ("운동", "산책", "헬스", "조깅", "스트레칭", "수영", "요가"),
    "관계": ("연애", "애인", "남자친구", "여자친구", "이별", "헤어", "다퉜", "다투", "갈등"),
    "경제": ("월세", "생활비", "등록금", "용돈", "월급", "대출", "빚", "돈이", "돈을"),
}


def diary_text(content):
    if not content:
        return ""
    try:
        parsed = json.loads(content)
        if isinstance(parsed, dict):
            return str(parsed.get("mainText") or "")
    except (TypeError, ValueError):
        pass
    return str(content)


def extract_topics(text):
    text = re.sub(r"\s+", " ", text or "")
    matches = []
    for topic, aliases in TOPICS.items():
        positions = [text.find(alias) for alias in aliases if alias in text]
        if positions:
            matches.append((min(positions), topic))
    return [topic for _, topic in sorted(matches)]
