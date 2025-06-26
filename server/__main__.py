from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from api import setup_routers as setup_api_routers
from config_reader import app, config, ROOT_DIR
from api.voice import router as voice_router



app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(setup_api_routers())
app.include_router(voice_router)
@app.get("/", response_class=FileResponse)
async def read_root():
    return str(ROOT_DIR / "templates" / "index.html")

if __name__ == "__main__":
    print(f"Starting server at http://{config.APP_HOST}:{config.APP_PORT}")
    print(f"Webapp URL: {config.WEBAPP_URL}")
    print(f"Google Redirect URI: {config.GOOGLE_REDIRECT_URI}")
    uvicorn.run(app, host="0.0.0.0", port=config.APP_PORT)