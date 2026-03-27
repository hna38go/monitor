import streamlit as st
import feedparser
import pandas as pd
import os
from datetime import datetime, timedelta

KEYWORD_FILE = "keywords.txt"

def load_keywords():
    if os.path.exists(KEYWORD_FILE):
        with open(KEYWORD_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    return "공급망, supply chain"

def save_keywords(keywords):
    with open(KEYWORD_FILE, "w", encoding="utf-8") as f:
        f.write(keywords)

st.set_page_config(page_title="실시간 뉴스 관제", layout="wide")

# 모바일 최적화 고밀도 CSS (여백 최소화, 글씨 축소)
st.markdown("""
    <style>
    .block-container { padding-top: 1rem !important; padding-bottom: 1rem !important; padding-left: 1rem !important; padding-right: 1rem !important; }
    .time-font { font-size: 11px !important; color: #888888; margin-bottom: 2px !important; }
    .title-font { font-size: 14px !important; font-weight: 600 !important; line-height: 1.3 !important; }
    .stDivider { margin-top: 8px !important; margin-bottom: 8px !important; }
    </style>
""", unsafe_allow_html=True)

if 'current_ks' not in st.session_state:
    st.session_state['current_ks'] = load_keywords()

st.sidebar.title("설정")
user_input = st.sidebar.text_input("키워드 (쉼표 구분)", st.session_state['current_ks'])

if user_input != st.session_state['current_ks']:
    save_keywords(user_input)
    st.session_state['current_ks'] = user_input

search_keywords = [k.strip() for k in user_input.split(",") if k.strip()]

def get_news():
    all_news = []
    for kw in search_keywords:
        # 국내 전체 및 국제 전체 포괄 통합망 구축
        feeds = {
            "국내뉴스": f"https://news.google.com/rss/search?q={kw}&hl=ko&gl=KR&ceid=KR:ko",
            "국제뉴스": f"https://news.google.com/rss/search?q={kw}&hl=en&gl=US&ceid=US:en"
        }
        for media_type, url in feeds.items():
            feed = feedparser.parse(url)
            for entry in feed.entries[:15]: # 수집량 확보를 위해 15개씩 긁어옵니다
                published = entry.get('published_parsed', None)
                # 무조건 한국 시간(KST)으로 강제 변환
                dt = datetime(*published[:6]) + timedelta(hours=9) if published else datetime.now()
                
                # 구글 RSS에서 원본 매체 이름 추출
                source_name = entry.get('source', {}).get('title', media_type)
                
                all_news.append({
                    "분류": media_type,
                    "매체": source_name,
                    "제목": entry.title,
                    "시간": dt, 
                    "링크": entry.link
                })
    return all_news

st.markdown("### 🚀 실시간 관제 센터")

if search_keywords:
    news_data = get_news()
    if news_data:
        # 수집된 모든 뉴스를 완벽한 최신 시간순으로 통합 정렬
        df = pd.DataFrame(news_data).sort_values(by="시간", ascending=False).drop_duplicates(subset=['제목']).reset_index(drop=True)
        
        for _, row in df.iterrows():
            time_str = row['시간'].strftime('%m-%d %H:%M')
            # [분류 - 원본매체명] 시간 형태로 출력
            st.markdown(f"<div class='time-font'>[{row['분류']} - {row['매체']}] {time_str}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='title-font'><a href='{row['링크']}' target='_blank' style='text-decoration:none; color:#1f77b4;'>{row['제목']}</a></div>", unsafe_allow_html=True)
            st.divider()
