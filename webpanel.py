import os
import logging
from datetime import datetime
import time
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

from main import shutdownBot, isBotOnline

router = APIRouter()
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
logger = logging.getLogger("app.requests")
handler = logging.FileHandler(filename='logs/webpanel.log', encoding='utf-8', mode='w')
bot_log_file_path = "logs/discord.log"
panel_log_file_path = "logs/webpanel.log"
bot_online = ""

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()

    response = await call_next(request)

    duration = time.time() - start
    client_ip = request.client.host if request.client else "unknown"

    logger.info(
        "%s %s %s %d %.2fms",
        client_ip,
        request.method,
        request.url.path,
        request.scope["http_version"],
        response.status_code,
        duration * 1000,
    )

    return response



@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    # print(sharbot_online)
    status_class = "status-online" if bot_online else "status-offline"
    status_text = "ONLINE" if bot_online else "OFFLINE"

    html = open("templates/index.html").read()
    html = html.replace("{{STATUS_CLASS}}", status_class)
    html = html.replace("{{STATUS_TEXT}}", status_text)

    msg = request.query_params.get("msg")
    if msg:
        html = html.replace("{{MESSAGE}}", msg)
    else:
        html = html.replace("{{MESSAGE}}", "")

    displayDiv = request.query_params.get("displayDiv")
    if displayDiv:
        html = html.replace("{{LOGS}}", displayDiv)
    else:
        html = html.replace("{{LOGS}}", "")

    return html
    

@app.get("/api/status")
async def api_status():
    return JSONResponse({
        {"online": isBotOnline}
    })

@app.get("/logs", response_class=RedirectResponse) 
async def logs():
    if not os.path.exists(bot_log_file_path):
        return RedirectResponse(f"/?displayDiv=No logs found.")
    else:
        message = open(bot_log_file_path).read()
        return RedirectResponse(f"/?displayDiv={message}")

@app.get("/panel_logs")
async def getPanelLogs():
    if not os.path.exists(panel_log_file_path):
        return PlainTextResponse("No logs found.")
    
    return PlainTextResponse(
        open(panel_log_file_path).read(),
        media_type="text/plain"
    )

@app.get("/shutdown_bot")
async def shutdown_bot():
    status = await shutdownBot()
    if status == True:
        message = "Successfully shut down bot."
        return RedirectResponse(f"/?msg={message}")
    else: 
        return RedirectResponse("/")

"""
@app.get("/start_bot")
async def start():
    if not shared.bot_online:
        asyncio.create_task(shared.start_bot())
    return RedirectResponse("/")
"""

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) # Here you can change the port.