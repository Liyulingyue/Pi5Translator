from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from rapidocr import EngineType, ModelType, OCRVersion, RapidOCR
import uvicorn
import os
from typing import List

# Initialize OCR engine
ocr_engine = RapidOCR(
    params={
        "Det.engine_type": EngineType.ONNXRUNTIME,
        "Det.model_type": ModelType.MOBILE,
        "Det.ocr_version": OCRVersion.PPOCRV4,
    }
)

app = FastAPI(title="RapidOCR Service")


@app.post("/ocr")
async def ocr_service(image: UploadFile = File(...)) -> dict:
    """
    Accepts an uploaded image and returns OCR results (list of strings)
    - Input: uploaded image file (PNG/JPG/JPEG supported)
    - Output: {"result": ["text1", "text2", ...]}
    """
    try:
        # Validate file type
        if image.content_type not in ["image/png", "image/jpeg", "image/jpg"]:
            raise HTTPException(status_code=400, detail="Only PNG/JPG/JPEG images are supported")

        # Save temporary file
        temp_path = f"temp_{image.filename}"
        with open(temp_path, "wb") as f:
            f.write(await image.read())

        # Run OCR
        ocr_result = ocr_engine(temp_path)
        texts = ocr_result.txts

        # Clean up
        os.remove(temp_path)

        return {"result": texts}

    except Exception as e:
        # Remove temp file on error if it exists
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")