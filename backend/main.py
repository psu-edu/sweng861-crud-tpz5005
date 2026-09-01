from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

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

# Launch the backend server apon startup of the application
if __name__ == "__main__":
    HOST = "0.0.0.0"
    PORT = 8000
    uvicorn.run("main:app", host=HOST, port=PORT, reload=True)