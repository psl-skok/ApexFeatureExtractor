# unsupervised_grouping.py
import pandas as pd
import json
from typing import Optional
from client import client


def unsupervised_grouping(
    df: pd.DataFrame,
    input_column: str,
    context_prompt: str,
    id_column: Optional[str] = None,
    target_column: str = "Group_Mapping",
) -> pd.DataFrame:
    """
    Groups text responses into 2–5 categories using an LLM (unsupervised grouping).

    Args:
        df (pd.DataFrame): DataFrame containing the text to categorize.
        input_column (str): Column name with text data to group.
        context_prompt (str): Instruction to guide grouping (e.g., "Group by customer sentiment").
        id_column (str, optional): Unique identifier column; defaults to first column if None.
        target_column (str, optional): Name of the new output column. Default = 'Group_Mapping'.

    Returns:
        pd.DataFrame: Updated DataFrame with a new column assigning each row to a category.
    """

    if df.empty:
        print("⚠️ Empty DataFrame received. Returning unchanged.")
        return df

    id_column = id_column or df.columns[0]

    # Build text input for the model
    input_data = "\n".join([
        f"ID: {str(row[id_column])} | {row[input_column]}"
        for _, row in df.iterrows()
        if pd.notna(row[input_column])
    ])

    # System + User prompt
    system_prompt = f"""
    You are an expert at unsupervised text grouping and categorization.
    Your task: {context_prompt}

    Instructions:
    1. Identify 2–5 meaningful categories.
    2. Provide clear category names + short descriptions.
    3. Assign each ID to exactly one category.
    4. Respond ONLY in JSON:
    {{
        "categories": [
            {{"name": "Category Name", "description": "Short description"}}
        ],
        "assignments": {{
            "1": "Category Name",
            "2": "Another Category"
        }}
    }}
    """

    user_prompt = f"Text entries to group:\n\n{input_data}"

    print(f"🧠 Running unsupervised grouping on {len(df)} rows...")

    try:
        response = client.chat.completions.create(
            model="gpt-5-mini",
            input=[
                {"role": "system", "content": system_prompt.strip()},
                {"role": "user", "content": user_prompt.strip()}
            ],
            temperature=0,
            response_format={"type": "json_object"}
        )

        parsed = json.loads(response.choices[0].message.content)


        assignments = parsed.get("assignments", {})
        categories = parsed.get("categories", [])

        # Apply category assignments
        df[target_column] = df[id_column].astype(str).map(assignments)

        # Handle missing IDs (unmapped)
        missing_count = df[target_column].isna().sum()
        if missing_count > 0:
            print(f"⚠️ {missing_count} rows were not mapped to any category. Filling as 'Uncategorized'.")
            df[target_column] = df[target_column].fillna("Uncategorized")

        # Print summary
        print(f"✅ Created {len(categories)} categories:")
        for c in categories:
            print(f"  - {c['name']}: {c['description']}")

        return df

    except Exception as e:
        print(f"❌ Error during unsupervised grouping: {str(e)}")
        df[target_column] = "Error"
        return df
