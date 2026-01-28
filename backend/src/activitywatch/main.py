import json
from fastapi import FastAPI, Request
from datetime import datetime
from typing import List, Dict
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from src.activitywatch.api.auth.router import router as auth_router
from src.activitywatch.api.device.router import router as device_router

app = FastAPI(title="ActivityWatch Receiver", version="1.0")
app.include_router(auth_router)
app.include_router(device_router)
origins = ["*", "http://localhost:5173"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
received_data = []


@app.get("/")
async def root():
    return {
        "message": "ActivityWatch Receiver API",
        "endpoints": {
            "POST /receive": "Принять данные из ActivityWatch",
            "GET /data": "Посмотреть все полученные данные",
            "GET /clear": "Очистить данные",
        },
        "received_count": len(received_data),
    }


if __name__ == "__main__":
    print("🚀 ActivityWatch Receiver запущен!")
    print("📡 Адрес: http://localhost:8000")
    print("📝 Документация: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
