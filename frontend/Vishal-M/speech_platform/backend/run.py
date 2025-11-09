# /run.py
import uvicorn
import os

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "app.main:app",  # <-- UPDATED
        host=os.getenv("HOST", "0.0.0.0"),
        port=port,
        reload=True
    )