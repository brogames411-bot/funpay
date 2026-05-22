# main.py

import asyncio
import aiohttp
from bs4 import BeautifulSoup
from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

# =====================================================
# НАСТРОЙКИ
# =====================================================

BOT_TOKEN = "8991586803:AAHSY-Olyc8SpExGBSLeEYpeiz_dK7gauf8"
CHAT_ID = "561985152"

# Black Russia
URL = "https://funpay.com/chips/186/"

# Сервер и лимит цены
SERVER_NAME = "№70 Lipetsk"
MAX_PRICE = 30

# Проверка каждые N секунд
CHECK_DELAY = 10

# =====================================================

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(
        parse_mode=ParseMode.HTML
    )
)

# Чтобы не слать одинаковые лоты
sent_lots = set()


async def get_html():

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36"
        )
    }

    async with aiohttp.ClientSession(headers=headers) as session:

        async with session.get(URL) as response:

            return await response.text()


async def check_lots():

    global sent_lots

    while True:

        try:

            html = await get_html()

            soup = BeautifulSoup(html, "html.parser")

            lots = soup.find_all("a", class_="tc-item")

            for lot in lots:

                try:

                    # Весь текст лота
                    text = lot.get_text(" ", strip=True)

                    # Только Lipetsk
                    if SERVER_NAME.lower() not in text.lower():
                        continue

                    # Цена
                    price_block = lot.find("div", class_="tc-price")

                    if not price_block:
                        continue

                    price_text = (
                        price_block.text
                        .replace("₽", "")
                        .replace(" ", "")
                        .replace(",", ".")
                        .strip()
                    )

                    price = float(price_text)

                    # Проверка цены
                    if price > MAX_PRICE:
                        continue

                    # Продавец
                    seller_block = lot.find(
                        "div",
                        class_="media-user-name"
                    )

                    seller = (
                        seller_block.text.strip()
                        if seller_block
                        else "Unknown"
                    )

                    # Ссылка
                    lot_link = (
                        "https://funpay.com"
                        + lot.get("href")
                    )

                    # Уникальный ID
                    unique_id = f"{lot_link}_{price}"

                    if unique_id in sent_lots:
                        continue

                    sent_lots.add(unique_id)

                    # Лог
                    print(
                        f"[+] НАЙДЕН ЛОТ | "
                        f"{price} ₽ | "
                        f"{seller}"
                    )

                    # Telegram сообщение
                    text_message = (
                        f"🔥 <b>Дешевый лот найден!</b>\n\n"
                        f"🎮 Сервер: <b>{SERVER_NAME}</b>\n"
                        f"💰 Цена: <b>{price} ₽</b>\n"
                        f"👤 Продавец: <b>{seller}</b>\n\n"
                        f"🔗 {lot_link}"
                    )

                    await bot.send_message(
                        CHAT_ID,
                        text_message
                    )

                except Exception as e:
                    print("Ошибка лота:", e)

            await asyncio.sleep(CHECK_DELAY)

        except Exception as e:

            print("Ошибка проверки:", e)

            await asyncio.sleep(5)


async def main():

    print("Бот запущен")

    await check_lots()


if __name__ == "__main__":
    asyncio.run(main())