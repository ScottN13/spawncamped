import os
from datetime import datetime
import time
import json
from rich import print as say
from fastapi import FastAPI
from fastapi import APIRouter
from fastapi import Request
from fastapi.responses import HTMLResponse, RedirectResponse, PlainTextResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

router = APIRouter()
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    html = open("templates/index.html").read()
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
    return PlainTextResponse({
        "1"
    })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) # Here you can change the port.