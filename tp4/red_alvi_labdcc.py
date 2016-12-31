from __future__ import print_function
from keras.models import Sequential
from keras.layers import Dense, Activation, Dropout
from keras.layers import LSTM
from keras.optimizers import RMSprop
from keras.utils.data_utils import get_file
import numpy as np
import random
import sys
import h5py
from utils import *
import os


print('Cargando dataset...')
path = "dataseth5/noLessComm0.1-con-dict-full.h5"
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


# build the model: a single LSTM
print('Creando modelo...')
model = Sequential()
model.add(LSTM(64, consume_less='gpu', input_shape=(maxlen, len(chars)), return_sequences=True))
model.add(Dropout(0.2))
model.add(LSTM(128, consume_less='gpu', return_sequences=True))
model.add(Dropout(0.2))
model.add(LSTM(256, consume_less='gpu'))
model.add(Dense(len(chars)))
model.add(Activation('softmax'))

optimizer = RMSprop(lr=0.001) #baje el lr de 0.01 a 0.001
print('Compilando...')
model.compile(loss='categorical_crossentropy', optimizer=optimizer)


def sample(preds, temperature=1.0):
    # helper function to sample an index from a probability array
    preds = np.asarray(preds).astype('float64')
    preds = np.log(preds) / temperature
    exp_preds = np.exp(preds)
    preds = exp_preds / np.sum(exp_preds)
    probas = np.random.multinomial(1, preds, 1)
    return np.argmax(probas)

print('Entrenando...')
name=NameGen(os.path.basename(sys.argv[0]))
modelfile = name.get_model_file('best-model.h5')
# train the model, output generated text after each iteration
#~ best_loss = None
best_val_loss = None

for iteration in range(1, 60):
    print()
    print('-' * 50)
    print('Iteration', iteration)
    history = model.fit(X, y, batch_size=128, nb_epoch=1, validation_split=0.2) #added validation
    #~ if best_loss>history.history['loss'] or best_val_loss>history.history['val_loss']:
        #~ print('Guardando modelo en {}'.format(modelfile+'iter'+str(iteration)+'loss'+str(history.history['loss'])+'val_loss'+str(history.history['val_loss'])))
        #~ if best_loss>history.history['loss']:
            #~ best_loss = history.history['loss']
        #~ if best_val_loss>history.history['val_loss']:
            #~ best_val_loss = history.history['val_loss']
    if best_val_loss==None or history.history['val_loss']<best_val_loss:
        print('Guardando modelo en {}'.format(modelfile+'iter'+str(iteration)+'loss'+str(history.history['loss'])+'val_loss'+str(history.history['val_loss'])))
        best_val_loss = history.history['val_loss']
        model.save(modelfile+'iter'+str(iteration)+'loss'+str(history.history['loss'])+'val_loss'+str(history.history['val_loss'])+'.h5')

    start_index = random.randint(0, len(text) - maxlen - 1)

    for diversity in [0.2, 0.4, 0.5, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 1.0]:
        print()
        print('----- diversity:', diversity)

        generated = ''
        sentence = text[start_index: start_index + maxlen]
        generated += sentence
        print('----- Generating with seed: "' + sentence + '"')
        sys.stdout.write(generated)
        for i in range(400):
            x = np.zeros((1, maxlen, len(chars)))
            for t, char in enumerate(sentence):
                x[0, t, char_indices[char]] = 1.

            preds = model.predict(x, verbose=0)[0]
            next_index = sample(preds, diversity)
            next_char = indices_char[next_index]

            generated += next_char
            sentence = sentence[1:] + next_char

            sys.stdout.write(next_char)
            sys.stdout.flush()
        print()

