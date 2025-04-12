from abc import ABC, abstractmethod

class AbstractSurveyAutoFiller(ABC):

    @abstractmethod
    def auto_fill_survey(self, survey_url: str, csv_file: str, num_fill: int) -> None:
        pass
