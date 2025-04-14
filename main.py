from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from typing import List
import os
from file_upload_handler import FileUploadHandler

app = FastAPI()

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    return await FileUploadHandler.handle_upload(file)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)