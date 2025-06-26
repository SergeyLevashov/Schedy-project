from enum import Enum, auto
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from aiogram.utils.web_app import WebAppInitData

from .utils import auth, check_user


class Layer(str, Enum):
    HOME = "HOME"
    CALENDAR = "CALENDAR"
    SETTINGS = "SETTINGS"
    PROFILE = "PROFILE"


router = APIRouter(prefix="/api/layers", dependencies=[Depends(auth)])


@router.post("/set/{layer_name}")
async def set_layer(
    layer_name: Layer, request: Request, auth_data: WebAppInitData = Depends(auth)
):
    user = await check_user(auth_data.user.id)
    # Here you would typically save the user's current layer to the database
    # For example:
    # user.current_layer = layer_name.value
    # await user.save()

    return JSONResponse(
        {"status": "ok", "layer": layer_name.value}
    ) 