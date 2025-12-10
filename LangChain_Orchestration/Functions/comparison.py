import pandas as pd
from typing import List, Dict
from pydantic import BaseModel
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from client import client


# -------------------------------
# Schema for structured comparison
# -------------------------------
class GroupSummary(BaseModel):
    group_name: str
    summary: str

class ComparisonOutput(BaseModel):
    introduction: str
    key_findings: List[str]
    similarities: List[str]
    differences: List[str]
    group_summaries: List[GroupSummary]

# -------------------------------
# Comparison function
# -------------------------------
def comparison(df, 
               grouping_column: str,
               context_prompt: str,
               id_column: str = 'call_id',
               text_column: str = 'call_text') -> pd.DataFrame:
    
    # Group and concatenate texts
    grouped_texts = {}
    for group_value, group_df in df.groupby(grouping_column):
        texts = []
        for _, row in group_df.iterrows():
            texts.append(f"{row[id_column]}: {row[text_column]}")
        grouped_texts[group_value] = "\n\n".join(texts)
    
    # Build prompt with all groups
    group_prompt = "\n\n".join([f"Group {gv}:\n{text}" for gv, text in grouped_texts.items()])

    messages = [
        {
            "role": "system", 
            "content": "You are an AI assistant that compares and contrasts groups. Respond ONLY in structured JSON."
        },
        {
            "role": "user", 
            "content": f"""
        Context: {context_prompt}

        Here are the groups and their contents:
        {group_prompt}

        For each group, provide:
        1. comparison: how it is similar to other groups
        2. contrast: how it differs from other groups

        Return JSON in this format:
        {{
            "groups": [
                {{
                    "group_value": "name of group",
                    "comparison": "text describing similarities",
                    "contrast": "text describing differences"
                }}
            ]
        }}
        """}
    ]
    
    class GroupOutput(BaseModel):
        group_value: str
        comparison: str
        contrast: str
    
    class AllGroups(BaseModel):
        groups: List[GroupOutput]
    
    response = client.responses.parse(
        model="gpt-5-mini", 
        input=messages, 
        text_format=AllGroups
    )

    parsed = response.output_parsed
    
    # Create output df
    output_data = [{"group_value": g.group_value, "comparison": g.comparison, "contrast": g.contrast} for g in parsed.groups]
    comparison_df = pd.DataFrame(output_data)
    

    return comparison_df

# # Example usage
# if __name__ == "__main__":
#     # Create example data
#     example_df = pd.DataFrame({
#         'call_id': ['call_1', 'call_2', 'call_3', 'call_4'],
#         'follow_up_label': ['yes', 'no', 'yes', 'no'],
#         'follow_up_explanation': [
#             "Customer agreed to meet next Tuesday at 2pm",
#             "Customer was not interested in scheduling",
#             "Follow-up demo scheduled for next week",
#             "No clear next steps established"
#         ]
#     })
    
#     # Run comparison
#     result = comparison(
#         df=example_df,
#         grouping_column="follow_up_label",
#         text_column="follow_up_explanation", 
#         context_prompt="Compare calls where follow-up was scheduled vs not scheduled"
#     )
#     print("\nComparison Results:")
#     print(result)