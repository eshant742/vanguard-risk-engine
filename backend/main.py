from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from underwriting_engine import analyze_merchant
from fx_risk_engine import get_fx_risk_data

app = FastAPI(title="Razorpay Horizon API")

# Allow CORS for the React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the exact frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class UnderwritingRequest(BaseModel):
    url: str

@app.get("/")
def read_root():
    return {"status": "Razorpay Horizon API is running"}

@app.post("/api/underwrite")
def underwrite_merchant(req: UnderwritingRequest):
    try:
        result = analyze_merchant(req.url)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/fx-risk")
def fx_risk():
    try:
        data = get_fx_risk_data()
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
