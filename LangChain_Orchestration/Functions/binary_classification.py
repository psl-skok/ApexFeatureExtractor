import pandas as pd  
from pydantic import BaseModel
from concurrent.futures import ThreadPoolExecutor
from client import client
from typing import Optional

# Define schema for structured output
class BinaryOutcome(BaseModel):
    call_id: str
    binary_label: str
    binary_explanation: str

class BinaryOutcomeNoExplanation(BaseModel):
    call_id: str
    binary_label: str
    

# -------------------------------
# Helper function for one row
# -------------------------------
def process_row_binary(row,
                       context_prompt,
                       input_data,
                       positive_label,
                       negative_label,
                       client,
                       include_explanation=True):
    call_id = row["call_id"]
    transcript = row[input_data]

        # Build base JSON format dynamically
    json_structure = (
        f'{{ "binary_label": "{positive_label}" or "{negative_label}" }}'
        if not include_explanation
        else f'''{{
            "binary_label": "{positive_label}" or "{negative_label}",
            "binary_explanation": "Reasoning citing evidence from the transcript"
        }}'''
    )

    messages = [
        {
            "role": "system",
            "content": """
            You are a precise binary classifier. Answer strictly based only on evidence in the transcript. 
            Do not make assumptions. 
            Always respond with valid JSON.
            """,
        },
        {
            "role": "user",
            "content": f"""
            Question: {context_prompt}
            Transcript: {transcript}

            Respond ONLY as JSON:
            {json_structure}
            """,
        },
    ]

   

    try:
        text_format = BinaryOutcome # Default assignment

        if(include_explanation == "false"):
            text_format = BinaryOutcomeNoExplanation

        response = client.responses.parse(
            model="gpt-5-mini",
            input=messages,
            text_format=text_format,
            temperature=1.0,
        )

        if(include_explanation == "false"):
            parsed:  BinaryOutcomeNoExplanation = response.output_parsed
        else:
            parsed:  BinaryOutcome = response.output_parsed

        parsed.call_id = call_id

    except Exception as e:
        print(f"Failed to parse {call_id}: {e}")
        parsed = text_format(
            call_id=call_id,
            binary_label=negative_label,
            binary_explanation=None if not include_explanation else "No explanation found",
        )

    return parsed.model_dump()

# -------------------------------
# Parallel classifier
# -------------------------------
def binary_classifier_parallel(df,
                               context_prompt,
                               input_data="call_text",
                               positive_label="true",
                               negative_label="false",
                               explanation_col="binary_explanation",
                               label_col="binary_label",
                               include_explanation=True,
                               max_workers=8) -> pd.DataFrame:
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(
                process_row_binary,
                row,
                context_prompt,
                input_data,
                positive_label,
                negative_label,
                client,
                include_explanation
            )
            for _, row in df.iterrows()
        ]
        results = [f.result() for f in futures]

    # Convert list of dicts into DataFrame and merge
    results_df = pd.DataFrame(results)
    results_df = results_df.rename(columns={
        "binary_explanation": explanation_col,
        "binary_label": label_col,
    })

    # Drop explanation column if not requested
    if not include_explanation and explanation_col in results_df.columns:
        results_df = results_df.drop(columns=[explanation_col])

    df = df.merge(results_df, on="call_id", how="left")
    return df

# -------------------------------
# Multi-Binary classifier (Compiler-compatible)
# -------------------------------
def run_multiple_binary_classifiers(df: pd.DataFrame, questions: list[dict], max_workers=5) -> pd.DataFrame:
    """
    Runs multiple binary classification questions sequentially on the same dataframe.
    Each question adds two new columns (label + explanation).
    """
    df = df.copy()

    for q in questions:
        print(f"Running classifier: {q['context_prompt']}")
        df = binary_classifier_parallel(
            df,
            context_prompt=q["context_prompt"],
            positive_label=q["positive_label"],
            negative_label=q["negative_label"],
            explanation_col=q["explanation_col"],
            label_col=q["label_col"],
            include_explanation=q.get("include_explanation", True),
            max_workers=max_workers,
        )

    return df