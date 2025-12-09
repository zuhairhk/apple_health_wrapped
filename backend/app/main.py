from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .parser import get_wrapped_stats

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/wrapped")
def wrapped_data():
    return get_wrapped_stats()
