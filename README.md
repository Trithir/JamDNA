# JamDNA

JamDNA is a local-first tool for organizing and clustering jam session recordings.  
Drop full-take audio files into a folder → the app fingerprints them → suggests near-identical matches → you review, play, and cluster them.  
Everything runs **locally** — no cloud services, no data collection.

---

## Features (MVP scaffold)

- **Ingest**: scan `data/audio/` for new tracks, fingerprint with Chromaprint.
- **Database**: SQLite for tracks and clusters.
- **Indexing**: FAISS for fast nearest-neighbor search on fingerprints.
- **API**: FastAPI backend with routes for ingest, query, cluster management, and audio streaming.
- **UI**: React + Vite frontend with a review queue, neighbor preview, and cluster list.
- **File moves**: When you assign a track, it moves into `data/clusters/<ClusterName>/`.

---

## Prerequisites

Before setup, make sure you have these installed on your system:

- **Visual Studio build tools** 
- **Python** 3.10+  
- **Node.js** 18+ (comes with `npm`) 
- **ffmpeg** (for audio decoding/streaming)  
- **Chromaprint (fpcalc)** (for audio fingerprinting) https://acoustid.org/chromaprint

### Install system dependencies

**Ubuntu/Debian**
sudo apt update
sudo apt install ffmpeg chromaprint-tools python3-venv

**macOS (Homebrew)**
brew install ffmpeg chromaprint

**Windows**
Install ffmpeg and add to PATH.
Install Chromaprint binaries.

**Setup**
Clone and enter repo

cd jamdna

**Backend setup**
cd backend
python -m venv venv
source venv/bin/activate   # Windows bash: source venv/Scripts/activate
pip install -r requirements.txt

**Frontend setup**
cd ../frontend
npm install

**Running the app**
**Run both backend (FastAPI) and frontend (Vite) at once:**

cd frontend
npm run fullstack

Backend → http://localhost:8000

Frontend → http://localhost:5173

Alternatively run two terminals both cd frontend:

npm run dev

npm run backend

**Usage**
Place audio files (WAV, FLAC, MP3, etc.) in data/audio/.

Open the frontend in your browser → http://localhost:5173.

**Review Queue tab:**

Shows unclustered tracks.

Play audio, check nearest neighbors, create/assign clusters.

**Cluster List tab:**

Browse all clusters and their members.

Play audio directly from clusters.

When a track is assigned, its file is moved into the proper cluster folder under data/clusters/.

**Roadmap**
Add persistence for FAISS index (faiss.index file).

Add cluster rename + inline editing in frontend.

Smarter similarity thresholds (DTW tie-breaker).

Version genealogy (“jam family tree”).

Export playlists/folders from clusters.

**License**
MIT — free to use, modify, and share.

### Recap
- `db.sqlite` is auto-created and filled when you run the backend and hit `/ingest`.  
- `faiss.index` isn’t used yet (future step if you want persistence).  
- After running `npm run fullstack`, you’ll be able to hit the frontend, ingest tracks, and start testing.  
