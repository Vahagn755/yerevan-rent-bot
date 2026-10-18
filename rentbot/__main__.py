import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, MenuButtonCommands, MenuButtonWebApp, WebAppInfo

from .config import load_config
from .db import Database
from .handlers import all_routers
from .middlewares import UserMiddleware
from .texts import t

COMMANDS = {
    "hy": [("start", "Սկսել"), ("filter", "Իմ ֆիլտրը"), ("post", "Տեղադրել հայտարարություն"),
           ("my", "Իմ հայտարարությունները"), ("pause", "Դադարեցնել ծանուցումները"),
           ("resume", "Միացնել ծանուցումները"), ("lang", "Լեզու"), ("help", "Օգնություն")],
    "ru": [("start", "Начать"), ("filter", "Мой фильтр"), ("post", "Разместить объявление"),
           ("my", "Мои объявления"), ("pause", "Пауза уведомлений"),
           ("resume", "Включить уведомления"), ("lang", "Язык"), ("help", "Помощь")],
    "en": [("start", "Start"), ("filter", "My filter"), ("post", "Post a listing"),
           ("my", "My listings"), ("pause", "Pause notifications"),
           ("resume", "Resume notifications"), ("lang", "Language"), ("help", "Help")],
}


async def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    cfg = load_config()
    db = Database(cfg.db_path)
    await db.connect()

    bot = Bot(cfg.token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage(), db=db, cfg=cfg)
    dp.update.outer_middleware(UserMiddleware())
    dp.include_routers(*all_routers())

    await bot.set_my_commands([BotCommand(command=c, description=d) for c, d in COMMANDS["hy"]])
    for code in ("ru", "en"):
        await bot.set_my_commands([BotCommand(command=c, description=d) for c, d in COMMANDS[code]],
                                  language_code=code)

    runner = None
    if cfg.web_port:
        from .webapp import start_web
        runner = await start_web(db, cfg, bot)
    if cfg.webapp_url:
        # the button left of the message field opens the Mini App
        await bot.set_chat_menu_button(menu_button=MenuButtonWebApp(
            text=t("open_app", "hy"), web_app=WebAppInfo(url=cfg.webapp_url)))
    else:
        await bot.set_chat_menu_button(menu_button=MenuButtonCommands())

    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        if runner:
            await runner.cleanup()
        await db.close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
