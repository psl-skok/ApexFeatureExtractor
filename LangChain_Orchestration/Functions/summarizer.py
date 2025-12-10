import pandas as pd
from pydantic import BaseModel
from concurrent.futures import ThreadPoolExecutor
from client import client


class SummarizationOutput(BaseModel):
    summary: str
    explanation: str


def summarize_text_block(group_text: str, context_prompt: str) -> SummarizationOutput:
    """
    Summarizes a block of text using GPT with a given context.
    """
    if not group_text.strip():
        return SummarizationOutput(summary="No content to summarize", explanation="Empty or whitespace-only text")

    print("😎Starting the summarize text block function")
    messages = [
        {
            "role": "system",
            "content": "You are an expert assistant summarizing grouped text. Output JSON only."
        },
        {
            "role": "user",
            "content": f"""
            Context: {context_prompt}
            Data to summarize:
            {group_text}
            
            Respond in JSON with:
            {{
                "summary": "Concise summary of the key points",
                "explanation": "Evidence/trends used to create the summary"
            }}
            """,
        },
    ]

    try:
        response = client.responses.parse(
            model="gpt-5-mini",
            input=messages,
            text_format=SummarizationOutput,
            temperature=0,
        )
        
        return response.output_parsed

    except Exception as e:
        print(f"⚠️ Failed to summarize group: {e}")
        return SummarizationOutput(summary="Summary failed", explanation=str(e))


def summarize_column_by_group(
    df: pd.DataFrame,
    target_col: str,
    group_by_col: str,
    context_prompt: str,
    max_workers: int = 4,
) -> pd.DataFrame:
    """
    Summarizes text in `target_col` for each unique value in `group_by_col'.

    - Designed for use after token_based_splitter modifies group labels
      (e.g., 'Group A_0', 'Group A_1', etc.).
    - Returns one summary per group value.

    Args:
        df (pd.DataFrame): DataFrame containing data to summarize.
        target_col (str): Column with text to summarize.
        group_by_col (str): Column to group by before summarizing.
        context_prompt (str): Context instruction for the summarizer.
        max_workers (int): Max threads for parallel summarization.

    Returns:
        pd.DataFrame: DataFrame with [group_by_col, summary, explanation].
    """
    print("👽Starting the summarize column by group function")
    if df.empty:
        print("⚠️ Empty DataFrame received. Returning empty summary DataFrame.")
        group_cols = [group_by_col] if isinstance(group_by_col, str) else group_by_col
        return pd.DataFrame(columns=group_cols + ["summary", "explanation"])

    if group_by_col not in df.columns:
            raise ValueError(f"Column '{group_by_col}' not found in DataFrame.")

    grouped = df.groupby(group_by_col)

    def process_group(name, group):
        """
        Combine all text for a group and summarize it.
        """
        combined_text = "\n\n".join(group[target_col].dropna().astype(str).tolist())
        result = summarize_text_block(combined_text, context_prompt)
        return {
            group_by_col: name,
            "summary": result.summary,
            "explanation": result.explanation,
        }

    # Run summarization in parallel
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(lambda g: process_group(*g), grouped))

    summary_df = pd.DataFrame(results)

    print(f"✅ Generated {len(summary_df)} summaries (grouped by '{group_by_col}').")
    return summary_df
