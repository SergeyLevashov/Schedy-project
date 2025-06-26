from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse

from aiogram.types import LabeledPrice, Update
from aiogram.methods import CreateInvoiceLink
from aiogram.utils.web_app import WebAppInitData

from config_reader import config, dp, bot
from .utils import auth

router = APIRouter()


@router.post("/webhook")
async def webhook(request: Request) -> None:
    update = Update.model_validate(await request.json(), context={"bot": bot})
    await dp.feed_update(bot, update)


@router.post("/api/donate", response_class=JSONResponse)
async def donate(request: Request, auth_data: WebAppInitData = Depends(auth)) -> JSONResponse:
    data = await request.json()
    invoice_link = await bot(
        CreateInvoiceLink(
            title="schedy",
            description="Make my life better!",
            payload="",
            currency="XTR",
            prices=[LabeledPrice(label="XTR", amount=data["amount"])]
        )
    )
    
    return JSONResponse({"invoice_link": invoice_link})