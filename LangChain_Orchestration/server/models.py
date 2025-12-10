# server/models.py
from __future__ import annotations
from typing import List, Dict, Any, Literal, Optional
from pydantic import BaseModel, Field

# ---- Flow & steps ----
class FlowStep(BaseModel):
    # 'function' must map to your FUNCTION_REGISTRY key
    function: str = Field(..., description="One of FUNCTION_REGISTRY keys")
    args: Dict[str, Any] = Field(default_factory=dict)
    input_df_name: str = Field(..., description="Name of the input DataFrame")
    output_df_name: str = Field(..., description="Name of the output DataFrame")

class FlowDefinition(BaseModel):
    name: str = "Ad-hoc Flow"
    dataset_id: str
    steps: List[FlowStep]
    run_options: Dict[str, Any] = Field(default_factory=dict)  # model, caps, pii toggle, etc.

class ExecuteMode(BaseModel):
    mode: Literal["dry_run", "execute"] = "execute"

class ExecuteRequest(ExecuteMode, FlowDefinition):
    pass

# ---- Datasets ----
class DatasetInfo(BaseModel):
    dataset_id: str
    filename: str
    n_rows: int

class DatasetWithHead(BaseModel):
    id: str
    original_filename: str
    num_rows: int
    created_at: Optional[str] = None
    head: Optional[List[Dict[str, Any]]] = None

# ---- Runs ----
class RunStatus(BaseModel):
    run_id: str
    status: Literal["queued", "running", "succeeded", "failed", "canceled"]
    progress: Optional[Dict[str, Any]] = None   # e.g. {"step_idx": 2, "of": 4, "processed": 120, "total": 800}
    logs: List[str] = Field(default_factory=list)
    artifacts: Dict[str, Any] = Field(default_factory=dict)  # URIs or inline small JSON
    error: Optional[str] = None
    cost_estimate_usd: Optional[float] = None
    token_estimate: Optional[int] = None

class ExecuteResponse(BaseModel):
    mode: Literal["dry_run", "execute"]
    run_id: Optional[str] = None
    plan_preview: Optional[List[FlowStep]] = None
    cost_estimate_usd: Optional[float] = None
    token_estimate: Optional[int] = None
    validation_warnings: List[str] = Field(default_factory=list)

class AnalysisSummary(BaseModel):
    id: str
    dataset_id: str
    status: str
    execution_log: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: Optional[str] = None
    finished_at: Optional[str] = None

class FullAnalysis(BaseModel):
    id: str
    dataset_id: str
    status: str
    execution_log: List[Dict[str, Any]] = Field(default_factory=list)
    artifacts: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    created_at: Optional[str] = None
    finished_at: Optional[str] = None

# ---- Compiler specific models ----
class CompilerRequest(BaseModel):
    dataset_id: str
    path_request: List[Dict[str, Any]] = Field(..., description="List of function calls with input_df_name and output_df_name")
    local_csv_path: Optional[str] = None  # Path to local CSV when dataset_id is "local_df"

class CompilerResponse(BaseModel):
    success: bool
    state_keys: List[str] = Field(default_factory=list)
    execution_log: List[Dict[str, Any]] = Field(default_factory=list)
    artifacts: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None



class SaveGraphRequest(BaseModel):
    name: str
    path: List[Dict[str, Any]]