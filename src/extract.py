"""Validate a face recognizer on the "Labeled Faces in the Wild" dataset (http://vis-www.cs.umass.edu/lfw/).
Embeddings are calculated using the pairs from http://vis-www.cs.umass.edu/lfw/pairs.txt and the ROC curve
is calculated and plotted. Both the model metagraph and the model parameters need to exist
in the same directory, and the metagraph should have the extension '.meta'.
"""
# MIT License
#
# Copyright (c) 2016 David Sandberg
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import tensorflow as tf
import numpy as np
import argparse
import facenet
import lfw
import os
import sys
import math
import h5py
from sklearn import metrics
from scipy.optimize import brentq
from scipy import interpolate
from os import listdir
from os.path import isfile, join

def get_paths(face_dir):
    return [os.path.abspath(join(face_dir, f)) for f in listdir(face_dir) if isfile(join(face_dir, f))]

def main(args):

    with tf.Graph().as_default():

        with tf.Session() as sess:

            # Get the paths for the corresponding images
            paths = get_paths(os.path.expanduser(args.face_dir))

            # Load the model
            facenet.load_model(args.model)

            # Get input and output tensors
            images_placeholder = tf.get_default_graph().get_tensor_by_name("input:0")
            embeddings = tf.get_default_graph().get_tensor_by_name("embeddings:0")
            phase_train_placeholder = tf.get_default_graph().get_tensor_by_name("phase_train:0")

            #image_size = images_placeholder.get_shape()[1]  # For some reason this doesn't work for frozen graphs
            image_size = args.image_size
            embedding_size = embeddings.get_shape()[1]

            # Run forward pass to calculate embeddings
            print('Runnning forward pass on LFW images')
            batch_size = args.lfw_batch_size
            nrof_images = len(paths)
            nrof_batches = int(math.ceil(1.0*nrof_images / batch_size))
            emb_array = np.zeros((nrof_images, embedding_size))
            for i in range(nrof_batches):
                start_index = i*batch_size
                end_index = min((i+1)*batch_size, nrof_images)
                paths_batch = paths[start_index:end_index]
                images = facenet.load_data(paths_batch, False, False, image_size)
                feed_dict = { images_placeholder:images, phase_train_placeholder:False }
                emb_array[start_index:end_index, :] = sess.run(embeddings, feed_dict=feed_dict)

            h5f = h5py.File('data.h5', 'w')
            h5f["feature"] = emb_array


def parse_arguments(argv):
    parser = argparse.ArgumentParser()

    parser.add_argument('face_dir', type=str,
        help='Path to the data directory containing aligned face patches.')
    parser.add_argument('model', type=str,
        help='Could be either a directory containing the meta_file and ckpt_file or a model protobuf (.pb) file')
    parser.add_argument('--lfw_batch_size', type=int,
        help='Number of images to process in a batch in the LFW test set.', default=100)
    parser.add_argument('--image_size', type=int,
        help='Image size (height, width) in pixels.', default=160)
    return parser.parse_args(argv)

if __name__ == '__main__':
    main(parse_arguments(sys.argv[1:]))
