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
            return f.read().strip()
    return "공급망, supply chain"

def save_keywords(keywords):
    with open(KEYWORD_FILE, "w", encoding="utf-8") as f:
        f.write(keywords)

st.set_page_config(page_title="실시간 뉴스 관제", layout="wide")

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
        safe_kw = urllib.parse.quote(kw)
        
        # [핵심 1] 인베스팅 한국(KR)과 영문(US) 사이트 철저히 분리
        # [핵심 2] 통합망에 when:1d 파라미터를 추가하여 무조건 '최근 24시간' 기사만 강제 타겟팅
        feeds = {
            "인베스팅(KR)": f"https://news.google.com/rss/search?q={safe_kw}+site:kr.investing.com&hl=ko&gl=KR",
            "인베스팅(US)": f"https://news.google.com/rss/search?q={safe_kw}+site:investing.com&hl=en&gl=US",
            "국내통합": f"https://news.google.com/rss/search?q={safe_kw}+when:1d&hl=ko&gl=KR",
            "국제통합": f"https://news.google.com/rss/search?q={safe_kw}+when:1d&hl=en&gl=US"
        }
        
        for media_type, url in feeds.items():
            feed = feedparser.parse(url)
            # [핵심 3] [15:] 제한 삭제. 구글이 던지는 100여 개 기사를 남김없이 전부 쓸어 담음
            for entry in feed.entries: 
                published = entry.get('published_parsed', None)
                dt = datetime(*published[:6]) + timedelta(hours=9) if published else datetime.now()
                
                source_name = entry.get('source', {}).get('title', media_type)
                
                # 구글 뉴스 특유의 " - 매체명" 꼬리표가 제목에 붙는 것을 깔끔하게 제거
                clean_title = entry.title.rsplit(" - ", 1)[0]
                
                all_news.append({
                    "분류": media_type,
                    "매체": source_name,
                    "제목": clean_title,
                    "시간": dt, 
                    "링크": entry.link
                })
    return all_news

st.markdown("### 🚀 실시간 관제 센터")

if search_keywords:
    with st.spinner('실시간 기사 대량 수집 중...'):
        news_data = get_news()
        
    if news_data:
        # 수집된 수백 개의 뉴스를 시간순으로 정렬
        df = pd.DataFrame(news_data).sort_values(by="시간", ascending=False).drop_duplicates(subset=['제목']).reset_index(drop=True)
        
        st.caption(f"**총 {len(df)}개**의 기사가 수집되었습니다.")
        
        for _, row in df.iterrows():
            time_str = row['시간'].strftime('%m-%d %H:%M')
            st.markdown(f"<div class='time-font'>[{row['분류']} - {row['매체']}] {time_str}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='title-font'><a href='{row['링크']}' target='_blank' style='text-decoration:none; color:#1f77b4;'>{row['제목']}</a></div>", unsafe_allow_html=True)
            st.divider()
