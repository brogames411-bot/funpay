import asyncio
import aiohttp
from bs4 import BeautifulSoup

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.types import Message

# =====================================================
# НАСТРОЙКИ
# =====================================================

BOT_TOKEN = "8991586803:AAHSY-Olyc8SpExGBSLeEYpeiz_dK7gauf8"
CHAT_ID = 561985152

URL = "https://funpay.com/chips/186/"

SERVER_NAME = "№70 Lipetsk"
MAX_PRICE = 30

CHECK_DELAY = 10

# =====================================================

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(
        parse_mode=ParseMode.HTML
    )
)

dp = Dispatcher()

# Вкл / выкл
is_running = True

# Антидубликаты
sent_lots = set()


# =====================================================
# TELEGRAM COMMANDS
# =====================================================

@dp.message(F.text == "/start")
async def start(message: Message):

    await message.answer(
        "🤖 Бот запущен\n\n"
        "/on — включить\n"
        "/off — выключить\n"
        "/status — статус"
    )


@dp.message(F.text == "/off")
async def stop_bot(message: Message):

    global is_running

    is_running = False

    await message.answer("⛔ Мониторинг выключен")


@dp.message(F.text == "/on")
async def start_bot(message: Message):

    global is_running

    is_running = True

    await message.answer("✅ Мониторинг включен")


@dp.message(F.text == "/status")
async def status(message: Message):

    status_text = (
        "🟢 Включен"
        if is_running
        else "🔴 Выключен"
    )

    await message.answer(
        f"Статус: {status_text}"
    )


# =====================================================
# PARSER
# =====================================================

async def get_html():

    headers = {
        "User-Agent": (
            "Mozilla/5.0 "
            "Windows NT 10.0; Win64; x64"
        )
    }

    async with aiohttp.ClientSession(
        headers=headers
    ) as session:

        async with session.get(URL) as response:

            return await response.text()


async def check_lots():

    global sent_lots
    global is_running

    while True:

        try:

            # Если выключен
            if not is_running:
                await asyncio.sleep(1)
                continue

            html = await get_html()

            soup = BeautifulSoup(
                html,
                "html.parser"
            )

            lots = soup.find_all(
                "a",
                class_="tc-item"
            )

            for lot in lots:

                try:

                    text = lot.get_text(
                        " ",
                        strip=True
                    )

                    # Фильтр сервера
                    if SERVER_NAME.lower() not in text.lower():
                        continue

                    # Цена
                    price_block = lot.find(
                        "div",
                        class_="tc-price"
                    )

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

                    # Лимит цены
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

                    unique_id = f"{lot_link}_{price}"

                    # Антидубликат
                    if unique_id in sent_lots:
                        continue

                    sent_lots.add(unique_id)

                    print(
                        f"[+] ЛОТ | "
                        f"{price} ₽ | "
                        f"{seller}"
                    )

                    # Telegram
                    await bot.send_message(
                        CHAT_ID,
                        f"🔥 <b>Дешевый лот найден!</b>\n\n"
                        f"🎮 Сервер: <b>{SERVER_NAME}</b>\n"
                        f"💰 Цена: <b>{price} ₽</b>\n"
                        f"👤 Продавец: <b>{seller}</b>\n\n"
                        f"🔗 {lot_link}"
                    )

                except Exception as e:
                    print("Ошибка лота:", e)

            await asyncio.sleep(CHECK_DELAY)

        except Exception as e:

            print("Ошибка:", e)

            await asyncio.sleep(5)


# =====================================================
# MAIN
# =====================================================

async def main():

    print("Бот запущен")

    parser_task = asyncio.create_task(
        check_lots()
    )

    polling_task = asyncio.create_task(
        dp.start_polling(bot)
    )

    await asyncio.gather(
        parser_task,
        polling_task
    )


if __name__ == "__main__":
    asyncio.run(main())
