from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import ingest, cluster, query, audio

app = FastAPI(title="Jam Clusterer")

# Allow frontend dev server (Vite) to talk to backend
origins = [
    "http://localhost:5173",  # Vite dev
    "http://127.0.0.1:5173",  # alternate
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingest.router, prefix="/ingest")
app.include_router(cluster.router, prefix="/cluster")
app.include_router(query.router, prefix="/query")
app.include_router(audio.router, prefix="/audio")
