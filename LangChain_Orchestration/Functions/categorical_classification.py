import pandas as pd  
from pydantic import BaseModel
from concurrent.futures import ThreadPoolExecutor
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from client import client
from typing import List

# =========================
# SCHEMA
# =========================
class CategoricalOutcome(BaseModel):
    call_id: str
    categorical_explanation: str
    categorical_label: str

# -------------------------------
# Helper function for one row
# -------------------------------
def process_row_categorical(row,
                            classifications,
                            context_prompt,
                            input_data,
                            client,
                            id_column="call_id"):
    call_id = row[id_column]
    transcript = row[input_data]

    # Create classifications string for the prompt
    classifications_str = ", ".join(classifications)

    messages = [
        {
            "role": "system",
            "content": f"""
            You are an expert at analyzing sales call transcripts for categorical classification purposes.
            Your task: {context_prompt}
            Available classifications: {classifications_str}
            
            Instructions:
            1. Choose exactly ONE classification.
            2. Provide a short explanation referencing transcript evidence.
            3. Return valid JSON exactly as:
            {{
                "classification": "selected_classification",
                "explanation": "Reason for choice based on transcript"
            }}
            """,
        },
        {
            "role": "user",
            "content": f"""
            Call ID: {call_id}
            Transcript:-
            {transcript}
            """,
        },
    ]

    try:
        response = client.responses.parse(
            model="gpt-5-mini",
            input=messages,
            text_format=CategoricalOutcome,
            temperature=0,
        )

        parsed: CategoricalOutcome = response.output_parsed
        parsed.call_id = call_id

    except Exception as e:
        print(f"Failed to parse {call_id}: {e}")
        parsed = CategoricalOutcome(
            call_id=call_id,
            categorical_explanation="No explanation found",
            categorical_label="None"
        )

    return parsed.model_dump()

# -------------------------------
# Multi-row categorical classification with parallel processing
# -------------------------------
def categorical_classification(df,
                                   context_prompt: str,
                                   classifications: List[str] = [],
                                   input_data: str = "call_text", 
                                   explanation_col: str = "categorical_explanation",
                                   label_col: str = "categorical_label",
                                   max_workers: int = 8,
                                   id_column: str = "call_id") -> pd.DataFrame:
    """
    Classify call transcripts using categorical classification with parallel processing.
    
    Args:
        df (pd.DataFrame): DataFrame with call data
        classifications (List[str]): List of possible classifications (including "None")
        context_prompt (str): Context/question for classification
        input_data (str): Name of the column containing transcript text
        explanation_col (str): Name for the output explanation column
        label_col (str): Name for the output label column
        max_workers (int): Maximum number of parallel workers
    
    Returns:
        pd.DataFrame: Original DataFrame with added classification columns
    """
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(
                process_row_categorical,
                row,
                classifications,
                context_prompt,
                input_data, 
                client,
                id_column
            )
            for _, row in df.iterrows()
        ]
        results = [f.result() for f in futures]

    # 3️⃣ Merge results
    results_df = pd.DataFrame(results)
    results_df = results_df.rename(columns={
        "categorical_explanation": explanation_col,
        "categorical_label": label_col,
    })

    df = df.merge(results_df, left_on=id_column, right_on='call_id', how="left")
    if id_column != 'call_id':
        df = df.drop(columns=['call_id'])
    return df
