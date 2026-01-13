from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from models.recorded_input import RecordedInput

from normalizer import normalize_steps, normalize_steps_with_grouping
from doc_prompt import build_business_doc_prompt
from llm_client import call_llm

from exporters.export_docx import export_to_docx
from exporters.export_pdf import export_to_pdf

import os
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv
load_dotenv()

app = FastAPI(
    title="User Guide Generator",
    description="Generate professional user guides from recorded web interactions",
    version="2.0"
)

# Add CORS middleware to allow browser requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define absolute exports directory
EXPORT_DIR = os.path.join(os.path.dirname(__file__), "exports")


@app.get("/")
async def root():
    """Health check endpoint."""
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
    """Handle OPTIONS requests for CORS preflight."""
    return {"status": "ok"}


@app.post("/generate-user-guide")
async def generate_user_guide(data: RecordedInput):
    import traceback

    try:
        print(f"📝 Received request for application: {data.application}")
        print(f"📊 Number of steps: {len(data.steps)}")
        # Step 1: Normalize and analyze the recorded steps
        analysis = normalize_steps_with_grouping(data.steps)

        normalized = analysis["normalized_steps"]
        workflow_type = analysis["workflow_type"]
        logical_groups = analysis["logical_groups"]

        # Step 2: Build the prompt for LLM
        prompt = build_business_doc_prompt(
            app_name=data.application,
            normalized_steps=normalized
        )

        # Step 3: Generate user guide using LLM
        user_guide = await call_llm(prompt)

        # Step 4: Create export directory
        os.makedirs(EXPORT_DIR, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Step 5: Export to multiple formats
        docx_file = f"{EXPORT_DIR}/{timestamp}_user_guide.docx"
        pdf_file = f"{EXPORT_DIR}/{timestamp}_user_guide.pdf"
        md_file = f"{EXPORT_DIR}/{timestamp}_user_guide.md"

        # Save as markdown (raw)
        with open(md_file, "w", encoding="utf-8") as f:
            f.write(user_guide)

        # Export to DOCX and PDF
        export_to_docx(user_guide, docx_file)
        export_to_pdf(user_guide, pdf_file)

        return {
            "success": True,
            "application": data.application,
            "workflow_type": workflow_type,
            "analysis": {
                "total_steps": analysis["total_steps"],
                "step_counts": analysis["step_counts"],
                "logical_groups": len(logical_groups)
            },
            "normalized_steps": normalized,
            "logical_groups": logical_groups,
            "user_guide_text": user_guide,
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
                "traceback": error_details,
                "type": type(e).__name__
            }
        )


@app.post("/business-doc")
async def generate_business_doc(data: RecordedInput):
    """Legacy endpoint - redirects to new generate_user_guide endpoint."""
    return await generate_user_guide(data)


@app.get("/download/{filename}")
async def download_file(filename: str):
    """
    Download a generated file using absolute path to prevent ERR_FILE_NOT_FOUND.
    """
    # Build absolute path
    file_path = os.path.join(EXPORT_DIR, filename)

    # Security check to prevent path traversal
    if not os.path.abspath(file_path).startswith(os.path.abspath(EXPORT_DIR)):
        raise HTTPException(status_code=400, detail="Invalid file path")

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    # Set proper MIME type for PDF
    media_type = "application/pdf" if filename.lower().endswith(".pdf") else "application/octet-stream"

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type=media_type
    )


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
            "created": datetime.fromtimestamp(os.path.getctime(file_path)).isoformat()
        })

    return {"files": files}


@app.delete("/exports/{filename}")
async def delete_export(filename: str):
    file_path = os.path.join(EXPORT_DIR, filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    os.remove(file_path)
    return {"success": True, "message": f"File {filename} deleted successfully"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
