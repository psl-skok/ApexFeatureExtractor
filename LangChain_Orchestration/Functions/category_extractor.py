import pandas as pd
from typing import List
from concurrent.futures import ThreadPoolExecutor
import json
from client import client


# -------------------------------
# Helper: Extract categories for a single transcript
# -------------------------------
def _extract_category_names_from_transcript(transcript_text: str,
                                            context_prompt: str,
                                            transcript_idx: int) -> List[str]:
    """Extract category names from one transcript."""
    processed_transcript = (
        transcript_text[:8000] + "... [truncated]"
        if len(transcript_text) > 8000 else transcript_text
    )

    system_prompt = f"""
    You are an expert at extracting category names from text.
    Your task: {context_prompt}

    Instructions:
    1. Extract 1–10 distinct categories mentioned in the transcript.
    2. Use exact text; no duplicates.
    3. Return ONLY categories clearly referenced.
    4. Respond as JSON:
    {{
        "categoryNames": ["Category A", "Category B"]
    }}
    """

    user_prompt = f"""
    Transcript ID: {transcript_idx}
    Transcript:
    {processed_transcript}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-5-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0,
            response_format={"type": "json_object"},
        )
        parsed = json.loads(response.choices[0].message.content.strip())
        return [str(name) for name in parsed.get("categoryNames", [])]

    except Exception as e:
        print(f"⚠️ Error extracting categories for transcript {transcript_idx}: {e}")
        return []


# -------------------------------
# Main function (returns DataFrame)
# -------------------------------
def category_extractor(df: pd.DataFrame,
                       transcript_column: str,
                       context_prompt: str,
                       target_column: str = "category_list",
                       max_workers: int = 8) -> pd.DataFrame:
    """
    Extracts category names from each transcript and adds a column containing
    the list of categories found per transcript.
    Returns a new DataFrame with the added column.
    """

    print(f"🚀 Starting category extraction for {len(df)} transcripts...")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(
                _extract_category_names_from_transcript,
                str(row[transcript_column]),
                context_prompt,
                idx + 1
            )
            for idx, row in df.iterrows()
        ]

        results = [future.result() for future in futures]

    df[target_column] = results
    print(f"✅ Completed category extraction — added column: '{target_column}'")

    return df
