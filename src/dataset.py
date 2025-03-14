import json
import random

import pandas as pd

from src.utils.eng2ipa import eng2ipa

dataset_filename = 'cv-text-demo.txt'
dataset_information = pd.read_csv(f'data/{dataset_filename}', header=None)[0].to_list()

def get_data():
    text_list = []
    ipa_text_list = []

    for text in dataset_information:
        text_list.append(text)
        ipa_text_list.append(eng2ipa(text))

    result = {
        'status': 200,
        'text_list': text_list,
        'ipa_text_list': ipa_text_list}

    return result
