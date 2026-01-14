# Apex Feature Extractor (Transcript Analysis MVP)

This repository contains an MVP platform for analyzing large collections of call transcripts using configurable, LLM-powered analysis workflows.

The system is designed to help analysts upload transcript datasets, construct reusable analysis pipelines, and execute those pipelines to generate structured insights such as classifications, summaries, and comparisons.

---

## Overview

The Apex Feature Extractor is composed of:
- A **FastAPI backend** for dataset management, workflow execution, and result persistence
- A **frontend** that interacts with the backend APIs to configure and run analyses
- A set of **LLM-assisted analytical functions** composed into directed graphs using LangGraph

Rather than running one-off scripts, the system enables repeatable, modular analysis workflows that can be saved, re-run, and iterated on.

---

## Key Capabilities

### Dataset Management
- Upload CSV datasets (e.g., call transcripts)
- Preview and truncate large text fields for UI display
- Persist dataset metadata and row counts
- Delete datasets and associated analyses

### Analysis Workflows
- Define analysis workflows as directed graphs of analytical steps
- Supported steps include:
  - Binary classification (e.g., presence/absence of topics)
  - Open-ended classification
  - Text summarization
  - Group-level comparison
- Workflows operate over Pandas DataFrames and pass shared state between steps

### Execution & Tracking
- Execute workflows asynchronously in the background
- Track analysis status, logs, errors, and artifacts
- Store and retrieve structured outputs (CSV / JSON)
- Persist reusable workflow graphs for later execution

### API-Driven Architecture
- Backend exposes REST endpoints for:
  - Dataset upload and preview
  - Function registry inspection (argument metadata for UI)
  - Workflow execution
  - Analysis result retrieval
  - Saved workflow graph management

---

## Example Workflow

An example analysis graph chains together multiple LLM-assisted steps:

1. Binary classification of transcripts (e.g., pricing discussed, competitor mentioned)
2. Open-ended classification into sales categories
3. Summarization of calls
4. Comparison across groups of calls

These steps are composed using LangGraph and executed as a single, reusable pipeline.

See `workflows/analysis_graph.py` for an example.

---

## Tech Stack

- **Backend:** Python, FastAPI
- **Data:** Pandas, SQLite (SQLAlchemy)
- **LLM Orchestration:** LangGraph, LangChain-style function modules
- **Frontend:** TypeScript
- **Execution Model:** Asynchronous background tasks
- **Storage:** Local filesystem + SQLite (MVP)

---

## Status

This project represents an internal MVP and experimentation platform.
It prioritizes flexibility and rapid iteration over production hardening.



# Running the Back End
1. Navigate to root directory
2. Create virtual environment:
    python -m venv .venv
3. Activate the Virtual Environment
    .venv\Scripts\activate
4. Install requirements
     pip install -r requirements.txt
5. To start server run in root directory:
    uvicorn LangChain_Orchestration.server.main:app --reload

6. To test server, run in root directory:
python LangChain_Orchestration\server\test_api.py



# Running the Front End

1. Navigate to the front_end folder
2. Install dependences with "npm install" (only needed the first time)
2. Start the development server with "npm run dev"
3. Visit http://localhost:3000 in your browser
