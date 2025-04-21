"""
run_api.py
----------
Entry point script for running the FastAPI backend server.
"""

import uvicorn
from app.main import app

if __name__ == "__main__":
    # Run the FastAPI app with uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)