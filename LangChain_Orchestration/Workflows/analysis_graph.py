# workflows/analysis_graph.py
from langgraph.graph import StateGraph
from typing import Dict, List, TypedDict


# Import your function modules
from LangChain_Orchestration.Functions.binary_classification import run_multiple_binary_classifiers
from LangChain_Orchestration.Functions.token_based_splitter import chunked_dfs
from LangChain_Orchestration.Functions.open_classification import open_ended_parallel
from LangChain_Orchestration.Functions.text_summarizer import summarize_column
from LangChain_Orchestration.Functions.comparison import comparison



# -----------------------------
# 1. Define Shared State
# -----------------------------
class CallAnalysisState(TypedDict):
    df: object                # Pandas DataFrame with call transcripts

    # Not sure about these, chatgpt recommended as high level results storage structure, 
    # but I think we prob will change after testing.
    """binary_results: object    # Results of binary classifiers
    open_results: object      # Results of open-ended classification
    summary: str              # Summary of all calls
    comparison: object        # Comparison results"""

# -----------------------------
# 2. Define Nodes
# -----------------------------
def binary_classification_node(
        state: CallAnalysisState,
        questions: List[Dict] = None,
        max_workers: int = 8):
    df = state["df"]

    # Example binary questions (customize to your needs)
    if questions is None:
        questions = [
        {"question": "Did the rep discuss pricing?", "label_col": "pricing_label", "explanation_col": "pricing_expl"},
        {"question": "Did the rep mention competitor products?", "label_col": "competitor_label", "explanation_col": "competitor_expl"},
        ]

    updated_df = run_multiple_binary_classifiers(df, questions, max_workers)
    state["df"] = updated_df
    return state


def open_classification_node(
        state: CallAnalysisState,
        context_prompt: str = "Classify the call into sales categories",
        input_data: str = "call_text",
        response_col: str = "open_response",
        max_workers: int = 8):
    df = state["df"]

    updated_df = open_ended_parallel(df, context_prompt, input_data, response_col, max_workers)
    state["df"] = updated_df
    return state


def summarization_node(
        state: CallAnalysisState,
        context_prompt: str = "Summarize the following sales calls",
        target_col="call_text", 
        id_col="call_id"):
    df = state["df"]

    summary = summarize_column(df, context_prompt, target_col, id_col)

    state["summary"] = summary
    return state


def comparison_node(
        state: CallAnalysisState,
        groups: dict = None,
        columns_to_analyze: list = None,
        context_prompt: str = "Compare the following call groups") -> CallAnalysisState:
    df = state["df"]

    # Default grouping if not provided
    if groups is None:
        if columns_to_analyze is None:
            raise ValueError("Default grouping requires multiple dataframes and shared columns to analyze on.")
        groups = {
            "Definitive Sale": df[df["binary_label"] == "true"],
            "Potential Interest": df[df["binary_label"] == "false"],
        }

    # Default columns to analyze if not provided
    if columns_to_analyze is None:
        raise ValueError("Default grouping requires shared columns to analyze on.")
    
        # maybe instead of erroring should default to all columns
        "columns_to_analyze = df.select_dtypes(include='object').columns.tolist()"

    comparison = comparison_function(groups, columns_to_analyze, context_prompt)
    state["comparison"] = comparison
    return state


# -----------------------------
# 3. Build the Graph
# -----------------------------
def build_analysis_graph():
    graph = StateGraph(CallAnalysisState)

    # Register nodes
    graph.add_node("binary_classification", binary_classification_node)
    graph.add_node("open_classification", open_classification_node)
    graph.add_node("summarization", summarization_node)
    graph.add_node("comparison", comparison_node)

    # Define workflow order
    graph.set_entry_point("binary_classification")
    graph.add_edge("binary_classification", "open_classification")
    graph.add_edge("open_classification", "summarization")
    graph.add_edge("summarization", "comparison")
    graph.set_finish_point("comparison")

    return graph.compile()


# -----------------------------
# 4. Run Example
# -----------------------------
if __name__ == "__main__":
    import pandas as pd

    # Example dataframe (replace with your real call transcripts)
    df = pd.read_csv("Data/Post-Clean Data/AllCallsCleaned.csv").head(50)

    initial_state = {"df": df}

    app = build_analysis_graph()
    final_state = app.invoke(initial_state)

    print("=== Final State ===")
    print(final_state)