import streamlit as st
import feedparser
import pandas as pd
import os
import urllib.parse
from datetime import datetime, timedelta

KEYWORD_FILE = "keywords.txt"

def load_keywords():
    if os.path.exists(KEYWORD_FILE):
        with open(KEYWORD_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if content:
                return [k.strip() for k in content.split(",") if k.strip()]
    return ["공급망", "supply chain"]

def save_keywords(keywords):
    with open(KEYWORD_FILE, "w", encoding="utf-8") as f:
        f.write(",".join(keywords))

st.set_page_config(page_title="실시간 뉴스 관제", layout="wide")

st.markdown("""
    <style>
    .block-container { padding-top: 1rem !important; padding-bottom: 1rem !important; padding-left: 1rem !important; padding-right: 1rem !important; }
    .time-font { font-size: 11px !important; color: #888888; margin-bottom: 2px !important; }
    .title-font { font-size: 14px !important; font-weight: 600 !important; line-height: 1.3 !important; }
    .stDivider { margin-top: 8px !important; margin-bottom: 8px !important; }
    .kw-banner { border: 1px solid #d3d4d6; border-radius: 0.3rem; padding: 0.4rem 0.5rem; font-size: 0.9rem; font-weight: 600; margin-bottom: 0.1rem; display: flex; align-items: center; justify-content: center; background-color: transparent;}
    </style>
""", unsafe_allow_html=True)

if 'keywords' not in st.session_state:
    st.session_state['keywords'] = load_keywords()

st.sidebar.title("설정")

with st.sidebar.form(key='kw_form', clear_on_submit=True):
    new_kw = st.text_input("새 키워드 (하나씩 입력)")
    submit_btn = st.form_submit_button("추가")
    if submit_btn and new_kw.strip():
        kw = new_kw.strip()
        if kw not in st.session_state['keywords']:
            st.session_state['keywords'].append(kw)
            save_keywords(st.session_state['keywords'])
            st.rerun()

st.sidebar.markdown("### 📌 등록된 키워드")

for kw in list(st.session_state['keywords']):
    col1, col2 = st.sidebar.columns([4, 1])
    with col1:
        st.markdown(f"<div class='kw-banner'>{kw}</div>", unsafe_allow_html=True)
    with col2:
        if st.button("❌", key=f"del_{kw}"):
            st.session_state['keywords'].remove(kw)
            save_keywords(st.session_state['keywords'])
            st.rerun()

# [핵심 1] 중국, 대만, 홍콩, 일본 메이저 언론사 대거 추가
MAJOR_MEDIA = [
    # 국내 종합/경제지/통신사/IT전문지
    "매일경제", "한국경제", "조선", "중앙", "동아", "한겨레", "경향", "한국일보", "서울신문", "세계일보", "국민일보", "문화일보",
    "파이낸셜", "서울경제", "헤럴드", "머니투데이", "아시아경제", "이데일리", "비즈워치", "조세일보",
    "연합", "뉴시스", "뉴스1",
    "전자신문", "블로터", "지디넷", "디지털데일리", "아이뉴스24",
    
    # 영미권 경제/테크/금융/종합 
    "reuters", "bloomberg", "wall street journal", "wsj", "cnbc", "financial times", "forbes", "investing",
    "fortune", "the economist", "barron", "marketwatch", "yahoo finance", "business insider", "morningstar",
    "seeking alpha", "motley fool", "techcrunch", "the verge", "wired", "venturebeat", "engadget", 
    "new york times", "washington post", "the guardian", "telegraph", "ap", "afp",
    
    # 아시아권(중/일/대만/홍콩) 추가
    "nikkei", "yomiuri", "asahi", "mainichi", "nhk", "jiji", "toyokeizai", "diamond", "kyodo",
    "south china morning post", "scmp", "xinhua", "global times", "cgtn", "caixin", "yicai", "sina", "tencent", "udn", "chinatimes", "liberty times"
]

def get_news():
    all_news = []
    for kw in st.session_state['keywords']:
        safe_kw = urllib.parse.quote(kw)
