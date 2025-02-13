import asyncio

from config import bot, dp
from handlers import router


async def main():
    dp.include_router(router)
    await dp.start_polling(bot, handle_as_tasks=False, allowed_updates=dp.resolve_used_update_types())


if __name__ == '__main__':
    asyncio.run(main())
