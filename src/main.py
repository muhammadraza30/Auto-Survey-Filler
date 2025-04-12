from survey_auto_filler import SurveyAutoFiller

if __name__ == "__main__":
    survey_url = input("Enter survey URL: ").strip()
    csv_file = "./data/data.csv"
    try:
        num_fill = int(input("How many times to fill survey? ").strip())
        if num_fill <= 0:
            raise ValueError()
    except ValueError:
        print("Invalid input, using 1")
        num_fill = 1

    filler = SurveyAutoFiller()
    filler.auto_fill_survey(survey_url, csv_file, num_fill)
    
