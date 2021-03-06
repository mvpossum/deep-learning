from __future__ import print_function
from keras.models import load_model
import numpy as np
import random
import sys
from sys import argv
import h5py
from utils import *
import os

USAGE = "Usage python eval_model.py <db.h5> <model.h5>"
if len(argv)==3:
    dbfile = argv[1]
    modelfile = argv[2]
else:
    print(USAGE)
    exit(1)

print('Cargando modelo...')
model = load_model(modelfile)

print('Cargando dataset...')
path = dbfile #"dataseth5/con-dict.h5"
with h5py.File(path,'r') as hf:
    text = str(hf.get('dataset')[0]).decode("unicode_escape")
print('corpus length:', len(text))


chars = sorted(list(set(text)))
print('total chars:', len(chars))
char_indices = dict((c, i) for i, c in enumerate(chars))
indices_char = dict((i, c) for i, c in enumerate(chars))

print('Creando oraciones...')
# cut the text in semi-redundant sequences of maxlen characters
maxlen = 40
step = 3
sentences = []
next_chars = []
for i in range(0, len(text) - maxlen, step):
    sentences.append(text[i: i + maxlen])
    next_chars.append(text[i + maxlen])
print('nb sequences:', len(sentences))

print('Vectorizando...')
X = np.zeros((len(sentences), maxlen, len(chars)), dtype=np.bool)
y = np.zeros((len(sentences), len(chars)), dtype=np.bool)
for i, sentence in enumerate(sentences):
    for t, char in enumerate(sentence):
        X[i, t, char_indices[char]] = 1
    y[i, char_indices[next_chars[i]]] = 1

def sample(preds, temperature=1.0):
    # helper function to sample an index from a probability array
    preds = np.asarray(preds).astype('float64')
    preds = np.log(preds) / temperature
    exp_preds = np.exp(preds)
    preds = exp_preds / np.sum(exp_preds)
    probas = np.random.multinomial(1, preds, 1)
    return np.argmax(probas)

# train the model, output generated text after each iteration


dicc={''}
for dicfile in ['diccionario-ingles.txt']:
    with codecs.open(dicfile, encoding='utf-8') as myfile:
        for l in myfile.readlines():
            dicc.add(strip_accents(l.strip()).lower().encode('utf-8'))
            
start_index = random.randint(0, len(text) - maxlen - 1)
for diversity in [0.4, 0.5, 0.55, 0.6, 0.7]:
    print('----- diversity:', diversity)

    generated = ''
    sentence = text[start_index: start_index + maxlen]
    #sentence= "tengo mucha hambre, que venga la pizza porfavor"[:maxlen]
    generated += sentence
    print('----- Generating with seed: "' + sentence + '"')
    sys.stdout.write(generated)
    next_char=' '
    i=0
    tries=0
    while i<400:
        x = np.zeros((1, maxlen, len(chars)))
        for t, char in enumerate(sentence):
            x[0, t, char_indices[char]] = 1.

        preds = model.predict(x, verbose=0)[0]
        next_index = sample(preds, diversity if next_char!=' ' else diversity+0.3)
        next_char = indices_char[next_index]
        if next_char==' ':
            w=generated[generated.rfind(' ')+1:].strip()
            if not w in dicc and len(generated)-len(w)>=maxlen and tries<100:
                generated=generated[:-len(w)]
                sentence=generated[-maxlen:]
                i-=len(w)
                for j in range(len(w)):
                    sys.stdout.write('\b')
                    sys.stdout.flush()
                tries+=1
                continue
            else:
                tries=0

        generated += next_char
        sentence = sentence[1:] + next_char

        sys.stdout.write(next_char)
        sys.stdout.flush()
        i+=1
    print()
    
