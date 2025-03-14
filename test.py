import io
import time
import random

import torch
import librosa

import numpy as np
import eng_to_ipa as ei

from itertools import groupby
from datasets import load_dataset
from pydub import AudioSegment, silence
from pydub.playback import play
from pynput import keyboard
from speech_recognition import Recognizer, Microphone
from transformers import AutoProcessor, AutoModelForCTC, Wav2Vec2Processor


def calculate_score(correct_count, total_count):
    return np.round(correct_count / (total_count+0.001), 2)

def get_score(label, pred):
    def find_lcs(X, Y):
        m = len(X)
        n = len(Y)

        L = [[0 for i in range(n+1)] for j in range(m+1)]
    
        # Following steps build L[m+1][n+1] in bottom up fashion. Note
        # that L[i][j] contains length of LCS of X[0..i-1] and Y[0..j-1]
        for i in range(m+1):
            for j in range(n+1):
                if i == 0 or j == 0:
                    L[i][j] = 0
                elif X[i-1] == Y[j-1]:
                    L[i][j] = L[i-1][j-1] + 1
                else:
                    L[i][j] = max(L[i-1][j], L[i][j-1])
    
        # Create a string variable to store the lcs string
        # lcs = ""
        lcs_indexes = []
    
        # Start from the right-most-bottom-most corner and
        # one by one store characters in lcs[]
        i = m
        j = n
        while i > 0 and j > 0:
    
            # If current character in X[] and Y are same, then
            # current character is part of LCS
            if X[i-1] == Y[j-1]:
                # lcs += X[i-1]
                lcs_indexes.append(i-1)
                i -= 1
                j -= 1
    
            # If not same, then find the larger of two and
            # go in the direction of larger value
            elif L[i-1][j] > L[i][j-1]:
                i -= 1
                
            else:
                j -= 1
    
        # We traversed the table in reverse order
        # LCS is the reverse of what we got
        # lcs = lcs[::-1]
        # lcs_indexes = lcs_indexes[::-1]
        
        return lcs_indexes
    
    lcs_indexes = find_lcs(label, pred)
    score = calculate_score(len(lcs_indexes), len(label))
    error_indexes = np.ones(len(label), dtype=bool)
    for index in lcs_indexes:
        error_indexes[index] = False

    return score, error_indexes

def eng2ipa(text):
    ipa_text = ei.convert(text)
    replacement_dict = {'*': '',
                       "ˈ": '',
                       'ˌ': '',
                       }
    for char in replacement_dict.keys():
        ipa_text = ipa_text.replace(char, replacement_dict[char])
    return ipa_text

def convert_output(text):
    converted_text = text
    replacement_dict = {'d͡ʒ': 'ʤ',
                        't͡ʃ': 'ʧ',
                        'ɚ': 'ər',
                        'ɹ': 'r',
                        'ʌ': 'ə',
                        'ɡ': 'g',
                       }
    for char in replacement_dict.keys():
        converted_text = converted_text.replace(char, replacement_dict[char])
    return converted_text

def decode_phonemes(
    ids: torch.Tensor, processor: Wav2Vec2Processor, ignore_stress: bool = False
) -> str:
    """CTC-like decoding. First removes consecutive duplicates, then removes special tokens."""
    # removes consecutive duplicates
    ids = [id_ for id_, _ in groupby(ids)]

    special_token_ids = processor.tokenizer.all_special_ids + [
        processor.tokenizer.word_delimiter_token_id
    ]
    # converts id to token, skipping special tokens
    phonemes = [processor.decode(id_) for id_ in ids if id_ not in special_token_ids]

    # joins phonemes
    prediction = " ".join(phonemes)

    # whether to ignore IPA stress marks
    if ignore_stress == True:
        prediction = prediction.replace("ˈ", "").replace("ˌ", "")

    return prediction

