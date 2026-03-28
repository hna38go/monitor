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

# 모바일 고밀도 UI (사이드바 버튼 크기 및 여백 최소화 반영)
st.markdown("""
    <style>
    .block-container { padding-top: 1rem !important; padding-bottom: 1rem !important; padding-left: 1rem !important; padding-right: 1rem !important; }
    .time-font { font-size: 11px !important; color: #888888; margin-bottom: 2px !important; }
    .title-font { font-size: 14px !important; font-weight: 600 !important; line-height: 1.3 !important; }
    .stDivider { margin-top: 8px !important; margin-bottom: 8px !important; }
    div[data-testid="stSidebar"] button { padding: 0px 5px !important; min-height: 0px !important; line-height: 1.5 !important; }
    </style>
""", unsafe_allow_html=True)

if 'keywords' not in st.session_state:
    st.session_state['keywords'] = load_keywords()

st.sidebar.title("설정")

with st.sidebar.form(key='kw_form', clear_on_submit=True):
    new_kw = st.text_input("새 키워드 추가")
    submit_btn = st.form_submit_button("추가")
    if submit_btn and new_kw.strip():
        kw = new_kw.strip()
        if kw not in st.session_state['keywords']:
            st.session_state['keywords'].append(kw)
            save_keywords(st.session_state['keywords'])
            st.rerun()

st.sidebar.markdown("### 📌 등록된 키워드")

# 키워드 배너 제거 및 텍스트 바로 옆에 X 버튼 위치하도록 수정
for kw in list(st.session_state['keywords']):
    col1, col2 = st.sidebar.columns([4, 1])
    with col1:
        st.markdown(f"<div style='margin-top: 4px; font-weight: bold;'>{kw}</div>", unsafe_allow_html=True)
    with col2:
        if st.button("❌", key=f"del_{kw}"):
            st.session_state['keywords'].remove(kw)
            save_keywords(st.session_state['keywords'])
            st.rerun()

def get_news():
    all_news = []
    for kw in st.session_state['keywords']:
        safe_kw = urllib.parse.quote(kw)
        
        feeds = {
            "인베스팅(KR)": f"https://news.google.com/rss/search?q={safe_kw}+site:kr.investing.com&hl=ko&gl=KR",
            "인베스팅(US)": f"https://news.google.com/rss/search?q={safe_kw}+site:investing.com&hl=en&gl=US",
            "국내뉴스": f"https://news.google.com/rss/search?q={safe_kw}+when:1d&hl=ko&gl=KR",
            "국제뉴스": f"https://news.google.com/rss/search?q={safe_kw}+when:1d&hl=en&gl=US",
            "일본(영문)": f"https://news.google.com/rss/search?q={safe_kw}+when:1d&hl=en-JP&gl=JP",
            "중화권(영문)": f"https://news.google.com/rss/search?q={safe_kw}+when:1d&hl=en-HK&gl=HK"
        }
        
        for media_type, url in feeds.items():
            feed = feedparser.parse(url)
            for entry in feed.entries: 
                source_name = entry.get('source', {}).get('title', media_type)
                published = entry.get('published_parsed', None)
                dt = datetime(*published[:6]) + timedelta(hours=9) if published else datetime.now()
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

# 원본 로직 유지: 별도 버튼 없이 접속 시 또는 키워드 변경 시에만 1회 자동 수집
if st.session_state['keywords']:
    with st.spinner('전 세계 영문/국내 뉴스 수집 중...'):
        news_data = get_news()
        
    if news_data:
        df = pd.DataFrame(news_data).sort_values(by="시간", ascending=False).drop_duplicates(subset=['제목']).reset_index(drop=True)
        
        st.caption(f"**총 {len(df)}개**의 최신 기사가 수집되었습니다.")
        
        for _, row in df.iterrows():
            time_str = row['시간'].strftime('%m-%d %H:%M')
            st.markdown(f"<div class='time-font'>[{row['분류']} - {row['매체']}] {time_str}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='title-font'><a href='{row['링크']}' target='_blank' style='text-decoration:none; color:#1f77b4;'>{row['제목']}</a></div>", unsafe_allow_html=True)
            st.divider()
    else:
        st.warning("현재 키워드에 해당하는 최신 뉴스가 없습니다.")
else:
    st.info("사이드바에서 관제할 키워드를 추가해 주십시오.")
