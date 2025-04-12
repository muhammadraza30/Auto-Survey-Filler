from abc import ABC, abstractmethod

class AbstractSurveyHandler(ABC):

    @abstractmethod
    def extract_entities(self, text):
        """
        Use spaCy to extract Named Entities (e.g., Name, Email).
        """
        pass

    @abstractmethod
    def match_field_with_ner(self, question_text):
        """
        Use NER to extract entities and match fields to the CSV columns.
        """
        pass

    @abstractmethod
    def match_field_with_transformer(self, question_text):
        """
        Use transformers for semantic field matching.
        """
        pass

    @abstractmethod
    def get_form_context(self):
        """
        Extract form title and description for context.
        """
        pass

    @abstractmethod
    def get_ai_answer(self, question_text):
        """
        Use OpenAI GPT to answer questions that don't match any CSV fields.
        """
        pass
    
    @abstractmethod
    def handle_question(self, question_element):
        """
        Handle individual questions in the survey.
        """
        pass

    @abstractmethod
    def handle_multi_page_form(self):
        """
        Handle multi-page forms in the survey.
        """
        pass
