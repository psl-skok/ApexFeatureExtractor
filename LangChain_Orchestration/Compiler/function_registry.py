# function_registry.py
from Functions.binary_classification import run_multiple_binary_classifiers
from Functions.categorical_classification import categorical_classification
from Functions.category_extractor import category_extractor
from Functions.comparison import comparison
from Functions.mece_theme_analysis import mece_theme_analysis
from Functions.open_classification import open_classification
from Functions.summarizer import summarize_column_by_group
from Functions.token_based_splitter import token_based_splitter
from Functions.unique_value_splitter import unique_value_splitter
from Functions.unsupervised_grouping import unsupervised_grouping
from Functions.filter import filter

FUNCTION_REGISTRY = {
    "binary_classification": run_multiple_binary_classifiers,
    "categorical_classification": categorical_classification,
    "category_extractor": category_extractor,
    "comparison": comparison,
    "mece_theme_analysis": mece_theme_analysis,
    "open_classification": open_classification,
    "summarizer": summarize_column_by_group,
    "token_based_splitter": token_based_splitter,
    "unique_value_splitter": unique_value_splitter,
    "unsupervised_grouping": unsupervised_grouping,
    "filter": filter,
}