import streamlit as st
import feedparser
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
from datetime import datetime, timedelta, timezone
import time

st.set_page_config(page_title="Multi-Keyword Monitor", layout="wide")

if 'keywords' not in st.session_state:
    st.session_state.keywords = ["Supply Chain"]

current_keys = ", ".join(st.session_state.keywords)
st.title(f"🌐 실시간 통합 관제: {current_keys}")

def to_kst(struct_time):
    # RSS에서 제공하는 UTC 시간을 한국 시간(UTC+9)으로 정확히 변환
    if struct_time:
        dt_utc = datetime(*struct_time[:6], tzinfo=timezone.utc)
        return dt_utc.astimezone(timezone(timedelta(hours=9)))
    return datetime.now(timezone(timedelta(hours=9)))

def fetch_reddit(keyword):
    url = f"https://www.reddit.com/search.rss?q={quote(keyword)}&sort=new&t=hour"
    feed = feedparser.parse(url)
    items = []
    for e in feed.entries:
        real_url = e.id if 'http' in e.id else e.link
        if "/comments/" not in real_url: real_url = e.link.split('?')[0]
        dt = to_kst(e.updated_parsed) if 'updated_parsed' in e else datetime.now(timezone(timedelta(hours=9)))
        items.append({"Src": f"Reddit({keyword})", "Tit": e.title, "Url": real_url, "Time": dt})
    return items

def fetch_google_reuters(keyword):
    url = f"https://news.google.com/rss/search?q={quote(keyword)}+source:Reuters+when:1h&hl=en-US&gl=US&ceid=US:en"
    feed = feedparser.parse(url)
    return [{"Src": f"Reuters({keyword})", "Tit": e.title, "Url": e.link, "Time": to_kst(e.published_parsed)} for e in feed.entries[:5]]

def fetch_google_global(keyword):
    url = f"https://news.google.com/rss/search?q={quote(keyword)}+when:1h&hl=en-US&gl=US&ceid=US:en"
    feed = feedparser.parse(url)
    return [{"Src": f"Global({keyword})", "Tit": e.title, "Url": e.link, "Time": to_kst(e.published_parsed)} for e in feed.entries[:5]]

def fetch_naver(keyword):
    url = f"https://news.google.com/rss/search?q={quote(keyword)}&hl=ko&gl=KR&ceid=KR:ko"
    feed = feedparser.parse(url)
    return [{"Src": f"Naver({keyword})", "Tit": e.title, "Url": e.link, "Time": to_kst(e.published_parsed)} for e in feed.entries[:10]]

def fetch_investing(keyword):
    url = f"https://www.investing.com/search/?q={quote(keyword)}&tab=news"
    items = []
    try:
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        for art in soup.select('.articleItem')[:3]:
            t = art.select_one('.title')
            l = art.select_one('a.title')
            if t and l:
                # 인베스팅은 현재 한국 시간으로 처리
                items.append({"Src": f"Investing({keyword})", "Tit": t.get_text(strip=True), "Url": "https://www.investing.com" + l['href'], "Time": datetime.now(timezone(timedelta(hours=9)))})
    except: pass
    return items

with st.sidebar:
    with st.form(key='keyword_form', clear_on_submit=True):
        new_key = st.text_input("새 키워드 추가")
        submit = st.form_submit_button("추가")
    if submit and new_key and new_key not in st.session_state.keywords:
        st.session_state.keywords.append(new_key)
        st.rerun()
    st.write("---")
    for k in st.session_state.keywords: st.info(f"📍 {k}")
    if st.button("목록 초기화"):
        st.session_state.keywords = ["Supply Chain"]
        st.rerun()

all_data = []
for k in st.session_state.keywords:
    all_data += fetch_reddit(k) + fetch_google_reuters(k) + fetch_google_global(k) + fetch_naver(k) + fetch_investing(k)

# 시간순(최신순) 정렬
all_data.sort(key=lambda x: x['Time'], reverse=True)

for item in all_data:
    col1, col2 = st.columns([2.5, 7.5])
    with col1:
        st.caption(f"{item['Src']}")
        st.caption(f"🕒 {item['Time'].strftime('%m-%d %H:%M:%S')}")
    with col2:
        st.markdown(f"### [{item['Tit']}]({item['Url']})")
    st.divider()