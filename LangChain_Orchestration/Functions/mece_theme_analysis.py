import pandas as pd
from typing import Dict, List, Optional
from pydantic import BaseModel
import json
from concurrent.futures import ThreadPoolExecutor
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from client import client

# =========================
# SCHEMAS
# =========================
class Theme(BaseModel):
    themeName: str
    themeDescription: str

class MECEThemeAnalysis(BaseModel):
    themes: List[Theme]
    theme_mappings: Dict[str, List[str]]

# -------------------------------
# Helper Functions
# -------------------------------
def _make_api_call(messages: List[Dict], model: str = "gpt-4o-mini", max_tokens: int = 2000) -> Dict:
    """Centralized API call with error handling."""
    try:
        response = client.chat.completions.create(
            model=model,
            input=messages,
            temperature=0,
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content.strip())
    except Exception as e:
        print(f"API call failed: {e}")
        return {}

def _create_theme_prompt(context_prompt: str, transcript: str) -> tuple[str, str]:
    """Create system and user prompts for theme generation."""
    system_prompt = f"""You are an expert at creating MECE categorization frameworks.

Task: {context_prompt}

Generate 3-10 themes that are:
- Mutually Exclusive: No overlap
- Collectively Exhaustive: All content fits

Return JSON: {{"themes": [{{"themeName": "...", "themeDescription": "..."}}], "mece_validation": "..."}}"""

    user_prompt = f"Analyze this transcript and create MECE themes:\n\n{transcript}"
    
    return system_prompt, user_prompt

def _create_classification_prompt(context_prompt: str, themes: List[Theme], transcript: str, single_theme: bool = True) -> tuple[str, str]:
    """Create prompts for transcript classification."""
    themes_text = "\n".join([f"- {t.themeName}: {t.themeDescription}" for t in themes])
    instruction = "Assign exactly ONE theme" if single_theme else "Assign one or more themes"
    
    system_prompt = f"""Classify transcript using these themes:

{themes_text}

Rules:
1. {instruction}
2. Use only provided themes
3. Assign transcript to at least one theme

Return JSON: {{"classifications": {{"id": ["Theme"]}}}}"""

    user_prompt = f"Context: {context_prompt}\n\nTranscript:\n{transcript}"
    
    return system_prompt, user_prompt

# -------------------------------
# Core Theme Analysis Functions
# -------------------------------
def _generate_themes_parallel(dataframe: pd.DataFrame, transcript_column: str, context_prompt: str, max_workers: int = 4) -> List[Theme]:
    """Generate themes using parallel processing - no batching, each transcript processed individually."""
    def process_single_transcript(row):
        transcript = row[transcript_column]
        system_prompt, user_prompt = _create_theme_prompt(context_prompt, transcript)
        
        response = _make_api_call([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ])
        
        return [Theme(**theme) for theme in response.get("themes", [])]
    
    print(f"Generating themes from {len(dataframe)} individual transcripts...")
    
    # Process each transcript individually in parallel
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        transcript_results = list(executor.map(process_single_transcript, [row for _, row in dataframe.iterrows()]))
    
    # Flatten results
    all_themes = [theme for transcript_themes in transcript_results for theme in transcript_themes]
    
    print(f"Generated {len(all_themes)} total themes from individual transcripts")
    
    # Merge similar themes
    if len(all_themes) > 1:
        return _merge_themes(all_themes, context_prompt)
    
    return all_themes

def _merge_themes(themes: List[Theme], context_prompt: str) -> List[Theme]:
    """Merge similar themes semantically."""
    themes_text = "\n".join([f"- {t.themeName}: {t.themeDescription}" for t in themes])
    
    system_prompt = f"""Merge similar themes while maintaining MECE principles.

Task: {context_prompt}

Merge these themes into 3-10 final themes:
{themes_text}

Return JSON: {{"themes": [{{"themeName": "...", "themeDescription": "..."}}], "mece_validation": "..."}}"""

    user_prompt = "Create final MECE framework by merging similar themes."
    
    response = _make_api_call([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ])
    
    return [Theme(**theme) for theme in response.get("themes", themes)]

def _classify_transcripts_parallel(dataframe: pd.DataFrame, transcript_column: str, themes: List[Theme], 
                                 context_prompt: str, id_column: str, single_theme: bool = True, 
                                 max_workers: int = 4) -> Dict[str, List[str]]:
    """Classify transcripts using parallel processing - no batching, each transcript processed individually."""
    def process_single_transcript(row):
        transcript = row[transcript_column]
        transcript_id = str(row[id_column])
        system_prompt, user_prompt = _create_classification_prompt(context_prompt, themes, transcript, single_theme)
        
        response = _make_api_call([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ])
        
        # Extract classification for this single transcript
        classifications = response.get("classifications", {})
        # The response should have a single "id" key, but we'll use the actual transcript_id
        if "id" in classifications:
            return {transcript_id: classifications["id"]}
        else:
            return {transcript_id: ["Unclassified"]}
    
    print(f"Classifying {len(dataframe)} individual transcripts...")
    
    # Process each transcript individually in parallel
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        transcript_results = list(executor.map(process_single_transcript, [row for _, row in dataframe.iterrows()]))
    
    # Merge all classifications
    all_classifications = {}
    for transcript_result in transcript_results:
        all_classifications.update(transcript_result)
    
    return all_classifications

# -------------------------------
# Main MECE Theme Analysis Function
# -------------------------------
def mece_theme_analysis(
    dataframe: pd.DataFrame,
    transcript_column: str,
    context_prompt: str,
    id_column: str = None,
    target_column: str = "Theme_Analysis",
    themes_per_transcript: List[int] = [1],
    max_workers: int = 4
) -> pd.DataFrame:
    """
    Optimized MECE theme analysis with parallel processing - no batching.
    Each transcript is processed individually in parallel.
    
    Args:
        dataframe: DataFrame with transcript data
        transcript_column: Column containing transcript text
        context_prompt: Analysis context/question
        id_column: ID column (defaults to first column)
        target_column: Output column name
        themes_per_transcript: 1 for single theme, "multiple" for multiple themes
        max_workers: Number of parallel workers
    
    Returns:
        DataFrame with themes
    """
    id_column = id_column or dataframe.columns[0]
    single_theme = themes_per_transcript == 1
    
    print(f"MECE Analysis: {len(dataframe)} transcripts (no batching, parallel processing)")
    
    # Phase 1: Generate themes
    themes = _generate_themes_parallel(dataframe, transcript_column, context_prompt, max_workers)
    if not themes:
        return dataframe.assign(**{target_column: "Error: No themes generated"}), MECEThemeAnalysis(
            themes=[], theme_mappings={}
        )
    
    print(f"Generated {len(themes)} themes")
    
    # Phase 2: Classify transcripts
    theme_mappings = _classify_transcripts_parallel(
        dataframe, transcript_column, themes, context_prompt, id_column, single_theme, max_workers
    )
    
    # Apply themes to dataframe
    result_df = dataframe.copy()
    if single_theme:
        theme_map = {str(id_val): themes[0] if themes else "Unclassified" 
                    for id_val, themes in theme_mappings.items()}
        result_df[target_column] = result_df[id_column].astype(str).map(theme_map).fillna("Unclassified")
    else:
        theme_map = {str(id_val): ", ".join(themes) if themes else "Unclassified" 
                    for id_val, themes in theme_mappings.items()}
        result_df[target_column] = result_df[id_column].astype(str).map(theme_map).fillna("Unclassified")
    
    return result_df

""", MECEThemeAnalysis(
        themes=themes,
        theme_mappings=theme_mappings
    )"""

