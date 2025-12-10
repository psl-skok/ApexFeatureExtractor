# unique_value_splitter.py
import pandas as pd

def unique_value_splitter(df: pd.DataFrame, splitter_column: str) -> pd.DataFrame:
    """
    Adds a new column mapping each unique value in `splitter_column` to an integer group index.

    Example:
        splitter_column = 'follow_up_label'
        Unique values = ['yes', 'no']
        → New column: 'follow_up_label_group' with values [0, 1]

    Args:
        df (pd.DataFrame): input dataframe
        splitter_column (str): column to create unique index mapping from

    Returns:
        pd.DataFrame: same dataframe with new group column added
    """
    if splitter_column not in df.columns:
        raise ValueError(f"Splitter column '{splitter_column}' not found in dataframe.")

    unique_values = sorted(df[splitter_column].dropna().unique().tolist())
    mapping = {val: i for i, val in enumerate(unique_values)}

    group_col_name = f"{splitter_column}_group"
    df[group_col_name] = df[splitter_column].map(mapping)

    print(f"✅ Added '{group_col_name}' column — {len(unique_values)} unique groups.")
    print("Mapping:", mapping)

    return df