def infer(waveform, feature_extractor, model, tokenizer) -> list:
  # forward sample through model to get greedily predicted transcription ids
    input_values = feature_extractor(waveform, sampling_rate=16_000, return_tensors="pt", padding="longest").input_values
    logits = model(input_values).logits[0]
    pred_ids = torch.argmax(logits, axis=-1)

    # retrieve word stamps (analogous commands for `output_char_offsets`)
    outputs = tokenizer.decode(pred_ids, output_char_offsets=True)
    # compute `time_offset` in seconds as product of downsampling ratio and sampling_rate
    time_offset = model.config.inputs_to_logits_ratio / feature_extractor.sampling_rate

    special_token_ids = tokenizer.all_special_ids + [tokenizer.word_delimiter_token_id]

    ipa_char_offsets = [
        {
            "ipa_char": d["char"],
            "start_time": round(d["start_offset"] * time_offset, 2),
            "end_time": round(d["end_offset"] * time_offset, 2),
        }
        for d in outputs.char_offsets if d["char"] != ' '
    ]

    ipa_recording_transcript = outputs.text.lower()

    return ipa_recording_transcript, ipa_char_offsets

def on_press(key):
    global recording
    if recording == False and key == keyboard.Key.shift:
        recording = True

# Input
text_list = ["good evening everyone",
        "without the dataset",
        "and you know it",
        "the sheep had taught him that",
        "i have the money"]

# import model, feature extractor, tokenizer
checkpoint = "bookbot/wav2vec2-ljspeech-gruut"
model = AutoModelForCTC.from_pretrained(checkpoint)
processor = AutoProcessor.from_pretrained(checkpoint)
sr = processor.feature_extractor.sampling_rate

recognizer = Recognizer()
recognizer.energy_threshold = 400

recording = False

listener = keyboard.Listener(on_press=on_press)
listener.start()

start_time = time.time()
with Microphone(sample_rate=sr) as source:
  while True:
    if not recording:
      print('Press Shift to start record', end='\r')
      time.sleep(1)
      continue

    recording = False
    text = text_list[random.randint(0, len(text_list) - 1)]
    print(f"\n\nSPEAK ALOUND: {text}")
    audio = recognizer.listen(source, phrase_time_limit=5) # Bytes
    
    data = io.BytesIO(audio.get_wav_data()) # Object(Bytes) Ex: 96300
    audio_segment = AudioSegment.from_file(data) # Object(Object) Ex: 96300
    waveform = torch.FloatTensor(audio_segment.get_array_of_samples()) # Tensor(Array(Int)) Ex: 48128 =>  1 Int = 2 Bytes

    start_time = time.time()
    # result = infer(waveform, phoneme_feature_extractor, phoneme_model, phoneme_tokenizer)
    inputs = processor(waveform, sampling_rate=sr, return_tensors="pt", padding=True)
    with torch.no_grad():
        logits = model(inputs["input_values"]).logits
    predicted_ids = torch.argmax(logits, dim=-1)
    prediction = decode_phonemes(predicted_ids[0], processor, ignore_stress=True)
    word_time = time.time() - start_time

    # text, char_offsets = result
    # play(audio_segment)
    # print(prediction)
    # print(char_offsets)

    label_string = eng2ipa(text)
    pred_string = convert_output(prediction)
    print(f'/{label_string}/')

    label = label_string.replace(' ', '') # remove space
    pred = pred_string.replace(' ', '') # remove space
    print(f'Pred: {pred}, Label: {label}')
    score, error_indexes = get_score(label, pred)
    print(f'Your score:', score)

    char_index = 0
    correct_char_count = 0
    char_in_word_count = 0
    word_scores = []
    error_char_indexes = []

    print('\nCHAR')
    for char in label_string:
        if char == ' ':
            word_scores.append(calculate_score(correct_char_count, char_in_word_count))
            correct_char_count = 0
            char_in_word_count = 0
            print(char, end=' ')
            continue

        if error_indexes[char_index]:
            error_char_indexes.append(False)
            print(f"\x1b[31m{char}\x1b[0m", end='')
        else:
            error_char_indexes.append(True)
            print(f"\x1b[32m{char}\x1b[0m", end='')
            correct_char_count += 1
        char_index += 1
        char_in_word_count += 1

    word_scores.append(calculate_score(correct_char_count, char_in_word_count))

    print('\nWORD')
    for i, word in enumerate(text.split(' ')):
        if word_scores[i] >= 0.8:
            print(f"\x1b[32m{word}\x1b[0m", end=' ')
        elif word_scores[i] >= 0.5:
            print(f"\x1b[93m{word}\x1b[0m", end=' ')
        else:
            print(f"\x1b[31m{word}\x1b[0m", end=' ')

    res = {'score': score,
           'error_char_indexes': error_char_indexes,
           'word_scores': word_scores}
    print(f'\n{res}')
    