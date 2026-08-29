from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Enable CORS for the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000",
                   "http://127.0.0.1:3000"],
)

#################################################

@app.get("/api/hello")
def get_hello():
    return {"message": "Hello World!"}

#################################################

@app.get("/health")
def health_status():
    return {"status": "ok"}

#################################################