from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from models import Base
from db import engine
import os
from fastapi.staticfiles import StaticFiles
from routers import router as api_router

app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development; adjust in production
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

Base.metadata.drop_all(bind=engine)  
Base.metadata.create_all(bind=engine)  


os.makedirs("media", exist_ok=True)
app.mount("/api/v1/media", StaticFiles(directory="media"), name="media")

@app.get("/")
def read_root():
    return {"message": "Welcome to the CSEDU backend!"}

app.include_router(api_router)