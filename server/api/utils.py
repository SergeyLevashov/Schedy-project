from fastapi import Request, HTTPException
import logging
from functools import lru_cache
from aiogram.utils.web_app import WebAppInitData, safe_parse_webapp_init_data
from db.models.user import User
from config_reader import config


def auth(request: Request) -> WebAppInitData:
    try:
        auth_string = request.headers.get("initData", None)
        if auth_string:
            data = safe_parse_webapp_init_data(
                config.BOT_TOKEN.get_secret_value(), 
                auth_string
            )
            return data
        else:
            raise HTTPException(401, {"error": "Unauthorized"})
    except Exception:
        raise HTTPException(401, {"error": "Unauthorized"})
    
async def check_user(user_id: int) -> User:
    user = await User.filter(id=user_id).first()
    if not user:
        raise HTTPException(404, {"error": "User not found"})
    return user

logger = logging.getLogger(__name__)

async def validate_init_data(request):
    try:
        auth_string = request.headers.get("initData", None)
        logger.debug(f"Validating initData: {auth_string[:20]}...")
        # ...rest of the function
    except Exception as e:
        logger.error(f"Authentication failed: {str(e)}")
        raise

@lru_cache(maxsize=100)
async def get_cached_user(user_id: int) -> User:
    return await check_user(user_id)