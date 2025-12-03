from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import init_db
from .routers import auth, banking, voice

app = FastAPI(title="Voice Banking System")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database
@app.on_event("startup")
def startup():
    init_db()

# Include routers
app.include_router(auth.router)
app.include_router(banking.router)
app.include_router(voice.router)

@app.get("/")
def root():
    return {"message": "Voice Banking System API"}
