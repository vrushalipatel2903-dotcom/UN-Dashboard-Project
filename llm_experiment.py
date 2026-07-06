import fitz  # PyMuPDF
import json
import requests
import re
import time

OLLAMA_URL = "http://localhost:11434/api/generate"

# The three models for the extra credit comparison
MODELS_TO_TEST = ["llama3", "mistral", "gemma"]

def ask_ollama(prompt, model):
    payload = {"model": model, "prompt": prompt, "stream": False, "format": "json"}
    start_time = time.time()
    response = requests.post(OLLAMA_URL, json=payload)
    end_time = time.time()
    
    if response.status_code == 200:
        return response.json()['response'], round(end_time - start_time, 2)
    return None, 0

def run_experiment(pdf_path):
    print("Reading PDF for LLM Comparison Experiment...")
    doc = fitz.open(pdf_path)
    # Grab just one large chunk of text to test across all 3 models
    text_chunk = doc[0].get_text() + doc[1].get_text() + doc[2].get_text()
    clean_text = re.sub(r'\s+', ' ', text_chunk).strip()[:2000] 

    experiment_prompt = f"""You are an expert UN Development Data Analyst. Analyze this text.
    Output STRICTLY as a valid JSON object with:
    "key_strengths" (list of strings),
    "key_challenges" (list of strings).
    Text: {clean_text}"""

    results = []

    for model in MODELS_TO_TEST:
        print(f"\nTesting Model: {model}...")
        raw_output, time_taken = ask_ollama(experiment_prompt, model)
        
        # 1. Test Verbosity (How many characters did it output?)
        verbosity = len(raw_output) if raw_output else 0
        
        # 2. Test Stability (Did it output valid JSON?)
        is_stable = False
        richness_score = 0
        try:
            parsed_json = json.loads(raw_output)
            is_stable = True
            # 3. Test Richness (How many combined strengths/challenges did it find?)
            richness_score = len(parsed_json.get('key_strengths', [])) + len(parsed_json.get('key_challenges', []))
        except:
            is_stable = False

        results.append({
            "model": model,
            "time_seconds": time_taken,
            "verbosity_chars": verbosity,
            "json_stability": "Passed" if is_stable else "Failed",
            "richness_count": richness_score
        })
        print(f"--> Done! Stability: {is_stable}, Richness: {richness_score}, Verbosity: {verbosity} chars")

    # Save results to a file for your report
    with open('llm_comparison_results.json', 'w') as f:
        json.dump(results, f, indent=4)
    print("\nExperiment complete! Check llm_comparison_results.json to write your report section.")

if __name__ == "__main__":
    run_experiment("philippines2005en.pdf")
