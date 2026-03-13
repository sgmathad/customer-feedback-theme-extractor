from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from typing import List
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import logging
import sys
import io
from dotenv import load_dotenv
import os

sys.path.append(str(Path(__file__).parent.parent))

# pylint: disable=import-error
from services.file_parser import parse_all_files
from services.text_cleaner import clean_and_prepare_feedback
from services.embeddings_clustering import generate_embeddings_and_cluster
from services.theme_generator import generate_themes
from services.sentiment_analyzer import run_sentiment_analysis
from services.quote_selector import add_quotes_to_themes
from services.recommendations import generate_recommendations
from services.pdf_report import generate_pdf_report
from services.demo_data import write_demo_files, get_demo_feedback_list

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Customer Feedback Theme Extractor")
load_dotenv()

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".pdf", ".docx", ".txt", ".json"}

# In-memory store for analysis results
analysis_results = {}

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────
# Health / root
# ─────────────────────────────────────────────

@app.get("/")
async def root():
    return {
        "message": "Customer Feedback Theme Extractor API",
        "version": "2.0.0",
        "status": "running",
    }


# ─────────────────────────────────────────────
# Upload
# ─────────────────────────────────────────────

@app.post("/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    result = []
    for file in files:
        if file.filename is None:
            raise HTTPException(status_code=400, detail="File has no filename")
        ext = Path(file.filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file.filename}. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
            )
        file_path = UPLOAD_DIR / file.filename
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        logger.info(f"Uploaded: {file.filename} ({len(content)} bytes)")
        result.append({"filename": file.filename, "status": "uploaded"})
    return {"success": True, "files_uploaded": len(result), "files": result}


# ─────────────────────────────────────────────
# Demo dataset
# ─────────────────────────────────────────────

@app.post("/demo")
async def load_demo_dataset():
    """Load the synthetic demo dataset into the uploads directory."""
    try:
        files = write_demo_files(UPLOAD_DIR)
        return {
            "success": True,
            "message": "Demo dataset loaded — ready to analyze.",
            "files": [f.name for f in files],
        }
    except Exception as e:
        logger.error(f"Error loading demo dataset: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error loading demo dataset: {e}")


# ─────────────────────────────────────────────
# Analyze
# ─────────────────────────────────────────────

