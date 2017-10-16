#!/usr/bin/python3
# -*- coding: iso-8859-15 -*-

'''Trains a simple convnet on the MNIST dataset.
Gets to 99.25% test accuracy after 12 epochs
(there is still a lot of margin for parameter tuning).
16 seconds per epoch on a GRID K520 GPU.
'''

from __future__ import print_function
import sys
import os
from os.path import dirname, realpath, join as path_join
# parent directory of the folder in which this script is located
PARENT_DIRECTORY = path_join(dirname(realpath(__file__)), "..")
sys.path.insert(0, PARENT_DIRECTORY)

import time
import json

import keras
from keras.datasets import mnist
from keras.models import Sequential
from keras.layers import Dense, Dropout, Flatten
from keras.layers import Conv2D, MaxPooling2D

from os.path import abspath, join as path_join

from autoda.data_augmentation import ImageAugmentation


config_id = int(sys.argv[1])
batch_size = 128
num_classes = 10
epochs = 12

# input image dimensions
img_rows, img_cols = 28, 28
data_augmentation = True

path = path_join(abspath("."), "Workspace/MastersThesis/AutoDA/experiments/results/mnist")

# The data, shuffled and split between train and test sets:
(x_train, y_train), (x_test, y_test) = mnist.load_data()

x_train = x_train.reshape(x_train.shape[0], 1, img_rows, img_cols)
x_test = x_test.reshape(x_test.shape[0], 1, img_rows, img_cols)
input_shape = (1, img_rows, img_cols)

x_train = x_train.astype('float32')
x_test = x_test.astype('float32')
x_train /= 255
x_test /= 255

print('x_train shape:', x_train.shape)
print(x_train.shape[0], 'train samples')
print(x_test.shape[0], 'test samples')

# Convert class vectors to binary class matrices.
y_train = keras.utils.to_categorical(y_train, num_classes)
y_test = keras.utils.to_categorical(y_test, num_classes)


# LeNet
model = Sequential()
model.add(Conv2D(32, kernel_size=(3, 3),
                 activation='relu',
                 input_shape=input_shape))
model.add(Conv2D(64, (3, 3), activation='relu'))
model.add(MaxPooling2D(pool_size=(2, 2)))
model.add(Dropout(0.25))
model.add(Flatten())
model.add(Dense(128, activation='relu'))
model.add(Dropout(0.5))
model.add(Dense(num_classes, activation='softmax'))

# Let's train the model using ADAM

start_compile_time = time.time()

model.compile(loss=keras.losses.categorical_crossentropy,
              optimizer=keras.optimizers.Adam(),
              metrics=['accuracy'])
compile_time = time.time() - start_compile_time

if not data_augmentation:
    print('Not using data augmentation.')
    start_time = time.time()
    history = model.fit(x_train, y_train,
                        batch_size=batch_size,
                        epochs=epochs,
                        validation_data=(x_test, y_test),
                        shuffle=True)

    runtime = time.time() - start_time
else:
    print('Using real-time data augmentation.')
    # This will do preprocessing and realtime data augmentation:

    config = ImageAugmentation.get_config_space().sample_configuration() #seed=123

    imagegen = ImageAugmentation(config)

    start_time = time.time()
    # Fit the model on the batches generated by datagen.flow().
    history = model.fit_generator(imagegen.apply_transform(x_train, y_train,
                                                           batch_size=batch_size),
                                  steps_per_epoch=x_train.shape[0] // batch_size,
                                  epochs=epochs,
                                  validation_data=(x_test, y_test))

    runtime = time.time() - start_time

# Evaluate model with test data set and share sample prediction results
score = model.evaluate(x_test, y_test, verbose=0)


result = dict()
result["configs"] = config.get_dictionary()
result["train_accuracy"] = history.history['acc'][-1]
result["validation_accuracy"] = score[1]
result["runtime"] = runtime
result["compile_time"] = compile_time
result["config_id"] = config_id

print("result:", result)

fh = open(os.path.join(path, "config_%d.json" % config_id), "w")
json.dump(result, fh)