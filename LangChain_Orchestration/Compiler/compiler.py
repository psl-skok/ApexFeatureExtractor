import pandas as pd
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Compiler.function_registry import FUNCTION_REGISTRY



def compile_and_run(path_request: list[dict], initial_df: pd.DataFrame):
    state = {"starting_df": (initial_df, None, None)}
    execution_log = []

    for step in path_request:
        fn_name = step["function"]
        args = step.get("args", {})
        input_name = step['input_df_name']
        input_df = state[input_name][0]
        output_name = step["output_df_name"]

        if fn_name not in FUNCTION_REGISTRY:
            raise ValueError(f"Unknown function: {fn_name}")

        fn = FUNCTION_REGISTRY[fn_name]

        # Assume all functions take df as first arg
        output_df = fn(input_df, **args)

        grouping_col = args.get("grouping_column", None)
        state[output_name] = (output_df, input_name, grouping_col)
        execution_log.append({"function": fn_name, "status": "success"})


    return state, execution_log


if __name__ == "__main__":
    import os
    
    current_dir = os.path.dirname(__file__)
    csv_path = os.path.join(current_dir, "../Compiler/10CallsCleaned.csv")
    print(f"📁 Loading CSV from: {csv_path}")
    df = pd.read_csv(csv_path)
    
    # Updated sample path_request with proper names
    path_request = [
        # {
        #     "function": "mece_theme_analysis",
        #     "args": {
        #         "transcript_column": "call_text",
        #         "context_prompt": "Identify the primary value that customers expect to find from the Optimum product in this sales call.",
        #         "id_column": "call_id",
        #         "target_column": "Theme_Analysis",
        #         "themes_per_transcript": 1,
        #         "max_workers": 4
        #     },
        #     "input_df_name": "starting_df",
        #     "output_df_name": "starting_df"
        # }
        # {
        #     "function": "token_based_splitter",
        #     "args": {
        #         "target_col": "call_text",
        #         "max_tokens": 8000,
        #         "buffer_size": 100,
        #         "model": "gpt-4o-mini",
        #         "new_col": "Split_Group"
        #     },
        #     "input_df_name": "starting_df",
        #     "output_df_name": "starting_df"
        # }
        # {
        #     "function": "categorical_classification",
        #     "args": {
        #         "classifications": ["high", "medium", "low"],
        #         "context_prompt": "Classify the call quality based on customer engagement and satisfaction.",
        #         "input_data": "call_text",
        #         "id_column": "call_id",
        #         "max_workers": 4,
        #     },
        #     "input_df_name": "starting_df",
        #     "output_df_name": "starting_df"
        # },
        # {
        #     "function": "unsupervised_grouping",
        #     "args": {
        #         "input_column": "call_text",
        #         "context_prompt": "Group these sales calls into 3–5 categories based on the overall "
        #                           "nature of the customer interaction, such as their intent, interest level, "
        #                           "or topic of discussion. Create meaningful and descriptive group names that "
        #                           "capture each pattern.",
        #         "id_column": "call_id",
        #         "target_column": "sentiment_group",
        #     },
        #     "input_df_name": "starting_df",
        #     "output_df_name": "starting_df"
        # },
        # {
        #     "function": "token_based_splitter",
        #     "args": {
        #         "target_col": "call_text",
        #         "max_tokens": 8000,
        #         "buffer_size": 100,
        #         "model": "gpt-4o-mini",
        #         "within_group_col": "sentiment_group"
        #     },
        #     "input_df_name": "starting_df",
        #     "output_df_name": "starting_df"
        # },

        # {
        #     "function": "filter",
        #     "args": {
        #         "target_col": "sentiment_group",
        #         "filter_values": ["Account Management and Changes", "Service Setup and Installation"]  # Keep only Positive and Neutral groups
        #     },
        #     "input_df_name": "starting_df",
        #     "output_df_name": "filtered_df"
        # },

        # {
        #     "function": "summarizer",
        #     "args": {
        #         "target_col": "call_text",
        #         "group_by_col": "split_col", 
        #         "context_prompt": (
        #             "Write a concise summary that describes the main theme, customer behavior, and "
        #             "overall tone of each group of sales calls."
        #         ),
        #     },
        #     "input_df_name": "filtered_df",
        #     "output_df_name": "summarized_interaction_df"
        # }

        # {
        #     "function": "category_extractor",
        #     "args": {
        #         "transcript_column": "call_text",
        #         "context_prompt": "Extract the sales techniques used by the sales technician discussed in the transcript.",
        #         "target_column": "extracted_sales_techniques",
        #         "max_workers": 4,
        #     },
        #     "input_df_name": "starting_df",
        #     "output_df_name": "starting_df"  
        # }
        # {
        #     "function": "binary_classification",
        #     "args": {
        #         "context_prompt": "Was a follow up scheduled on the call, be strict. Only say yes if you are 100 percent confident",
        #         "input_data": "call_text",
        #         "positive_label": "yes, follow up was scheduled",
        #         "negative_label": "no, follow up was not scheduled",
        #         "explanation_col": "follow_up_explanation",
        #         "label_col": "follow_up_label",
        #         "max_workers": 4,
        #     },
        #     "input_df_name": "starting_df",
        #     "output_df_name": "starting_df"
        # },
        # {
        #     "function": "open_classification",
        #     "args": {
        #         "context_prompt": "Score the explanation 1-5 on how solid/accurate they are",
        #         "response_col": "key_themes_response",
        #         "input_data": "follow_up_explanation",
        #         "max_workers": 4,
        #     },
        #     "input_df_name": "starting_df",
        #     "output_df_name": "starting_df"
        # },
        # # {
        # #     "function": "unique_value_splitter",
        # #     "args": {"splitter_column": "follow_up_label"},
        # #     "input_df_name": "starting_df",
        # #     "output_df_name": "starting_df"
        # # },
        # {
        #     "function": "comparison",
        #     "args": {
        #         "grouping_column": "follow_up_label",
        #         "text_column": "key_themes_response",
        #         "context_prompt": (
        #             "Compare calls where a follow-up *was* scheduled "
        #             "to those where it *wasn’t*. What differentiates them?"
        #         ),
        #         "id_column": "call_id",
        #     },
        #     "input_df_name": "starting_df",
        #     "output_df_name": "comparison_results"
        # },
    ]
    
    state, log = compile_and_run(path_request, df)
    
    print("\n✅ FINAL STATE KEYS:", list(state.keys()))
    for name, (df, parent, group_col) in state.items():
        print(f"\n--- {name} (parent: {parent}, group_col: {group_col}) ---")
        print(df.head())