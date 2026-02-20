import os
import sys
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
from dotenv import load_dotenv

load_dotenv()

URL = os.environ['SCHOOL_NOTI_URL']
TOKEN = os.environ['TELEGRAM_TOKEN']
CHAT_ID = os.environ['TELEGRAM_CHAT_ID']
DB_FILE = "ids_db.txt"

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def send_message(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
    return requests.post(url, data=data)

def get_notices():
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"}
    res = requests.get(URL, headers=headers)
    soup = BeautifulSoup(res.text, 'html.parser')

    rows = soup.select("table.board-table > tbody > tr")
    normal_rows = [row for row in rows if not row.select_one("td.b-top-box")]
    notices = [row.select_one("td.b-td-left") for row in normal_rows if row.select_one("td.b-td-left")]

    return notices

def structify(notices):
    notices_list = []
    base_url = URL

    for notice in notices:
        anchor = notice.select_one("div.b-title-box > a")
        if not anchor:
            continue

        title = anchor["title"]
        link = base_url + anchor["href"]
        writer = notice.select_one("div.b-m-con > span.b-writer").text.strip()
        category = notice.select_one("div.b-m-con > span.b-cate").text.strip()

        parsed_url = urlparse(link)
        params = parse_qs(parsed_url.query)
        article_id = params.get('articleNo', [''])[0]

        notices_list.append({
            'article_id': article_id,
            'title': title,
            'url': link,
            'writer': writer,
            'type': category
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
        if last_id and int(post['article_id']) <= int(last_id):
            continue
        new_posts.append(post)

    if new_posts:
        new_posts.sort(key=lambda x: int(x['article_id']))
        for post in new_posts:
            print(f"  📨 발송 중: [{post['type']}] {post['title']}")
            message = (
                f"<b>🚨 [새 {post['type']} 공지사항] 🚨</b>\n\n"
                f"📌 <b>제목:</b> {post['title']}\n"
                f"👤 <b>작성자:</b> {post['writer']}\n\n"
                f"<a href='{post['url']}'>🔗 게시글 바로가기</a>"
            )
            send_message(message)
        save_last_id(str(max(int(p['article_id']) for p in structured_data)))