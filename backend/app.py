import requests
from selectolax.parser import HTMLParser
from pocketbase import PocketBase
import time
import logging
from dotenv import load_dotenv
import os

load_dotenv()
# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)


wp_url = os.getenv("WP_URL")
db_url = os.getenv("DB_URL")

admin_email = os.getenv("ADMIN_EMAIL")
admin_password = os.getenv("ADMIN_PASSWORD")

db_client = PocketBase(db_url)

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0",
    "Content-Type": "application/json",
}


def auth_db():
    admin_data = db_client.admins.auth_with_password(admin_email, admin_password)
    token = admin_data.token
    return token


def fetch_db(token):
    params = "?sort=-posted_on&fields=title,images,post_url,tag,posted_on"
    headers = {
        "Authorization": token,
    }

    res = requests.get(
        url=f"{db_url}/api/collections/posts/records{params}",
        headers=headers,
    )
    logging.info(f"Connected DB (POSTS) - HTTP: {res.status_code}")
    return res.json()["items"]


def extract_html(text):
    html = HTMLParser(text)
    img_tags = html.css("img")
    return [
        image.css_first("img").attributes["src"].split("?")[0] + "?w=828&amp;ssl=1"
        for image in img_tags
    ]


def get_posts(url, **kwargs):
    if kwargs.get("page"):
        base_url = url + "?page=" + str(kwargs.get("page"))
        res = requests.get(base_url, headers=headers)
        logging.info(f"Connected WP API - HTTP: {res.status_code}")
        posts = res.json()
        items = []

        for post in posts:
            item = {
                "title": post["title"]["rendered"].split(" ")[-1].capitalize(),
                "post_url": post["link"],
                "tag": f'#{post["title"]["rendered"].split(" ")[-1]}',
                "images": extract_html(post["content"]["rendered"].split("</p>")[0]),
                # "images": extract_html(post["content"]["rendered"].split("<p>")[-1]),
                "posted_on": post["date"] + "+08:00",
            }

            items.append(item)
        return items
    else:
        None


def insert_data(new_posts):
    for post in new_posts:
        logging.info(post["title"] + "has been inserted!")
        db_client.collection("posts").create(post)
        time.sleep(0.2)
    logging.info("Process Completed!")


def data_validate(result, db_data):
    unique_item = list(
        set([post["post_url"] for post in result])
        - set([post["post_url"] for post in db_data])
    )
    if len(unique_item) > 0:
        return [item for item in result if item not in db_data]
    else:
        None


def main():
    # auth
    token = auth_db()
    logging.info("Getting posts......")
    # get wp posts api
    all_posts = []
    for x in range(1, 2):
        print(f"Gathering page{x}")

        wp_posts = get_posts(wp_url, page=x)
        if wp_posts == False:
            break
        all_posts.extend(wp_posts)

    # get db data
    db_data = fetch_db(token)

    # data validate
    new_posts = data_validate(all_posts, db_data)

    # If have new posts then insert data
    if new_posts:
        insert_data(new_posts)
    else:
        logging.info("No new posts were found!")


if __name__ == "__main__":
    main()
