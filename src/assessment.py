import os
import time
import torch
import json
import string
import base64
import random
import audioread
import numpy as np
import eng_to_ipa as ei
import src.utils.WordMatching as wm

from torchaudio.transforms import Resample
from src.model import EnglishModel


model = EnglishModel()

transform = Resample(orig_freq=48000, new_freq=16000)

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
                        'ʌ': 'ə'
                       }
    for char in replacement_dict.keys():
        converted_text = converted_text.replace(char, replacement_dict[char])
    return converted_text

def lambda_handler(event, context):
    data = json.loads(event['body'])

    # Get values
    sentence = data['title']
    audio_bytes = base64.b64decode(
        data['base64Audio'][22:].encode('utf-8')) # 22 is default

    # Check real_text exists
    if len(sentence) == 0:
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Credentials': "true",
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
            },
            'body': ''
        }

    audio_chunk_dir = './src/audio_chunks/'
    if not os.path.exists(audio_chunk_dir):
        os.makedirs(audio_chunk_dir)
    # Write audio to a temp file
    start = time.time()
    letters = string.ascii_lowercase
    random_string = ''.join(random.choice(letters) for i in range(20))
    audio_chunk_path = audio_chunk_dir + random_string + '.ogg'
    f = open(audio_chunk_path, 'wb')
    f.write(audio_bytes)
    f.close()
    print('Time for saving binary in file: ', str(time.time()-start))

    # Read the audio file and transform it
    start = time.time()
    signal, fs = audioread_load(audio_chunk_path)

    signal = transform(torch.Tensor(signal))

    print('Time for loading .ogg file file: ', str(time.time()-start))

    # Run model
    pred_string = model.recognize(signal)

    # Remove the audio file
    start = time.time()
    os.remove(audio_chunk_path)
    print('Time for deleting file: ', str(time.time()-start))

    start = time.time()
    label_string = eng2ipa(sentence)
    pred_string = convert_output(pred_string)
    print(sentence, label_string)

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

    for char in label_string:
        if char == ' ':
            word_scores.append(calculate_score(correct_char_count, char_in_word_count))
            correct_char_count = 0
            char_in_word_count = 0
            continue

        if error_indexes[char_index]:
            error_char_indexes.append(False)
        else:
            error_char_indexes.append(True)
            correct_char_count += 1
        char_index += 1
        char_in_word_count += 1
    
    word_scores.append(calculate_score(correct_char_count, char_in_word_count))

    print('Time to post-process results: ', str(time.time()-start))

    res = {'score': score,
           'error_char_indexes': error_char_indexes,
           'word_scores': word_scores,
           'label_string': label_string,
           'pred_string': pred}
    
    print(res)

    return json.dumps(res)

# From Librosa


def audioread_load(path, offset=0.0, duration=None, dtype=np.float32):
    """Load an audio buffer using audioread.

    This loads one block at a time, and then concatenates the results.
    """

    y = []
    with audioread.audio_open(path) as input_file:
        sr_native = input_file.samplerate
        n_channels = input_file.channels

        s_start = int(np.round(sr_native * offset)) * n_channels

        if duration is None:
            s_end = np.inf
        else:
            s_end = s_start + \
                (int(np.round(sr_native * duration)) * n_channels)

        n = 0

        for frame in input_file:
            frame = buf_to_float(frame, dtype=dtype)
            n_prev = n
            n = n + len(frame)

            if n < s_start:
                # offset is after the current frame
                # keep reading
                continue

            if s_end < n_prev:
                # we're off the end.  stop reading
                break

            if s_end < n:
                # the end is in this frame.  crop.
                frame = frame[: s_end - n_prev]

            if n_prev <= s_start <= n:
                # beginning is in this frame
                frame = frame[(s_start - n_prev):]

            # tack on the current frame
            y.append(frame)

    if y:
        y = np.concatenate(y)
        if n_channels > 1:
            y = y.reshape((-1, n_channels)).T
    else:
        y = np.empty(0, dtype=dtype)

    return y, sr_native

# From Librosa


def buf_to_float(x, n_bytes=2, dtype=np.float32):
    """Convert an integer buffer to floating point values.
    This is primarily useful when loading integer-valued wav data
    into numpy arrays.

    Parameters
    ----------
    x : np.ndarray [dtype=int]
        The integer-valued data buffer

    n_bytes : int [1, 2, 4]
        The number of bytes per sample in ``x``

    dtype : numeric type
        The target output type (default: 32-bit float)

    Returns
    -------
    x_float : np.ndarray [dtype=float]
        The input data buffer cast to floating point
    """

    # Invert the scale of the data
    scale = 1.0 / float(1 << ((8 * n_bytes) - 1))

    # Construct the format string
    fmt = "<i{:d}".format(n_bytes)

    # Rescale and format the data buffer
    return scale * np.frombuffer(x, fmt).astype(dtype)
