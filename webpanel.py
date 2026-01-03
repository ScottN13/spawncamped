import os
import logging
from datetime import datetime
import json
from rich import print as say
from fastapi import FastAPI
from fastapi import APIRouter
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse, PlainTextResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import asyncio
import subprocess
import shared
from main import shutdownBot, isBotOnline

router = APIRouter()
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    print(shared.bot_online)
    status_class = "status-online" if shared.bot_online else "status-offline"
    status_text = "ONLINE" if shared.bot_online else "OFFLINE"

    html = open("templates/index.html").read()
    html = html.replace("{{STATUS_CLASS}}", status_class)
    html = html.replace("{{STATUS_TEXT}}", status_text)

    msg = request.query_params.get("msg")
    if msg:
        html = html.replace("{{MESSAGE}}", msg)
    else:
        html = html.replace("{{MESSAGE}}", "")

    return html

@app.get("/api/status")
async def api_status():
    return JSONResponse({
        isBotOnline
    })

@app.get("/logs", response_class=PlainTextResponse) 
async def logs():
    if not os.path.exists(shared.bot_log_file_path):
        return PlainTextResponse("No logs found.")
    
    return PlainTextResponse(
        open(shared.bot_log_file_path).read(),
        media_type="text/plain"
    )

@app.get("/panel_logs")
async def getPanelLogs():
    if not os.path.exists(shared.panel_log_file_path):
        return PlainTextResponse("No logs found.")
    
    return PlainTextResponse(
        open(shared.panel_log_file_path).read(),
        media_type="text/plain"
    )

@app.get("/shutdown_bot")
async def shutdown_bot():
    if shared.bot_online:
        await shutdownBot()
        shared.bot_online = False
    return RedirectResponse("/")

@app.get("/start_bot")
async def start():
    if not shared.bot_online:
        asyncio.create_task(shared.start_bot())
    return RedirectResponse("/")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)