import os
import tweepy
import time
import requests
from pocketbase import PocketBase
import logging
from dotenv import load_dotenv

load_dotenv()

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

bearer_token = os.getenv("BEARER_TOKEN")
consumer_key = os.getenv("API_KEY")
consumer_secret = os.getenv("API_SECRET")
access_token = os.getenv("ACCESS_TOKEN")
access_token_secret = os.getenv("ACCESS_TOKEN_SECRET")
tg_tag = os.getenv("TG_TAG")
tg_channel = os.getenv("TG_CHANNEL")
web_url = os.getenv("WEB_URL")
db_url = os.getenv("DB_URL")
admin_email = os.getenv("ADMIN_EMAIL")
admin_password = os.getenv("ADMIN_PASSWORD")
pb_client = PocketBase(db_url)
admin_token = pb_client.admins.auth_with_password(admin_email, admin_password).token
headers = {"Authorization": admin_token}

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth, wait_on_rate_limit=True)

tweet_client = tweepy.Client(
    bearer_token,
    consumer_key,
    consumer_secret,
    access_token,
    access_token_secret,
    wait_on_rate_limit=True,
)


def fetch_db():
    admin_token = pb_client.admins.auth_with_password(admin_email, admin_password).token

    headers = {"Authorization": admin_token}

    response = requests.get(
        f"{db_url}/api/collections/posts/records?sort=-posted_on&fields=id,post_url,title,images,tag,posted_on",
        headers=headers,
    )

    response = response.json()["items"][0:3]

    return response


def download_image(urls):
    if not os.path.exists("./images"):
        directory = "images"
        parent_dir = "./"
        path = os.path.join(parent_dir, directory)
        os.mkdir(path)
    headers = {
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:32.0) Gecko/20100101 Firefox/32.0",
    }
    i = 1
    for url in urls:
        filename = f"./images/preupload_img-{i}.jpg"
        response = requests.get(url, headers=headers, stream=True)
        if response.status_code == 200:
            with open(filename, "wb") as image:
                image.write(response.content)
        else:
            print(f"Cannot download url: {url}")
            break

        print(f"{filename} has been downloaded!")
        i += 1


def get_media_id():
    media_id = []

    images = os.listdir("./images")
    for image in images:
        media_id.append(api.media_upload(filename=f"./images/{image}").media_id_string)
        os.remove(f"./images/{image}")
    return media_id


def check_is_posted(req):
    response = requests.get(
        f"{db_url}/api/collections/posts/records?filter=({req}=false)&fields=id,title,images,post_url,tag,{req}",
        headers=headers,
    ).json()

    items = response["items"]
    return items


def tweet_post(item):
    images = item["images"][0:4]
    title = item["title"]

    tag = f"#{title} {tg_tag}"

    text = f"{title.capitalize()} \n\n{web_url} \n\nTG: https://t.me/{tg_channel} \n\n{tag}"

    download_image(images)

    media_ids = get_media_id()

    tweet_client.create_tweet(text=text, media_ids=media_ids)

    logging.info("Post tweeted")


def check_and_post():
    not_posted = check_is_posted("twitter")

    if len(not_posted) > 0:
        for item in not_posted:
            tweet_post(item)
            pb_client.collection("posts").update(
                id=item["id"], body_params={"twitter": True}
            )
            time.sleep(5)

    else:
        logging.info("No new posts to post")


def main():
    check_and_post()


if __name__ == "__main__":
    main()
