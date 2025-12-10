# test_compiler.py
import os
import pandas as pd
from LangChain_Orchestration.Compiler.compiler import compile_and_run

# Get the folder where THIS script lives
current_dir = os.path.dirname(__file__)
csv_path = os.path.join(current_dir, "10CallsCleaned.csv")
print(f"📁 Loading CSV from: {csv_path}")
df = pd.read_csv(csv_path)


path_request = [
    {
        "function": "binary_classification",
        "args": {
            "questions": [
                {
                    "question": "Was a follow up scheduled on the call, be strict. Only say yes if you are 100 percent confident",
                    "label_col": "follow_up_label",
                    "explanation_col": "follow_up_explanation",
                }
            ]
        },
    },
    {
        "function": "open_classification",
        "args": {
            "context_prompt": "Score the explanation 1-5 on how solid/accurate they are",
            "response_col": "key_themes_response",
            "input_data": "follow_up_explanation",
            "max_workers": 4,
        },
    },
    {
        "function": "unique_value_splitter",
        "args": {"splitter_column": "follow_up_label"},
    },
    {
        "function": "comparison",
        "args": {
            "columns_to_analyze": [
                "follow_up_label",
                "follow_up_explanation",
                "key_themes_response",
            ],
            "context_prompt": (
                "Compare calls where a follow-up *was* scheduled "
                "to those where it *wasn’t*. What differentiates them?"
            ),
        },
        "output_name": "comparison",
    },
]

# -------------------------------------
# Run the compiler pipeline
# -------------------------------------
state, log = compile_and_run(path_request, df)


# -------------------------------------
# Output results
# -------------------------------------
print("\n✅ FINAL RESULT:")
print(state["df"].head() if "df" in state else state)

print("\n🧾 EXECUTION LOG:")
for entry in log:
    print(entry)

print("\n🧠 COMPARISON RESULTS:")
print(state["comparison"].head())
