from fastapi import APIRouter 
from . import google


from . import common, users, layers, google


def setup_routers() -> APIRouter:
    router = APIRouter(prefix="/api")

    router.include_router(google.router, prefix="/google", tags=["Google"])
    router = APIRouter()
    router.include_router(common.router)
    router.include_router(users.router)
    router.include_router(layers.router)
    router.include_router(google.router)

    return router
    