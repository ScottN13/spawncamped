import uvicorn
import os
import logging
from datetime import datetime
import json
from rich import print as say
from fastapi import FastAPI
from fastapi import APIRouter
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")