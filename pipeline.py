import fitz  # PyMuPDF
import json
import requests
import re

OLLAMA_URL = "http://localhost:11434/api/generate"
EXTRACTOR_MODEL = "llama3"
EVALUATOR_MODEL = "mistral"

def extract_and_chunk_pdf(pdf_path, chunk_size=3000):
    print("Reading PDF...")
    doc = fitz.open(pdf_path)
    full_text = ""
    for page in doc:
        text = page.get_text()
        clean_text = re.sub(r'\s+', ' ', text).strip()
        full_text += clean_text + " "
    return [full_text[i:i+chunk_size] for i in range(0, len(full_text), chunk_size)]

def ask_ollama(prompt, model, require_json=False):
    payload = {"model": model, "prompt": prompt, "stream": False}
    if require_json: payload["format"] = "json"
        
    response = requests.post(OLLAMA_URL, json=payload)
    if response.status_code == 200:
        return response.json()['response']
    else:
        raise Exception(f"Ollama API Error: {response.text}")

def process_report(pdf_path):
    chunks = extract_and_chunk_pdf(pdf_path)
    final_data = []
    
    # Just running 1 chunk for demonstration to save your computer's processing time
    for i, chunk in enumerate(chunks[:1]): 
        print(f"Processing chunk {i+1} with Llama3...")
        
        extractor_prompt = f"""You are an expert UN Development Data Analyst. Analyze this text.
        Output STRICTLY as a valid JSON object with these keys:
        "themes_distribution" (dict of ints: education, health, inequality, economy, gender, climate, employment),
        "key_strengths" (list of strings),
        "key_challenges" (list of strings),
        "numerical_indicators" (dict: HDI_value, HDI_rank, life_expectancy_years, expected_years_of_schooling, gni_per_capita, population),
        "demographic_trends" (list of dicts with 'year', 'metric_name', 'value').
        Text: {chunk}"""
        
        extracted_raw = ask_ollama(extractor_prompt, EXTRACTOR_MODEL, require_json=True)
        extracted_json = json.loads(extracted_raw)
            
        print("Evaluating with Mistral...")
        evaluator_prompt = f"""Review the JSON output against the text. Provide consistency_score, completeness_score, and factual_alignment_score (0-10) and a critique string.
        Output strictly as JSON. Text: {chunk} \n Extracted: {extracted_raw}"""
        
        evaluation_raw = ask_ollama(evaluator_prompt, EVALUATOR_MODEL, require_json=True)
        evaluation_json = json.loads(evaluation_raw)
            
        final_data.append({"chunk_id": i, "extraction": extracted_json, "evaluation": evaluation_json})
        
    with open('processed_report_data.json', 'w') as f:
        json.dump(final_data, f, indent=4)
    print("Pipeline complete. Check processed_report_data.json")

if __name__ == "__main__":
    process_report("philippines2005en.pdf")
