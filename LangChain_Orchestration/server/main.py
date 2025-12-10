# server/main.py
from __future__ import annotations
import io
import pandas as pd
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Optional
from models import DatasetInfo, ExecuteRequest, ExecuteResponse, RunStatus, CompilerRequest, CompilerResponse, DatasetWithHead, AnalysisSummary, FullAnalysis, SaveGraphRequest
from storage import init_db, save_dataset, get_datasets, get_analysis, get_analyses, create_analysis, save_graph, get_saved_graphs, get_saved_graph, get_dataset_df, delete_dataset_record
import os
import sys
import traceback
from runner import run_flow_background
from starlette.responses import FileResponse
from Compiler.function_registry import FUNCTION_REGISTRY

app = FastAPI(title="Transcript Analysis MVP", version="0.1.0")

# Allow localhost FE during dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    init_db()

# ---- Health ----
@app.get("/health")
def health():
    return {"ok": True}

# ---- Datasets ----
@app.post("/datasets")
async def upload_dataset(file: UploadFile = File(...)):
    """
    Accept a CSV (MVP). Reads into pandas and stores in memory.
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(400, "Only CSV supported")
    ds_id = save_dataset(file, file.filename)
    return {"success": True, "dataset_id": ds_id}

@app.get("/datasets", response_model=List[DatasetWithHead])
def list_datasets():
    datasets = get_datasets(with_heads=True)
    return datasets

# Get specific dataset preview
@app.get("/datasets/{dataset_id}", response_model=DatasetWithHead)
def get_dataset_preview(dataset_id: str):
    datasets = get_datasets(with_heads=True)
    for ds in datasets:
        if ds['id'] == dataset_id:  # Fixed: Use ['id'] for dict
            return ds
    raise HTTPException(404, "Dataset not found")

# Get function registry with argument metadata for FE
@app.get("/functions")
def get_functions():
    import inspect
    meta = {}
    for name, fn in FUNCTION_REGISTRY.items():
        try:
            sig = inspect.signature(fn)
        except (TypeError, ValueError):
            meta[name] = {"args": [], "doc": None}
            continue

        params = []
        for idx, (pname, p) in enumerate(sig.parameters.items()):
            # Skip DataFrame positional arg (first) and common self
            if idx == 0 or pname == "self":
                continue
            annotation = None if p.annotation is inspect._empty else str(p.annotation)
            if annotation and annotation.startswith("<class "):
                # Normalize simple annotations like <class 'str'> -> str
                annotation = annotation.replace("<class '", "").replace("'>", "")
            default = None if p.default is inspect._empty else p.default
            # Ensure defaults are JSON serializable (fallback to string)
            try:
                _ = default  # noqa: F841 (placeholder)
            except Exception:
                default = str(default)
            params.append({
                "name": pname,
                "required": p.default is inspect._empty,
                "default": default,
                "type": annotation,
            })

        meta[name] = {
            "args": params,
            "doc": inspect.getdoc(fn)
        }

    return meta

@app.get("/datasets/truncated/{dataset_id}")
def get_dataset_truncated(dataset_id: str, preview_rows: int = 10, max_cell_chars: int = 200):
    """
    Return dataset metadata and a truncated preview (first few rows and limited cell length).
    """
    try:
        df = get_dataset_df(dataset_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Dataset not found")

    # Take only top rows
    head_df = df.head(preview_rows)

    # Truncate long text cells
    def truncate(value):
        if isinstance(value, str) and len(value) > max_cell_chars:
            return value[:max_cell_chars].rsplit(' ', 1)[0] + "..."
        return value

    truncated_df = head_df.applymap(truncate)

    return {
        "id": dataset_id,
        "head": truncated_df.to_dict(orient="records"),
        "num_rows": len(df)
    }

# ---- Delete dataset ----
@app.delete("/datasets/{dataset_id}")
def delete_dataset(dataset_id: str):
    """
    Delete a dataset by ID. Removes the stored file and database record.
    """
    try:
        delete_dataset_record(dataset_id)
        return {"success": True, "message": f"Dataset {dataset_id} deleted"}
    except KeyError:
        raise HTTPException(status_code=404, detail="Dataset not found")
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to delete dataset: {str(e)}")


# ---- Run status ----
@app.get("/runs/{run_id}", response_model=RunStatus)
def get_run_status(run_id: str):
    try:
        r = get_run(run_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return RunStatus(
        run_id=run_id,
        status=r["status"],
        progress=r.get("progress"),
        logs=r.get("logs", []),
        artifacts=r.get("artifacts", {}),
        error=r.get("error"),
        cost_estimate_usd=r.get("cost_estimate_usd"),
        token_estimate=r.get("token_estimate"),
    )

# ---- Compiler endpoint ----
@app.post("/compiler/run")
def run_compiler(req: CompilerRequest, background_tasks: BackgroundTasks):
    try:
        analysis_id = create_analysis(req.dataset_id)
        background_tasks.add_task(run_flow_background, analysis_id=analysis_id, dataset_id=req.dataset_id, path_request=req.path_request)
        return {"analysis_id": analysis_id}
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start analysis: {str(e)}")

# GET /analyses
@app.get("/analyses", response_model=List[AnalysisSummary])
def list_analyses():
    return get_analyses()

# GET /analyses/{analysis_id}
@app.get("/analyses/{analysis_id}", response_model=FullAnalysis)
def get_specific_analysis(analysis_id: str):
    try:
        return get_analysis(analysis_id)
    except KeyError:
        raise HTTPException(404, "Analysis not found")

@app.get("/analyses/{analysis_id}/artifacts/{artifact_key}")
def get_artifact(analysis_id: str, artifact_key: str, format: Optional[str] = 'csv', nrows: Optional[int] = None):
    analysis = get_analysis(analysis_id)
    artifacts = analysis['artifacts']
    value = artifacts[artifact_key]
    print(f"Debug: artifact_key={artifact_key}, type(value)={type(value)}, value={value}")
    if isinstance(value, (list, tuple)) and len(value) == 3 and isinstance(value[0], str):
        path = value[0]
    elif isinstance(value, str):
        path = value
    else:
        raise HTTPException(404, "Artifact not found or not a file")
    print(f"Debug: extracted path={path}")
    if format == 'json':
        df = pd.read_csv(path, nrows=nrows)
        return df.to_dict(orient='records')
    else:
        return FileResponse(path, media_type='text/csv', filename=f"{artifact_key}.csv")



@app.post("/saved-graphs")
def save_graph_endpoint(req: SaveGraphRequest):
    graph_id = save_graph(req.name, req.path)
    return {"graph_id": graph_id}

# GET list of saved graphs
@app.get("/saved-graphs")
def list_saved_graphs():
    return get_saved_graphs()


# GET single saved graph by ID (with full path)
@app.get("/saved-graphs/{graph_id}")
def get_saved_graph_endpoint(graph_id: str):
    try:
        return get_saved_graph(graph_id)
    except KeyError:
        raise HTTPException(404, "Graph not found")
    except ValueError as e:
        raise HTTPException(500, str(e))