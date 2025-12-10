import pandas as pd
from pydantic import BaseModel
from concurrent.futures import ThreadPoolExecutor
from client import client


# -------------------------------
# Schema for structured output
# -------------------------------
class OpenEnded(BaseModel):
    call_id: str
    open_response: str


# -------------------------------
# Helper for one row
# -------------------------------
def process_row_open_ended(row, context_prompt, input_data, client):
    call_id = row["call_id"]
    transcript = row[input_data]
    messages = [
        {
            "role": "system",
            "content": "You are an assistant answering open-ended questions about sales calls. Return JSON only.",
        },
        {
            "role": "user",
            "content": f"""
            Question: {context_prompt}
            Transcript: {transcript}

            Respond with:
            {{
                "open_response": "1–2 sentences answering the question based on transcript"
            }}
            """,
        },
    ]
    try:
        response = client.responses.parse(
            model="gpt-5-mini",
            input=messages,
            text_format=OpenEnded,
            temperature=0,
        )
        parsed = response.output_parsed
        parsed.call_id = call_id
    except Exception as e:
        print(f"Failed to parse {call_id}: {e}")
        parsed = OpenEnded(call_id=call_id, open_response="No answer found")

    return parsed.model_dump()


# -------------------------------
# Parallel Open-Ended Classification
# -------------------------------
def open_classification(df,
                        context_prompt: str,
                        input_data="call_text",
                        response_col="open_response",
                        max_workers=8) -> pd.DataFrame:
    """
    Runs an open-ended question classifier across the dataframe.
    Returns the same dataframe with one new column (response_col).
    """
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(process_row_open_ended, row, context_prompt, input_data, client)
            for _, row in df.iterrows()
        ]
        results = [future.result() for future in futures]

    results_df = pd.DataFrame(results)
    results_df = results_df.rename(columns={"open_response": response_col})

    return df.merge(results_df, on="call_id", how="left")
