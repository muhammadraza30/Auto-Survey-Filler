from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import random
import time
import os
import re
import spacy
from transformers import pipeline
from dotenv import load_dotenv
from abstract_survey_handler import AbstractSurveyHandler
import google.generativeai as genai

dotenv_path = os.path.join("src","keys.env")
found_dotenv = load_dotenv(dotenv_path=dotenv_path, verbose=True)
if not found_dotenv:
    print(f"ERROR: Could not find or load the .env file at {dotenv_path}")
    # Optionally, print the current working directory to help debug
    print(f"Current Working Directory: {os.getcwd()}")

# Attempt to retrieve the API key
api_key = os.getenv("GENAI_API_KEY")

if api_key:
    print("Successfully loaded GENAI_API_KEY.")
    genai.configure(api_key=api_key)
else:
    print("ERROR: GENAI_API_KEY not found in environment variables.")
# genai.configure(api_key="GENAI_API_KEY")  # replace with your actual key
genai.configure(api_key=os.getenv("GENAI_API_KEY"))  # replace with your actual key

# Load spaCy model for NER
nlp = spacy.load("en_core_web_sm")

# Load transformer model for semantic similarity
semantic_search = pipeline('zero-shot-classification', model='facebook/bart-large-mnli')

class SurveyHandler(AbstractSurveyHandler):
    def __init__(self, driver, contact):
        self.driver = driver
        self.contact = contact
        self.form_context = self.get_form_context() or "Google Form for a general survey. Answer logically."
        self.keyword_map = {
            'name': 'Name', 'email': 'Email', 'phone': 'Phone',
            'age': 'Age', 'gender': 'Gender', 'city': 'City',
            'location': 'City', 'education': 'Education',
            'qualification': 'Education', 'profession': 'Profession',
            'job': 'Profession', 'occupation': 'Profession'
        }
        # Initialize the model once here if you want to reuse it across calls
        # Or keep initializing it in get_ai_answer if that works for your setup
        try:
             # Use the model name that works for you
             self.model = genai.GenerativeModel(model_name='models/gemini-2.0-flash-exp')
        except Exception as e:
             print(f"[Gemini Model Init Error] {e}")
             self.model = None # Handle cases where model init might fail

    def extract_entities(self, text):
        doc = nlp(text)
        return {ent.label_: ent.text for ent in doc.ents}

    def match_field_with_ner(self, question_text):
        entities = self.extract_entities(question_text)
        for label in entities:
            if label.lower() == 'person' and 'Name' in self.contact:
                return self.contact['Name']
            if label.lower() == 'email' and 'Email' in self.contact:
                return self.contact['Email']
        return None

    def match_field_with_transformer(self, question_text):
        candidate_labels = ['Name', 'Email', 'Phone', 'Age', 'Gender', 'City', 'Education', 'Profession']
        result = semantic_search(question_text, candidate_labels)
        
        # Get the top candidate and its score
        top_label = result['labels'][0]
        top_score = result['scores'][0]
        
        # Set a threshold (e.g., 0.7); if the confidence is below this, we do not trust the match.
        threshold = 0.7  
        if top_score >= threshold:
            return self.contact.get(top_label, None)
        return None

    
    def get_form_context(self):    
        try:
          form_title = ""
          form_desc = ""
          try:
              form_title = self.driver.find_element(By.XPATH, "//div[contains(@class, 'M7eMe')]").text.strip()
          except: pass
          try:
              form_desc = self.driver.find_element(By.XPATH, "//div[contains(@class, 'CDELXb')]").text.strip()
          except: pass
          return f"Form Title: {form_title}\nForm Description: {form_desc}"
        except Exception as e:
            print(f"[Form Context Error] {e}")
            return ""

    def get_ai_answer(self, question_text):
        # Check if model was initialized successfully
        if not self.model:
             print("[Gemini Error] Model not initialized.")
             return "Not Sure"

        # --- Revised Prompt ---
        prompt = (
            "You are simulating a person filling out an online survey form. Your persona is based on the 'Contact Info' provided."
            "Your task is to provide ONLY the direct answer text that should be typed into the form field for the given question. "
            "The answer must be concise, relevant to the question, and consistent with the persona and form context. "
            "CRITICAL: DO NOT include any introductory phrases, explanations, justifications, context, reasoning, or self-references like 'Based on...', 'Given my background...', 'Considering...', 'As an AI...', 'My answer is...', 'I would say...', etc. "
            "Just provide the plain answer text itself, exactly as it should appear in the form field.\n\n"
            f"Form Context:\n{self.form_context}\n\n"
            f"Persona (Contact Info):\n{self.contact}\n\n" # Using 'Persona' for clarity
            f"Question:\n{question_text}\n\n"
            "Direct Answer for Form Field:" # Changed label to reinforce output format
        )

        try:
            response = self.model.generate_content(prompt) # Use self.model
            raw_answer = response.text

            # --- Cleaning Logic (Keep this as it removes *, # and normalizes whitespace) ---
            cleaned_answer = raw_answer.replace('*', '').replace('#', '')
            cleaned_answer = re.sub(r'^[*\s]+|[*\s]+$', '', cleaned_answer) # Remove leading/trailing format chars/space
            cleaned_answer = ' '.join(cleaned_answer.split()) # Normalize whitespace
            # --- End of Cleaning Logic ---

            # Remove potential quote marks if the AI wraps the answer
            if len(cleaned_answer) > 1 and cleaned_answer.startswith('"') and cleaned_answer.endswith('"'):
                cleaned_answer = cleaned_answer[1:-1]
            if len(cleaned_answer) > 1 and cleaned_answer.startswith("'") and cleaned_answer.endswith("'"):
                cleaned_answer = cleaned_answer[1:-1]

            # Return the cleaned answer, ensuring it's not empty
            return cleaned_answer if cleaned_answer else "Not Sure"

        except Exception as e:
            # Check for specific API errors if possible, e.g., blocked content
            if hasattr(e, 'message') and 'block_reason' in e.message.lower():
                 print(f"[Gemini Safety Block] Prompt or response blocked. Question: {question_text}")
                 return "Blocked by safety filter" # Or another specific fallback
            else:
                 print(f"[Gemini Error] {e}")
            return "Not Sure" # Fallback answer    

    def handle_question(self, question_element):
        try:
            text_inputs = question_element.find_elements(By.CSS_SELECTOR, "input[type='text'], textarea")
            if text_inputs:
                question_text = question_element.text.strip()
                
                # First try transformer with threshold.
                matched_value = self.match_field_with_transformer(question_text)
                
                # Optionally, try NER (if you find that it gives a very specific result)
                if not matched_value:
                    matched_value = self.match_field_with_ner(question_text)
                
                # If no match is found, request an answer from the AI.
                if not matched_value:
                    matched_value = self.get_ai_answer(question_text)
                
                text_inputs[0].send_keys(matched_value)
                return

            radio_options = question_element.find_elements(By.CSS_SELECTOR, "div[role='radiogroup'] div[role='radio']")
            if radio_options:
                choice = random.choice(radio_options)
                WebDriverWait(self.driver, 5).until(EC.element_to_be_clickable(choice)).click()
                return

            checkbox_options = question_element.find_elements(By.CSS_SELECTOR, "div[role='checkbox']")
            if checkbox_options:
                for option in random.sample(checkbox_options, min(random.randint(1, 3), len(checkbox_options))):
                    option.click()
                return

            dropdown = question_element.find_elements(By.CSS_SELECTOR, "div[role='listbox']")
            if dropdown:
                dropdown[0].click()
                time.sleep(0.2)
                options = question_element.find_elements(By.CSS_SELECTOR, "div[role='option']")
                if options:
                    random.choice(options).click()
                return

            scale_buttons = question_element.find_elements(By.CSS_SELECTOR, "div[role='radiogroup'] div[role='radio']")
            if scale_buttons:
                weights = [1, 2, 3, 3, 2, 1][:len(scale_buttons)]
                random.choices(scale_buttons, weights=weights, k=1)[0].click()
        except Exception as e:
            print(f"[Handle Question Error] {e}")

    def handle_multi_page_form(self):
        while True:
            questions = self.driver.find_elements(By.CSS_SELECTOR, "div[role='listitem']")
            for question in questions:
                self.handle_question(question)

            try:
                next_btn = self.driver.find_elements(By.XPATH, "//div[@role='button']//span[contains(., 'Next')]")
                if next_btn:
                    next_btn[0].click()
                    time.sleep(1)
                    continue

                submit_btn = self.driver.find_elements(By.XPATH, "//div[@role='button']//span[contains(., 'Submit')]")
                if submit_btn:
                    submit_btn[0].click()
                    return True

                fallback_submit = self.driver.find_elements(By.CSS_SELECTOR, "div[role='button']")
                for btn in fallback_submit:
                    if "Submit" in btn.text:
                        btn.click()
                        return True

                print("No Next or Submit button found.")
                return False

            except Exception as e:
                print(f"[Form Navigation Error] {e}")
                return False
