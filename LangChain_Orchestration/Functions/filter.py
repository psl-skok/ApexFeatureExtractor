import pandas as pd
from typing import List

def filter(df: pd.DataFrame, target_col: str, filter_values: List[str]) -> pd.DataFrame:
    """
    Filter a DataFrame to include only rows where the value in target_col
    matches one of the strings in filter_values.

    Args:
        df (pd.DataFrame): The input dataframe.
        target_col (str): The column to filter on.
        filter_values (List[str]): A list of strings to keep.

    Returns:
        pd.DataFrame: A filtered dataframe containing only matching rows.
    """
    if target_col not in df.columns:
        raise ValueError(f"Column '{target_col}' not found in dataframe.")
    if not isinstance(filter_values, list):
        raise ValueError("filter_values must be a list of strings.")

    filtered_df = df[df[target_col].isin(filter_values)].reset_index(drop=True)
    print(f"✅ Filtering complete. Kept {len(filtered_df)} rows where '{target_col}' matches {filter_values}.")
    return filtered_df
