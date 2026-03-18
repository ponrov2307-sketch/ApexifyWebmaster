"""Run the FastAPI server."""

import os
import uvicorn

if __name__ == "__main__":
    port = int(os.getenv("API_PORT", "8005"))
    reload = os.getenv("APP_ENV", "development") != "production"

    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=port,
        reload=reload,
        workers=1 if reload else 2,
    )