@app.post("/analyze")
async def analyze_feedback():
    """Full analysis pipeline: parse → clean → embed → cluster → themes → sentiment → quotes → recommendations."""
    try:
        valid_files = [
            f for f in UPLOAD_DIR.glob("*")
            if f.is_file() and f.suffix.lower() in ALLOWED_EXTENSIONS
        ]
        if not valid_files:
            raise HTTPException(
                status_code=400,
                detail="No files uploaded. Use /upload or /demo first.",
            )

        logger.info(f"Starting analysis of {len(valid_files)} files")

        # 1. Parse
        feedback_list = parse_all_files(UPLOAD_DIR)
        if not feedback_list:
            raise HTTPException(status_code=400, detail="No valid feedback found in uploaded files.")

        # 2. Clean
        clean_feedback = clean_and_prepare_feedback(
            feedback_list,
            embeddings=None,
            min_length=10,
            similarity_threshold=0.95,
        )
        if not clean_feedback:
            raise HTTPException(status_code=400, detail="All feedback was too short or invalid after cleaning.")

        logger.info(f"Clean feedback: {len(clean_feedback)} entries")

        # 3. Embed + cluster
        embeddings, labels, clustered_feedback = generate_embeddings_and_cluster(
            clean_feedback, min_clusters=3, max_clusters=12
        )
        num_clusters = len(set(labels))
        logger.info(f"Clusters: {num_clusters}")

        # 4. Theme names
        themes = generate_themes(clustered_feedback, api_key=os.getenv("ANTHROPIC_API_KEY"))
        logger.info(f"Themes generated: {len(themes)}")

        # 5. Sentiment analysis
        clustered_feedback, themes, overall_sentiment = run_sentiment_analysis(
            clustered_feedback, themes
        )
        logger.info("Sentiment analysis complete")

        # 6. Quote selection
        themes = add_quotes_to_themes(clustered_feedback, themes, n_quotes=5)
        logger.info("Quotes selected")

        # 7. Recommendations
        recommendations = generate_recommendations(
            themes,
            overall_sentiment,
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            n_recommendations=5,
        )
        logger.info(f"Recommendations generated: {len(recommendations)}")

        # 8. Store result
        analysis_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        analysis_results[analysis_id] = {
            "timestamp": datetime.now().isoformat(),
            "total_feedback": len(feedback_list),
            "processed_feedback": len(clean_feedback),
            "num_clusters": num_clusters,
            "themes": themes,
            "overall_sentiment": overall_sentiment,
            "recommendations": recommendations,
        }

        return {
            "success": True,
            "analysis_id": analysis_id,
            "total_feedback": len(feedback_list),
            "processed_feedback": len(clean_feedback),
            "removed_entries": len(feedback_list) - len(clean_feedback),
            "num_themes": len(themes),
            "themes": themes,
            "overall_sentiment": overall_sentiment,
            "recommendations": recommendations,
            "message": f"Analysis complete! Found {len(themes)} themes from {len(clean_feedback)} feedback entries.",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error analyzing feedback: {e}")


# ─────────────────────────────────────────────
# Status
# ─────────────────────────────────────────────

@app.get("/status")
async def get_status():
    valid_files = [
        f.name for f in UPLOAD_DIR.glob("*")
        if f.is_file() and f.suffix.lower() in ALLOWED_EXTENSIONS
    ]
    return {
        "files_uploaded": len(valid_files),
        "files": valid_files,
        "ready_for_analysis": len(valid_files) > 0,
        "allowed_extensions": list(ALLOWED_EXTENSIONS),
    }


# ─────────────────────────────────────────────
# Results
# ─────────────────────────────────────────────

@app.get("/results/{analysis_id}")
async def get_analysis_results(analysis_id: str):
    if analysis_id not in analysis_results:
        raise HTTPException(status_code=404, detail=f"Analysis '{analysis_id}' not found.")
    return analysis_results[analysis_id]


@app.get("/results")
async def list_analyses():
    return {
        "total_analyses": len(analysis_results),
        "analyses": [
            {
                "analysis_id": aid,
                "timestamp": data["timestamp"],
                "num_themes": len(data["themes"]),
                "total_feedback": data["total_feedback"],
            }
            for aid, data in analysis_results.items()
        ],
    }


# ─────────────────────────────────────────────
# PDF Export
# ─────────────────────────────────────────────

@app.get("/results/{analysis_id}/pdf")
async def download_pdf_report(analysis_id: str):
    """Generate and stream a PDF report for a completed analysis."""
    if analysis_id not in analysis_results:
        raise HTTPException(status_code=404, detail=f"Analysis '{analysis_id}' not found.")

    data = analysis_results[analysis_id]
    try:
        pdf_bytes = generate_pdf_report(
            themes=data["themes"],
            overall_sentiment=data.get("overall_sentiment", {}),
            recommendations=data.get("recommendations", []),
            total_feedback=data["total_feedback"],
        )
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="feedback_report_{analysis_id}.pdf"'
            },
        )
    except Exception as e:
        logger.error(f"PDF generation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {e}")


# ─────────────────────────────────────────────
# Clear / Delete
# ─────────────────────────────────────────────

@app.delete("/clear")
async def clear_uploads():
    deleted_count = 0
    for f in UPLOAD_DIR.iterdir():
        if f.is_file():
            f.unlink()
            deleted_count += 1
    logger.info(f"Cleared {deleted_count} uploaded files")
    return {"success": True, "message": f"Cleared {deleted_count} files", "files_deleted": deleted_count}


@app.delete("/results/{analysis_id}")
async def delete_analysis(analysis_id: str):
    if analysis_id not in analysis_results:
        raise HTTPException(status_code=404, detail=f"Analysis '{analysis_id}' not found.")
    del analysis_results[analysis_id]
    return {"success": True, "message": f"Analysis '{analysis_id}' deleted."}


@app.delete("/results")
async def clear_all_results():
    count = len(analysis_results)
    analysis_results.clear()
    return {"success": True, "message": f"Cleared {count} analysis results."}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)