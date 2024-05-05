import logging
import requests
import time
from pocketbase import PocketBase
from telegram import Update, InputMediaPhoto
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes
from dotenv import load_dotenv
import os

load_dotenv()


# Enable logging

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)
TOKEN = os.getenv("TG_TOKEN")

url = os.getenv("DB_URL")
client = PocketBase(url)
chat_id = os.getenv("CHAT_ID")
admin_email = os.getenv("ADMIN_EMAIL")
admin_password = os.getenv("ADMIN_PASSWORD")

admin_token = client.admins.auth_with_password(admin_email, admin_password).token

headers = {"Authorization": admin_token}


async def dev_mode(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.job_queue.run_once(check_and_post, when=0)
    await update.message.reply_text("Bot Started! Dev Mode")

    return


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.job_queue.run_repeating(check_and_post, interval=900, first=0)
    await update.message.reply_text("Bot Started! It will send messsages every 15 mins")


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await context.job_queue.stop(wait=True)
    await update.message.reply_text("Bot has stopped.")


def check_is_posted(req):
    response = requests.get(
        f"{url}/api/collections/posts/records?filter=({req}=false)&fields=id,title,images,post_url,tag,{req}",
        headers=headers,
    ).json()

    items = response["items"]
    return items


async def send_media(item, context):
    media_group = []
    title = item["title"]
    images = item["images"][0:4]
    tag = item["tag"]
    post_url = item["post_url"]

    caption_text = f"Onlyfans.com - {title} {tag} \n\n{post_url}"

    for i, med in enumerate(images):
        media_group.append(
            InputMediaPhoto(
                media=med,
                caption=caption_text if i == 0 else "",
                parse_mode=ParseMode.HTML,
            )
        )
    await context.bot.send_media_group(chat_id, media_group, disable_notification=True)

    media_group.clear()


async def check_and_post(context: ContextTypes.DEFAULT_TYPE) -> None:
    # have not posted in tg yet
    not_posted = check_is_posted("telegram")

    if len(not_posted) > 0:
        items = not_posted[0:3]
        for item in not_posted:
            await send_media(item, context)
            client.collection("posts").update(
                id=item["id"], body_params={"telegram": True}
            )
            time.sleep(5)
    else:
        logging.info("No new posts to post")


def main() -> None:
    """Run bot."""

    # Create the Application and pass it your bot's token.

    application = Application.builder().token(TOKEN).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("dev", dev_mode))
    application.add_handler(CommandHandler("stop", stop))

    # Run the bot until the user presses Ctrl-C

    application.run_polling(allowed_updates=Update.ALL_TYPES)
    return


if __name__ == "__main__":
    main()
