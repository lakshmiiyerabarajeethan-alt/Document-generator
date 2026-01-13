from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from models.recorded_input import RecordedInput
from normalizer import normalize_steps_with_grouping
from doc_prompt import build_business_doc_prompt
from llm_client import call_llm
from exporters.export_docx import export_to_docx
from exporters.export_pdf import export_to_pdf

import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="User Guide Generator",
    description="Generate professional user guides from recorded web interactions",
    version="2.0"
)

# --------------------------------------------------
# CORS
# --------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------
# Export directory
# --------------------------------------------------
EXPORT_DIR = os.path.join(os.path.dirname(__file__), "exports")


@app.get("/")
async def root():
    return {
        "status": "running",
        "service": "User Guide Generator",
        "version": "2.0",
        "endpoints": {
            "docs": "/docs",
            "generate_guide": "/generate-user-guide (POST)",
            "list_exports": "/exports/list (GET)",
            "download": "/download/{filename} (GET)"
        }
    }


@app.options("/business-doc")
@app.options("/generate-user-guide")
async def options_handler():
    return {"status": "ok"}


# --------------------------------------------------
# MAIN ENDPOINT
# --------------------------------------------------
@app.post("/generate-user-guide")
async def generate_user_guide(data: RecordedInput):
    import traceback

    try:
        # ------------------------------------------
        # Resolve application name
        # ------------------------------------------
        app_name = "Recorded Web Application"
        if data.metadata and data.metadata.browser:
            app_name = f"Web Application ({data.metadata.browser.split(' ')[0]})"

        print(f"📝 Generating user guide for: {app_name}")
        print(f"📊 Number of steps: {len(data.steps)}")

        # ------------------------------------------
        # Normalize steps
        # ------------------------------------------
        analysis = normalize_steps_with_grouping(
            [step.dict() for step in data.steps]
        )

        normalized = analysis["normalized_steps"]
        workflow_type = analysis["workflow_type"]
        logical_groups = analysis["logical_groups"]

        # ------------------------------------------
        # Build LLM prompt
        # ------------------------------------------
        prompt = build_business_doc_prompt(
            app_name=app_name,
            normalized_steps=normalized
        )

        # ------------------------------------------
        # Call LLM
        # ------------------------------------------
        user_guide = await call_llm(prompt)

        # ------------------------------------------
        # Export files
        # ------------------------------------------
        os.makedirs(EXPORT_DIR, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        docx_file = f"{EXPORT_DIR}/{timestamp}_user_guide.docx"
        pdf_file = f"{EXPORT_DIR}/{timestamp}_user_guide.pdf"
        md_file = f"{EXPORT_DIR}/{timestamp}_user_guide.md"

        with open(md_file, "w", encoding="utf-8") as f:
            f.write(user_guide)

        export_to_docx(user_guide, docx_file)
        export_to_pdf(user_guide, pdf_file)

        return {
            "success": True,
            "application": app_name,
            "workflow_type": workflow_type,
            "analysis": {
                "total_steps": analysis["total_steps"],
                "step_counts": analysis["step_counts"],
                "logical_groups": len(logical_groups)
            },
            "exports": {
                "markdown": md_file,
                "docx": docx_file,
                "pdf": pdf_file
            }
        }

    except Exception as e:
        error_details = traceback.format_exc()
        print(f"❌ ERROR: {str(e)}")
        print(f"📋 Traceback:\n{error_details}")

        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "type": type(e).__name__,
                "traceback": error_details
            }
        )


# --------------------------------------------------
# LEGACY ENDPOINT
# --------------------------------------------------
@app.post("/business-doc")
async def generate_business_doc(data: RecordedInput):
    return await generate_user_guide(data)


# --------------------------------------------------
# DOWNLOAD
# --------------------------------------------------
@app.get("/download/{filename}")
async def download_file(filename: str):
    file_path = os.path.join(EXPORT_DIR, filename)

    if not os.path.abspath(file_path).startswith(os.path.abspath(EXPORT_DIR)):
        raise HTTPException(status_code=400, detail="Invalid file path")

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    media_type = (
        "application/pdf"
        if filename.lower().endswith(".pdf")
        else "application/octet-stream"
    )

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type=media_type
    )


# --------------------------------------------------
# EXPORT LISTING
# --------------------------------------------------
@app.get("/exports/list")
async def list_exports():
    if not os.path.exists(EXPORT_DIR):
        return {"files": []}

    files = []
    for filename in os.listdir(EXPORT_DIR):
        file_path = os.path.join(EXPORT_DIR, filename)
        files.append({
            "filename": filename,
            "size": os.path.getsize(file_path),
            "created": datetime.fromtimestamp(
                os.path.getctime(file_path)
            ).isoformat()
        })

    return {"files": files}


@app.delete("/exports/{filename}")
async def delete_export(filename: str):
    file_path = os.path.join(EXPORT_DIR, filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    os.remove(file_path)
    return {"success": True, "message": f"{filename} deleted"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
