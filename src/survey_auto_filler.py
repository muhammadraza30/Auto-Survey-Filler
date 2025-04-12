from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
import time
import csv
import random
from survey_handler import SurveyHandler
from abstract_survey_auto_filler import AbstractSurveyAutoFiller

class SurveyAutoFiller(AbstractSurveyAutoFiller):
    def auto_fill_survey(self, survey_url: str, csv_file: str, num_fill: int) -> None:
        chrome_options = Options()
        chrome_options.add_argument("user-data-dir=C:\\temp\\chrome_profile")
        chrome_options.add_argument("--start-maximized")

        driver = webdriver.Chrome(options=chrome_options)
        wait = WebDriverWait(driver, 10)

        try:
            # Load contacts from CSV or generate default ones if file is not found or is empty
            try:
                with open(csv_file, mode='r', encoding='utf-8') as f:
                    contacts = list(csv.DictReader(f))
                    if not contacts:
                        print("Error: CSV file is empty")
                        return

                    if 'Name' not in contacts[0] or 'Email' not in contacts[0]:
                        print("Warning: CSV missing 'Name' or 'Email'. Using default contacts.")
                        contacts = [{'Name': f'User {i}', 'Email': f'user{i}@example.com'} for i in range(1, num_fill + 1)]
            except FileNotFoundError:
                print(f"CSV file '{csv_file}' not found. Using defaults.")
                contacts = [{'Name': f'User {i}', 'Email': f'user{i}@example.com'} for i in range(1, num_fill + 1)]

            used_emails = set()
            successful_submissions = 0

            while successful_submissions < num_fill and contacts:
                available_contacts = [c for c in contacts if c['Email'] not in used_emails]

                if not available_contacts:
                    print("No more unique contacts.")
                    break

                contact = random.choice(available_contacts)
                print(f"Filling form {successful_submissions + 1}/{num_fill} with {contact['Name']}")

                # Navigate to the survey URL and use SurveyHandler to handle questions
                driver.get(survey_url)
                time.sleep(1)

                handler = SurveyHandler(driver, contact)
                if handler.handle_multi_page_form():
                    used_emails.add(contact['Email']) 
                    successful_submissions += 1
                else:
                    print("Failed submission")

                time.sleep(1)

        finally:
            driver.quit()
            print(f"Completed {successful_submissions} submissions.")