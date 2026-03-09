from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
from scraper import scrape_prospects

app = FastAPI(title="Prospects API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SearchParams(BaseModel):
    segment: str
    location: str
    radius: int

@app.post("/api/prospects")
def generate_prospects(params: SearchParams):
    from fastapi.responses import JSONResponse
    try:
        results = scrape_prospects(params.segment, params.location, params.radius)
        return {"status": "success", "data": results}
    except Exception as e:
        import traceback
        error_msg = traceback.format_exc()
        # Imprime no terminal do uvicorn
        print("Scraper Error:\n", error_msg)
        return JSONResponse(status_code=500, content={"detail": str(e), "traceback": error_msg})

@app.get("/api/health")
def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
