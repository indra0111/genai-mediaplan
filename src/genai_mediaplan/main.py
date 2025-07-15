#!/usr/bin/env python
import sys
import warnings

from datetime import datetime

from genai_mediaplan.crew import GenaiMediaplan
from genai_mediaplan.utils.forecast_data import export_table_as_json
from genai_mediaplan.utils.helper import extract_json_from_markdown
from genai_mediaplan.utils.update_google_slides_content import get_copy_of_presentation

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# This main file is intended to be a way for you to run your
# crew locally, so refrain from adding unnecessary logic into this file.
# Replace with inputs you want to test with, it will automatically
# interpolate any tasks and agents information

def run():
    """
    Run the crew.
    """
    cohort_name = "Study Abroad"
    data = export_table_as_json(cohort_name)
    audience_data = data['abvr']
    forecast_data = data['results']
    print(f"data: {data}")
    inputs = {
        'cohort_name': cohort_name,
        'audience_data': audience_data
    }
    try:
        GenaiMediaplan().crew().kickoff(inputs=inputs)
        model_output_json = extract_json_from_markdown("final_report.md")
        print(f"model_output_json: {model_output_json}")
        get_copy_of_presentation(cohort_name, model_output_json, forecast_data)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")


def train():
    """
    Train the crew for a given number of iterations.
    """
    inputs = {
        "topic": "AI LLMs",
        'current_year': str(datetime.now().year)
    }
    try:
        GenaiMediaplan().crew().train(n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")

def replay():
    """
    Replay the crew execution from a specific task.
    """
    try:
        GenaiMediaplan().crew().replay(task_id=sys.argv[1])

    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")

def test():
    """
    Test the crew execution and returns the results.
    """
    inputs = {
        "topic": "AI LLMs",
        "current_year": str(datetime.now().year)
    }
    
    try:
        GenaiMediaplan().crew().test(n_iterations=int(sys.argv[1]), eval_llm=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while testing the crew: {e}")