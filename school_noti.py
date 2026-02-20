import os
import sys
from turtle import update
from dotenv import load_dotenv
load_dotenv()
########################################################

import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs



if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

URL = os.environ['SCHOOL_NOTI_URL']
TOKEN = os.environ['TELEGRAM_TOKEN']
CHAT_ID = os.environ['TELEGRAM_CHAT_ID']
DB_FILE = "ids_db.txt"

def send_message(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID, 
        "text": message, 
        "parse_mode": "HTML", 
        "disable_web_page_preview": False}
    requests.post(url, data=data)

def get_notices():
    global notices
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"}
    res = requests.get(URL, headers=headers)
    soup = BeautifulSoup(res.text, 'html.parser')
    notice_table = soup.find("table", class_="board-table")
    notices = notice_table.select("table.board-table > tbody > tr > td.b-td-left")
    
    # normal_notices = notice_table.select("table.board-table > tbody > tr:not(.b-top-box) > td.b-td-left > div.b-title-box > a")
    return notices


def structify(notices):
    notices_list = []
    for notice in notices:
        title = notice.select_one("div.b-title-box > a")["title"]
        url = URL + notice.select_one("div.b-title-box > a")["href"]
        writer = notice.select_one("div.b-m-con > span.b-writer").text.strip()
        type = notice.select_one("div.b-m-con > span.b-cate").text.strip()
        # date = notice.select_one("div.b-m-con > span.b-date").text.replace(".","-").strip()
        # extra_data = notice.select("div.b-m-con")
        parsed_url = urlparse(url)
        params = parse_qs(parsed_url.query)
        article_id = params.get('articleNo', [''])[0]
        notices_list.append({
            'article_id': article_id,
            'title': title,
            'url': url,
            'writer' : writer,
            'type' : type
        })
    return notices_list

def get_last_id():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return f.read().strip()
    return ""

def save_last_id(new_id):
    with open(DB_FILE, "w") as f:
        f.write(new_id)


if __name__ == "__main__":
    update_notices = get_notices()
    structured_data = structify(update_notices)
    last_id = get_last_id()
    new_posts = []

    for post in structured_data:
        if post['article_id'] == last_id:
            break
        new_posts.append(post)

    if new_posts:
        for post in reversed(new_posts):
            # 날짜와 제목을 포함한 메시지 구성
            message = (
                f"<b>🚨[새 {post['type']} 공지사항]🚨</b>\n"
                f"📌 <b>제목:</b> {post['title']}\n\n"
                f"👤 <b>작성자:</b> {post["writer"]}\n\n"
                f"<a href='{post['url']}'>🔗 게시글 바로가기</a>"
            )
            send_message(message)
            print(f"발송 완료: {post['title']}")

        # 최신 공지 ID 저장
        save_last_id(structured_data[0]['article_id'])
    else:
        print("새로운 공지가 없습니다.")