import base64
import requests
import os
from dotenv import load_dotenv

load_dotenv()

# Replace the placeholders with your actual WordPress REST API credentials and post data:
base_url = os.getenv("BASE_URL")
user = os.getenv("WP_USER_TEST")
password = os.getenv("WP_KEY_TEST")
credentials = user + ":" + password
token = base64.b64encode(credentials.encode())
headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.106 Safari/537.36 OPR/38.0.2220.41",
    "Authorization": "Basic " + token.decode("utf-8"),
    "Content-Type": "application/json",
}


def upload_img():
    url = f"{base_url}/wp-json/wp/v2/media"
    data = open("./uploads/1.jpg", "rb").read()
    fileName = os.path.basename("1.jpg")
    res = requests.post(
        url=url,
        data=data,
        headers={
            "Content-Type": "image/jpg",
            "Authorization": "Basic " + token.decode("utf-8"),
            "Content-Disposition": "attachment; filename=%s" % fileName,
        },
    )
    newDict = res.json()
    return {"id": newDict.get("id"), "link": newDict.get("link")}


def main():
    media_info = upload_img()
    post_title = "CAT CATCATCAT"
    medias = [
        f"https://{base_url}/wp-content/uploads/2023/12/1.jpg",
        f"https://{base_url}/wp-content/uploads/2023/12/1.jpg",
        f"https://{base_url}/wp-content/uploads/2023/12/1.jpg",
        f"https://{base_url}/wp-content/uploads/2023/12/1.jpg",
    ]
    post_content = f'SOME THING IS GONNA CHANGE\n\n\n<figure class="wp-block-gallery has-nested-images columns-default is-cropped wp-block-gallery-1 is-layout-flex wp-block-gallery-is-layout-flex">\n<figure class="wp-block-image size-large"><img loading="lazy" decoding="async" width="900" height="900" data-id="17" src={medias[0]} alt="" /></figure>\n\n\n\n<figure class="wp-block-image size-large"><img loading="lazy" decoding="async" width="900" height="900" data-id="17" src={medias[1]} alt="" /></figure>\n\n\n\n<figure class="wp-block-image size-large"><img loading="lazy" decoding="async" width="300" height="200" data-id="12" src={medias[2]} alt="" class="wp-image-12"/></figure>\n</figure>'
    categories = [1, 2]  # Replace with the IDs of the desired categories.
    tags = [1, 2]  # Replace with the names of the desired tags.
    data = {
        "title": post_title,
        "content": post_content,
        "featured_media": media_info["id"],
        "categories": categories,
        "tags": tags,
        "excerpt": "test",
        "status": "publish",
    }

    url = f"{base_url}/wp-json/wp/v2/posts"
    # response = requests.post(url=url, headers=headers, data=json.dumps(data))
    # print(response)


if __name__ == "__main__":
    main()
