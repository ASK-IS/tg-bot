import asyncio

from aiogram.methods import DeleteWebhook

from config import bot, dp
from handlers import admin_router, router


async def main():
    dp.include_routers(admin_router, router)
    # await bot(DeleteWebhook(drop_pending_updates=True))
    await dp.start_polling(bot, handle_as_tasks=False, allowed_updates=dp.resolve_used_update_types())


if __name__ == '__main__':
    asyncio.run(main())
