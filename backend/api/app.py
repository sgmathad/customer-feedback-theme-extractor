from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from typing import List
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import logging
import sys
from dotenv import load_dotenv
import os


# Add services to path
sys.path.append(str(Path(__file__).parent.parent))

# pylint: disable=import-error.
from services.file_parser import parse_all_files
from services.text_cleaner import clean_and_prepare_feedback
from services.embeddings_clustering import generate_embeddings_and_cluster
from services.theme_generator import generate_themes

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Customer Feedback Theme Extractor")

load_dotenv()

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".pdf", ".docx", ".txt", ".json"}

# Global storage for analysis results
analysis_results = {}

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",  # Alternative React dev server
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint - API health check"""
    return {
        "message": "Customer Feedback Theme Extractor API",
        "version": "1.0.0",
        "status": "running",
    }


@app.post("/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    """
    Multiple files uploaded from the frontend is handled
    in this method.
    :param files: Multipart formdata.
    :type files: List[UploadFile]
    """
    result = []

    for file in files:
        if file.filename is None:
            raise HTTPException(
                status_code=400,
                detail="One of the uploaded files has no filename",
            )
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

        logger.info(f"Uploaded file: {file.filename} ({len(content)} bytes)")
        result.append({"filename": file.filename, "status": "uploaded"})

    return {"success": True, "files_uploaded": len(result), "files": result}


@app.post("/analyze")
async def analyze_feedback():
    """
    Analyze all uploaded feedback files and extract themes.
    This processes files uploaded via /upload endpoint.
    """
    try:
        # Step 1: Check if files exist
        files = list(UPLOAD_DIR.glob("*"))
        valid_files = [
            f for f in files if f.is_file() and f.suffix.lower() in ALLOWED_EXTENSIONS
        ]

        if not valid_files:
            raise HTTPException(
                status_code=400,
                detail="No files uploaded. Please upload files first using /upload endpoint.",
            )

        logger.info(f"Starting analysis of {len(valid_files)} files")

        # Step 2: Parse all files in upload directory
        feedback_list = parse_all_files(UPLOAD_DIR)

        if not feedback_list:
            raise HTTPException(
                status_code=400,
                detail="No valid feedback found in uploaded files. Check file format and content.",
            )

        logger.info(
            f"Parsed {len(feedback_list)} feedback entries from {len(valid_files)} files"
        )

        # Step 3: Clean and normalize text (without deduplication)
        clean_feedback = clean_and_prepare_feedback(
            feedback_list,
            embeddings=None,  # No deduplication in first pass
            min_length=10,
            similarity_threshold=0.95,
        )

        if not clean_feedback:
            raise HTTPException(
                status_code=400,
                detail="All feedback entries were too short or invalid after cleaning.",
            )

        logger.info(f"Cleaned feedback: {len(clean_feedback)} valid entries remaining")

        # Step 4: Generate embeddings and cluster
        logger.info("Generating embeddings and clustering...")
        embeddings, labels, clustered_feedback = generate_embeddings_and_cluster(
            clean_feedback, min_clusters=3, max_clusters=12
        )

        num_clusters = len(set(labels))
        logger.info(f"Clustering complete: {num_clusters} clusters found")

        # Step 5: Generate theme names and descriptions
        logger.info("Generating theme names using AI...")
        themes = generate_themes(
            clustered_feedback, api_key=os.getenv("ANTHROPIC_API_KEY")
        )

        logger.info(f"Successfully generated {len(themes)} themes")

        # Step 6: Store results for later retrieval
        analysis_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        analysis_results[analysis_id] = {
            "timestamp": datetime.now().isoformat(),
            "total_feedback": len(feedback_list),
            "processed_feedback": len(clean_feedback),
            "num_clusters": num_clusters,
            "themes": themes,
            "clustered_feedback": clustered_feedback[:100],  # Store sample for quotes
        }

        print(
            {
                "success": True,
                "analysis_id": analysis_id,
                "total_feedback": len(feedback_list),
                "processed_feedback": len(clean_feedback),
                "removed_entries": len(feedback_list) - len(clean_feedback),
                "num_themes": len(themes),
                "themes": themes,
                "message": f"Analysis complete! Found {len(themes)} themes from {len(clean_feedback)} feedback entries.",
            }
        )

        return {
            "success": True,
            "analysis_id": analysis_id,
            "total_feedback": len(feedback_list),
            "processed_feedback": len(clean_feedback),
            "removed_entries": len(feedback_list) - len(clean_feedback),
            "num_themes": len(themes),
            "themes": themes,
            "message": f"Analysis complete! Found {len(themes)} themes from {len(clean_feedback)} feedback entries.",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing feedback: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Error analyzing feedback: {str(e)}"
        )


@app.get("/status")
async def get_status():
    """
    Check how many files are ready for analysis
    """
    files = list(UPLOAD_DIR.glob("*"))
    valid_files = [
        f.name for f in files if f.is_file() and f.suffix.lower() in ALLOWED_EXTENSIONS
    ]

    return {
        "files_uploaded": len(valid_files),
        "files": valid_files,
        "ready_for_analysis": len(valid_files) > 0,
        "allowed_extensions": list(ALLOWED_EXTENSIONS),
    }


@app.get("/results/{analysis_id}")
async def get_analysis_results(analysis_id: str):
    """
    Retrieve previously completed analysis results by ID
    """
    if analysis_id not in analysis_results:
        raise HTTPException(
            status_code=404,
            detail=f"Analysis '{analysis_id}' not found. Use /results to see available analyses.",
        )

    return analysis_results[analysis_id]


@app.get("/results")
async def list_analyses():
    """
    List all completed analyses
    """
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


@app.delete("/clear")
async def clear_uploads():
    """
    Clear all uploaded files from the uploads directory
    """
    try:
        deleted_count = 0
        for file_path in UPLOAD_DIR.iterdir():
            if file_path.is_file():
                file_path.unlink()
                deleted_count += 1

        logger.info(f"Cleared {deleted_count} files from uploads")

        return {
            "success": True,
            "message": f"Cleared {deleted_count} files",
            "files_deleted": deleted_count,
        }
    except Exception as e:
        logger.error(f"Error clearing files: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error clearing files: {str(e)}")


@app.delete("/results/{analysis_id}")
async def delete_analysis(analysis_id: str):
    """
    Delete a specific analysis result
    """
    if analysis_id not in analysis_results:
        raise HTTPException(
            status_code=404, detail=f"Analysis '{analysis_id}' not found"
        )

    del analysis_results[analysis_id]
    logger.info(f"Deleted analysis: {analysis_id}")

    return {"success": True, "message": f"Analysis '{analysis_id}' deleted"}


@app.delete("/results")
async def clear_all_results():
    """
    Clear all analysis results from memory
    """
    count = len(analysis_results)
    analysis_results.clear()
    logger.info(f"Cleared all {count} analysis results")

    return {"success": True, "message": f"Cleared {count} analysis results"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
