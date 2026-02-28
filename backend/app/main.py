from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import papers, users, feed
from app.db.database import Base, engine
from app.db import models  # add this line

Base.metadata.create_all(bind=engine)


app = FastAPI(title="InnovateFeed API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(papers.router, prefix="/papers", tags=["papers"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(feed.router, prefix="/feed", tags=["feed"])

@app.get("/")
def root():
    return {"status": "InnovateFeed API is running"}

@app.get("/create-tables")
def create_tables():
    try:
        Base.metadata.create_all(bind=engine)
        return {"status": "tables created", "tables": list(Base.metadata.tables.keys())}
    except Exception as e:
        return {"error": str(e)}