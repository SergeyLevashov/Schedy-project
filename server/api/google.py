# /api/google.py

from fastapi import APIRouter, Depends, Request, Header
from fastapi.responses import RedirectResponse
from google_auth_oauthlib.flow import Flow

from config_reader import config
from db.models.user import User
from db.models.google_token import GoogleToken
from utils.telegram_auth import get_user_from_init_data

router = APIRouter()

SCOPES = ['https://www.googleapis.com/auth/calendar']

# Собираем конфигурацию для клиента Google из нашего config_reader.py
GOOGLE_CLIENT_CONFIG = {
    "web": {
        "client_id": config.GOOGLE_CLIENT_ID.get_secret_value(),
        "project_id": "schedy-ai-assistant", # Можете поменять
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_secret": config.GOOGLE_CLIENT_SECRET.get_secret_value(),
        "redirect_uris": [config.GOOGLE_REDIRECT_URI]
    }
}

@router.get("/auth/url")
async def get_google_auth_url(
    user: User = Depends(get_user_from_init_data),
    x_tg_init_data: str = Header(...)
):
    """
    Создает URL для аутентификации Google.
    Передаем initData в параметре 'state' для идентификации пользователя в колбэке.
    """
    flow = Flow.from_client_config(
        client_config=GOOGLE_CLIENT_CONFIG,
        scopes=SCOPES,
        redirect_uri=config.GOOGLE_REDIRECT_URI
    )

    authorization_url, state = flow.authorization_url(
        access_type='offline',
        prompt='consent',
        state=x_tg_init_data  # Используем initData как state для безопасности
    )
    return {"auth_url": authorization_url}

@router.get("/oauth2callback")
async def google_oauth2_callback(request: Request, state: str, code: str):
    """
    Обрабатывает редирект от Google после аутентификации.
    """
    # 1. Проверяем state, чтобы убедиться, что это тот же пользователь
    user = await get_user_from_init_data(state)

    try:
        # 2. Обмениваем временный 'code' на постоянные 'credentials'
        flow = Flow.from_client_config(
            client_config=GOOGLE_CLIENT_CONFIG,
            scopes=SCOPES,
            redirect_uri=config.GOOGLE_REDIRECT_URI
        )
        flow.fetch_token(code=code)
        credentials = flow.credentials

        # 3. Сохраняем токен в базу данных
        token_data = {
            "token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "token_uri": credentials.token_uri,
            "client_id": credentials.client_id,
            "client_secret": credentials.client_secret,
            "scopes": credentials.scopes,
        }
        
        await GoogleToken.update_or_create(
            user=user,
            defaults=token_data
        )

        # 4. Перенаправляем пользователя обратно в приложение с сообщением об успехе
        return RedirectResponse(f"{config.WEBAPP_URL}/?auth_status=success")

    except Exception as e:
        print(f"Ошибка при обработке колбэка Google: {e}")
        # Перенаправляем с сообщением об ошибке
        return RedirectResponse(f"{config.WEBAPP_URL}/?auth_status=error")