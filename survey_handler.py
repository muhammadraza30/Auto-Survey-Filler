from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import random
import time
from abstract_survey_handler import AbstractSurveyHandler
from dotenv import load_dotenv
import spacy
import random
import time
import csv
from transformers import pipeline
from abstract_survey_handler import AbstractSurveyHandler
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import openai
import os
spacy.cli.download("en_core_web_sm")

# Load spaCy model for NER
nlp = spacy.load("en_core_web_sm")

# Transformer model for semantic similarity
semantic_search = pipeline('zero-shot-classification', model='facebook/bart-large-mnli')

load_dotenv(dotenv_path='keys.env') 
# OpenAI GPT for question-answering
openai.api_key = os.getenv('OPENAI_API_KEY')

class SurveyHandler(AbstractSurveyHandler):
    def __init__(self, driver, contact):
        self.driver = driver
        self.contact = contact
        self.keyword_map = {
            'name': 'Name',
            'email': 'Email',
            'phone': 'Phone',
            'age': 'Age',
            'gender': 'Gender',
            'city': 'City',
            'location': 'City',
            'education': 'Education',
            'qualification': 'Education',
            'profession': 'Profession',
            'job': 'Profession',
            'occupation': 'Profession',
            'feedback': 'Feedback'
        }

    def extract_entities(self, text):
        doc = nlp(text)
        entities = {ent.label_: ent.text for ent in doc.ents}
        return entities

    def match_field_with_ner(self, question_text):
        entities = self.extract_entities(question_text)
        for label, entity in entities.items():
            if label.lower() in ['person', 'email']:
                if label.lower() == 'person' and 'Name' in self.contact:
                    return self.contact['Name']
                if label.lower() == 'email' and 'Email' in self.contact:
                    return self.contact['Email']
        return None

    def match_field_with_transformer(self, question_text):
        candidate_labels = ['Name', 'Email', 'Phone', 'Age', 'Gender', 'City', 'Education', 'Profession', 'Feedback']
        result = semantic_search(question_text, candidate_labels)
        # Return the field with the highest score
        return self.contact.get(result['labels'][0], None)

    def get_ai_answer(self, question_text):
        try:
            response = openai.Completion.create(
                engine="text-davinci-003",  # or use another available engine
                prompt=f"Answer this question: {question_text}",
                max_tokens=100,
                temperature=0.7
            )
            return response.choices[0].text.strip()
        except Exception as e:
            print(f"Error with OpenAI API: {str(e)}")
            return "I don't know the answer to this question."

    def handle_question(self, question_element):
        radio_options = question_element.find_elements(By.CSS_SELECTOR, "div[role='radiogroup'] div[role='radio']")
        if radio_options:
            radio = random.choice(radio_options)
            try:
                WebDriverWait(self.driver, 5).until(EC.element_to_be_clickable(radio))
                radio.click()
            except:
                self.driver.execute_script("arguments[0].click();", radio)
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

        text_input = question_element.find_elements(By.CSS_SELECTOR, "input[type='text'], textarea")
        if text_input:
            question_text = question_element.text
            matched_value = self.match_field_with_ner(question_text) or self.match_field_with_transformer(question_text)

            # If no match found in CSV, get AI answer
            if not matched_value:
                matched_value = self.get_ai_answer(question_text)

            text_input[0].send_keys(matched_value)
            return

        scale_buttons = question_element.find_elements(By.CSS_SELECTOR, "div[role='radiogroup'] div[role='radio']")
        if scale_buttons:
            weights = [1, 2, 3, 3, 2, 1][:len(scale_buttons)]
            choice = random.choices(scale_buttons, weights=weights, k=1)[0]
            choice.click()
            return

    def handle_multi_page_form(self):
        while True:
            questions = self.driver.find_elements(By.CSS_SELECTOR, "div[role='listitem']")
            for question in questions:
                self.handle_question(question)
            
            try:
                next_buttons = self.driver.find_elements(By.XPATH, "//div[@role='button']//span[contains(., 'Next')]")
                if next_buttons:
                    next_buttons[0].click()
                    time.sleep(1)
                    continue
                
                submit_buttons = self.driver.find_elements(By.XPATH, "//div[@role='button']//span[contains(., 'Submit')]")
                if submit_buttons:
                    submit_buttons[0].click()
                    return True
                
                submit_buttons = self.driver.find_elements(By.CSS_SELECTOR, "div[role='button']")
                for btn in submit_buttons:
                    if "Submit" in btn.text:
                        btn.click()
                        return True
                
                print("No Next or Submit button found")
                return False
                
            except Exception as e:
                print(f"Error navigating form pages: {str(e)}")
                return False
