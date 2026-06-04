from aiogram import Dispatcher
from .start import router as start_router
from .registration import router as reg_router
from .menu import router as menu_router
from .chat import router as chat_router
from .premium import router as premium_router
from .admin import router as admin_router
from .settings import router as settings_router


def register_all_handlers(dp: Dispatcher):
    dp.include_router(start_router)
    dp.include_router(reg_router)
    dp.include_router(menu_router)
    dp.include_router(chat_router)
    dp.include_router(premium_router)
    dp.include_router(admin_router)
    dp.include_router(settings_router)
