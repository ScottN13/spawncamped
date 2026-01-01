import os
import logging
from datetime import datetime
import json
from rich import print as say
from fastapi import APIRouter
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse, PlainTextResponse
import asyncio
import subprocess
import shared

router = APIRouter()

@router.get("/")
async def home(request: Request):
    status_class = "status-online" if shared.bot_online else "status-offline"
    status_text = "ONLINE" if shared.bot_online else "OFFLINE"

    html = open("templates/index.html").read()
    html = html.replace("{{STATUS_CLASS}}", status_class)
    html = html.replace("{{STATUS}}", status_text)

    msg = request.query_params.get("msg")
    if msg:
        html = html.replace("{{MESSAGE}}", msg)
    else:
        html = html.replace("{{MESSAGE}}", "")

    return html

@router.get("/logs") 
async def logs():
    if not os.path.exists(shared.log_file_path):
        return PlainTextResponse("No logs found.")
    
    return PlainTextResponse(
        open(shared.log_file_path).read(),
        media_type="text/plain"
    )

@router.get("/shutdown_bot")
async def shutdown_bot():
    if shared.bot_online:
        await bot.close()
        shared.bot_online = False
    return RedirectResponse("/")

@router.get("/start_bot")
async def start():
    if not shared.bot_online:
        asyncio.create_task(shared.start_bot())
    return RedirectResponse("/")