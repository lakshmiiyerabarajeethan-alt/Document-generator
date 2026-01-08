from fastapi import FastAPI
from models.recorded_input import RecordedInput

from normalizer import normalize_steps
from doc_prompt import build_business_doc_prompt
from llm_client import call_llm

from exporters.export_docx import export_to_docx
from exporters.export_pdf import export_to_pdf

import os
from datetime import datetime

from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(
    title="Business Documentation Generator",
    version="1.1"
)

# Allow all origins (for local dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (you can restrict in production)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/business-doc")
async def generate_business_doc(data: RecordedInput):

    normalized = normalize_steps(data.steps)

    prompt = build_business_doc_prompt(
        app_name=data.application,
        normalized_steps=normalized
    )

    business_doc = await call_llm(prompt)

    os.makedirs("exports", exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    docx_file = f"exports/{timestamp}_business_doc.docx"
    pdf_file = f"exports/{timestamp}_business_doc.pdf"

    export_to_docx(business_doc, docx_file)
    export_to_pdf(business_doc, pdf_file)

    return {
        "application": data.application,
        "normalized_steps": normalized,
        "business_document_text": business_doc,
        "docx_file": docx_file,
        "pdf_file": pdf_file
    }
