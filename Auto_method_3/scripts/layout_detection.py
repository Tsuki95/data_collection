import os
import sys
import os.path as osp
import argparse

sys.path.append(osp.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from pdf_extract_kit.utils.config_loader import load_config, initialize_tasks_and_models
import pdf_extract_kit.tasks

TASK_NAME = 'layout_detection'


def parse_args():
    parser = argparse.ArgumentParser(description="Run a task with a given configuration file.")
    parser.add_argument('--config', type=str, required=True, help='Path to the configuration file.')
    parser.add_argument('--word_file', type=str, required=False, help='Path to the Word document for saving results.')
    return parser.parse_args()


def main(config_path, word_file=None):
    config = load_config(config_path)

    # If word_file is provided, pass it to the config
    if word_file:
        config['word_file'] = word_file

    # Initialize tasks and models
    task_instances = initialize_tasks_and_models(config)

    # Get input and output paths from config
    input_data = config.get('inputs', None)
    result_path = config.get('outputs', 'outputs' + '/' + TASK_NAME)

    # Get the layout detection task instance
    model_layout_detection = task_instances[TASK_NAME]

    # For PDF detection
    detection_results = model_layout_detection.predict_pdfs(input_data, result_path)

    # Print the path to the predicted results
    print(f'The predicted results can be found at {result_path}')

    # If a word file is specified, print a message
    if word_file:
        print(f'Results will also be saved in the Word file: {word_file}')


if __name__ == "__main__":
    args = parse_args()
    main(args.config, args.word_file)
