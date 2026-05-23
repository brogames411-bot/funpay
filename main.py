import asyncio
import aiohttp
from bs4 import BeautifulSoup

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.types import Message

BOT_TOKEN = "8991586803:AAHSY-Olyc8SpExGBSLeEYpeiz_dK7gauf8"
CHAT_ID = "561985152"

URL = "https://funpay.com/chips/186/"

SERVER_NAME = "№70 Lipetsk"
MAX_PRICE = 30

CHECK_DELAY = 10

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(
        parse_mode=ParseMode.HTML
    )
)

dp = Dispatcher()

is_running = True
sent_lots = set()


@dp.message(F.text == "/start")
async def start(message: Message):

    await message.answer(
        "🤖 Бот запущен\n\n"
        "/on — включить мониторинг\n"
        "/off — выключить мониторинг\n"
        "/status — статус бота"
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


async def get_html():

    headers = {
        "User-Agent": (
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "Chrome/122.0.0.0 Safari/537.36"
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

    print("ПАРСЕР РАБОТАЕТ")

    while True:

        try:

            if not is_running:
                await asyncio.sleep(1)
                continue

            html = await get_html()

            soup = BeautifulSoup(
                html,
                "html.parser"
            )

            lots = soup.select("a.tc-item")

            print(f"Найдено лотов: {len(lots)}")

            for lot in lots:

                try:

                    text = lot.get_text(
                        " ",
                        strip=True
                    )

                    if "lipetsk" not in text.lower():
                        continue

                    price = None

                    for element in lot.find_all():

                        element_text = (
                            element.get_text(strip=True)
                        )

                        if "₽" in element_text:

                            try:

                                clean_price = (
                                    element_text
                                    .replace("₽", "")
                                    .replace(" ", "")
                                    .replace(",", ".")
                                )

                                price = float(clean_price)
                                break

                            except:
                                pass

                    if price is None:
                        continue

                    print("ЦЕНА:", price)

                    if price > MAX_PRICE:
                        continue

                    print("ДЕШЕВЫЙ ЛОТ НАЙДЕН")

                    seller = "Unknown"

                    seller_block = lot.select_one(
                        ".media-user-name"
                    )

                    if seller_block:
                        seller = (
                            seller_block.text.strip()
                        )

                    href = lot.get("href")

                    if not href:
                        continue

                    lot_link = (
                        "https://funpay.com"
                        + href
                    )

                    unique_id = (
                        f"{lot_link}_{price}"
                    )

                    if unique_id in sent_lots:
                        continue

                    sent_lots.add(unique_id)

                    print("ОТПРАВЛЯЮ В TELEGRAM")

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

            print("Ошибка парсера:", e)

            await asyncio.sleep(5)


async def main():

    print("Бот запущен")

    asyncio.create_task(
        check_lots()
    )

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
