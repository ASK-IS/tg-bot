import asyncio

from config import bot, dp
from handlers import admin_router, chat_router, router

# from aiogram.methods import DeleteWebhook


async def main():
    dp.include_routers(admin_router, chat_router, router)
    # await bot(DeleteWebhook(drop_pending_updates=True))
    await dp.start_polling(bot, handle_as_tasks=False, allowed_updates=dp.resolve_used_update_types())


if __name__ == '__main__':
    asyncio.run(main())
