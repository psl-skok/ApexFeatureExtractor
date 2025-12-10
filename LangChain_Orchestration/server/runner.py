# server/runner.py
from __future__ import annotations
from typing import List, Dict, Any, Tuple
import traceback
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
from storage import get_dataset_df, update_analysis, DATA_DIR
from pydantic import BaseModel
import smtplib
import os
from email.mime.text import MIMEText

# ---- import your stuff ----
# Adjust path if needed; assumes Compiler is a sibling of server
import sys, os
ROOT = os.path.dirname(os.path.dirname(__file__))
COMPILER_DIR = os.path.join(ROOT, "Compiler")
if COMPILER_DIR not in sys.path:
    sys.path.append(COMPILER_DIR)

from compiler import compile_and_run, FUNCTION_REGISTRY  # your existing code

# --- token/cost estimate: very rough heuristic for dry-run ---
def run_flow_background(analysis_id: str, dataset_id: str, path_request: List[Dict[str, Any]]):
    """Runs in a background task/thread. Updates RUNS store as we go."""
    update_analysis(analysis_id, status="running")
    # append_log equivalent: we'll collect logs in memory and update at end

    try:
        df = get_dataset_df(dataset_id)
        print('path_request', path_request)
        state, execution_log = compile_and_run(path_request, df)
        print('We have gotten to the point where we are writing the artifacts')
        # Save artifacts
        artifacts = {}
        artifacts_dir = os.path.join(DATA_DIR, 'artifacts', analysis_id)
        os.makedirs(artifacts_dir, exist_ok=True)
        for key, value in state.items():
            if isinstance(value, tuple) and len(value) == 3 and isinstance(value[0], pd.DataFrame):
                csv_path = os.path.join(artifacts_dir, f"{key}.csv")
                value[0].to_csv(csv_path, index=False)
                #artifacts[key] = (csv_path, value[1], value[2])  # Replace DF with path, keep structure
                artifacts[key] = csv_path  
            else:
                artifacts[key] = value  # Small/serializable values as-is

        update_analysis(analysis_id, status="completed", execution_log=execution_log, artifacts=artifacts)
        send_email_notification(
            subject=f"✅ Analysis {analysis_id} complete",
            body=f"Your analysis is finished! Check the dashboard for results."
        )

    except Exception as e:
        tb = traceback.format_exc()
        update_analysis(analysis_id, status="failed", error=f"{str(e)}\n{tb}", execution_log=[])
        send_email_notification(
            subject=f"❌ Analysis {analysis_id} failed",
            body=f"Error details:\n\n{str(e)}\n\n{tb}"
        )

def send_email_notification(subject: str, body: str):
    """Send a simple email when an analysis completes or fails."""
    try:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = os.getenv("EMAIL_USER")
        msg["To"] = os.getenv("ALERT_EMAIL")

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(os.getenv("EMAIL_USER"), os.getenv("EMAIL_PASS"))
            server.send_message(msg)

        print("✅ Email notification sent successfully.")
    except Exception as e:
        print(f"⚠️ Failed to send email: {e}")

