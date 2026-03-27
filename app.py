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

# 모바일 고밀도 UI 유지
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

# 키워드 개별 추가 폼
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

# 키워드 배너 및 삭제 버튼
for kw in list(st.session_state['keywords']):
    col1, col2 = st.sidebar.columns([4, 1])
    with col1:
        st.markdown(f"<div class='kw-banner'>{kw}</div>", unsafe_allow_html=True)
    with col2:
        if st.button("❌", key=f"del_{kw}"):
            st.session_state['keywords'].remove(kw)
            save_keywords(st.session_state['keywords'])
            st.rerun()

def get_news():
    all_news = []
    for kw in st.session_state['keywords']:
        safe_kw = urllib.parse.quote(kw)
        
        # [수정] 모든 국가별 파이프라인 유지
        feeds = {
            "인베스팅(KR)": f"https://news.google.com/rss/search?q={safe_kw}+site:kr.investing.com&hl=ko&gl=KR",
            "인베스팅(US)": f"https://news.google.com/rss/search?q={safe_kw}+site:investing.com&hl=en&gl=US",
            "국내뉴스": f"https://news.google.com/rss/search?q={safe_kw}+when:1d&hl=ko&gl=KR",
            "국제뉴스": f"https://news.google.com/rss/search?q={safe_kw}+when:1d&hl=en&gl=US",
            "일본뉴스": f"https://news.google.com/rss/search?q={safe_kw}+when:1d&hl=ja&gl=JP",
            "중화권뉴스": f"https://news.google.com/rss/search?q={safe_kw}+when:1d&hl=zh-TW&gl=TW"
        }
        
        for media_type, url in feeds.items():
            feed = feedparser.parse(url)
            for entry in feed.entries: 
                source_name = entry.get('source', {}).get('title', media_type)
                
                # [수정 핵심] MAJOR_MEDIA 필터링 로직을 완전히 제거함 (모든 출처 허용)
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

if st.session_state['keywords']:
    with st.spinner('전 세계 실시간 뉴스 수집 중...'):
        news_data = get_news()
        
    if news_data:
        # 시간순 정렬 및 중복 제거
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
