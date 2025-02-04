from fastapi import FastAPI
from app import api2_router

app = FastAPI()
app.include_router(api2_router, prefix='/chatlaps')
