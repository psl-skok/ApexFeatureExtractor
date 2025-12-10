import pandas as pd
import tiktoken

def count_tokens(text: str, model: str = "gpt-5-mini") -> int:
    """
    Count tokens in a string using OpenAI's tiktoken for a specific model.
    Returns 0 if text is NaN or empty.
    """
    if not isinstance(text, str) or not text.strip():
        return 0
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))


def token_based_splitter(
    df: pd.DataFrame,
    target_col: str,
    max_tokens: int = 8000,
    buffer_size: int = 100,
    model: str = "gpt-5-mini",
    within_group_col: str = None,
    new_col: str = "split_col"
) -> pd.DataFrame:
    """
    Splits text data into token-size-based chunks, optionally within each group.

    - If `within_group_col` is None, splits entire DataFrame sequentially.
    - If `within_group_col` is provided, splits *within each group value*
      and writes new subgroup labels (e.g., "GroupA_0", "GroupA_1") into `new_col`.

    Args:
        df (pd.DataFrame): Input DataFrame containing text data.
        target_col (str): Column containing text to evaluate.
        max_tokens (int): Maximum tokens per group.
        buffer_size (int): Buffer tokens added per row.
        model (str): Model name for tiktoken encoding.
        within_group_col (str): Optional column name to split within.
        new_col (str): Name of the new column for subgroup labels.

    Returns:
        pd.DataFrame: Updated DataFrame with a new `new_col` column.
    """
    if df.empty:
        print("⚠️ Empty DataFrame received. Returning unchanged.")
        df[new_col] = None
        return df

    def split_group(sub_df: pd.DataFrame, base_name: str = None):
        """Internal helper to perform token-based splitting within one subgroup."""
        current_tokens = 0
        chunk_index = 0
        split_labels = []

        for _, row in sub_df.iterrows():
            row_tokens = count_tokens(row[target_col], model) + buffer_size

            # Start a new subgroup if token limit exceeded
            if current_tokens + row_tokens > max_tokens:
                chunk_index += 1
                current_tokens = 0

            # Label = base group name + index (or just index if no base)
            if base_name:
                split_labels.append(f"{base_name}_{chunk_index}")
            else:
                split_labels.append(f"chunk_{chunk_index}")

            current_tokens += row_tokens

        sub_df = sub_df.copy()
        sub_df[new_col] = split_labels
        return sub_df

    # ---- Main logic ----
    split_dfs = []

    if within_group_col:
        for group_name, group_df in df.groupby(within_group_col):
            split_dfs.append(split_group(group_df, base_name=group_name))
    else:
        split_dfs.append(split_group(df))

    result = pd.concat(split_dfs, ignore_index=True)

    if within_group_col:
        print(f"✅ Token-based splitting complete within '{within_group_col}' groups.")
        print(f"   Total unique split groups: {result[new_col].nunique()}")
    else:
        print(f"✅ Token-based splitting complete across entire DataFrame.")

    return result
