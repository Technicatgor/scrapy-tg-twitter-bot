from mastodon import Mastodon
import time
import io
import requests
import config
from pocketbase import PocketBase
import logging
from dotenv import load_dotenv
import os

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

instance_domain = "mastodon.world"
db_url = os.getenv("DB_URL")
tg_channel = os.getenv("TG_CHANNEL")
tg_tag = os.getenv("TG_TAG")

pb_client = PocketBase(db_url)


admin_token = pb_client.admins.auth_with_password(
    os.getenv("ADMIN_EMAIL"), os.getenv("ADMIN_PASSWORD")
).token
headers = {"Authorization": admin_token}


def fetch_db():
    response = requests.get(
        f"{db_url}/api/collections/posts/records?sort=-posted_on&fields=id,post_url,title,images,tag,posted_on",
        headers=headers,
    )
    response = response.json()["items"][0:3]
    return response


# Create an instance of the Mastodon class
def login():
    token_data = {
        "grant_type": "password",
        "client_id": os.getenv("MASTODON_CLIENT_KEY"),
        "client_secret": os.getenv("MASTODON_CLIENT_SECRET"),
        "username": os.getenv("MASTODON_USERNAME"),
        "password": os.getenv("MASTODON_PASSWORD"),
        "scope": "read write follow",
    }
    response = requests.post(f"https://{instance_domain}/oauth/token", data=token_data)
    response_data = response.json()
    return response_data["access_token"]


def download_image(url):
    response = requests.get(url)
    return io.BytesIO(response.content)


def upload_image(access_token, image_url):
    headers = {"Authorization": f"Bearer {access_token}"}
    image_data = download_image(image_url)
    files = {"file": image_data}
    response = requests.post(
        f"https://{instance_domain}/api/v2/media", headers=headers, files=files
    )
    response_data = response.json()
    print(response_data)

    return response_data["id"]


def send_posts(item):
    images = item["images"][0]
    title = item["title"].capitalize()

    access_token = login()
    media_id = upload_image(access_token, images)
    status_text = (
        f"{title.capitalize()}\n\nTG: https://t.me/{tg_channel}\n\n#{title} {tg_tag}"
    )
    headers = {"Authorization": f"Bearer {access_token}"}
    data = {
        "status": status_text,
        "visibility": "public",
        "sensitive": True,
    }
    data["media_ids[]"] = media_id

    response = requests.post(
        f"https://{instance_domain}/api/v1/statuses",
        headers=headers,
        data=data,
    )
    logging.info(f'{item["title"]} has been posted.')
    if response.status_code != 200:
        raise Exception


def check_is_posted(req):
    response = requests.get(
        f"{db_url}/api/collections/posts/records?filter=({req}=false)&fields=id,title,images,post_url,tag,{req}",
        headers=headers,
    ).json()

    items = response["items"]
    return items


def check_and_post():
    not_posted = check_is_posted("mastodon")

    if len(not_posted) > 0:
        for item in not_posted:
            send_posts(item)
            pb_client.collection("posts").update(
                id=item["id"], body_params={"mastodon": True}
            )
            time.sleep(5)
    else:
        logging.info("No new posts to post")


def main():
    check_and_post()


if __name__ == "__main__":
    main()
