#!/usr/bin/python
#
# Copyright 2019 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specif5ic language governing permissions and
# limitations under the License.

import os
import wget
import logging
import tensorflow as tf
import tensorflow_hub as hub
import numpy as np
import lwvlib

MAX_RANK_MEM=5000
MAX_RANK=10000

MODULE_URL = 'https://tfhub.dev/google/universal-sentence-encoder/2'

FINNISH_WORD2VEC_URL = 'http://dl.turkunlp.org/finnish-embeddings/finnish_s24_skgram.bin'
FINNISH_WORD2VEC_FILE = "finnish_s24_skgram.bin"

class EmbedUtil:

  def __init__(self):

    print("init embed util")
    logging.info('Initialising english embedding utility...')
    embed_module = hub.Module(MODULE_URL)
    placeholder = tf.placeholder(dtype=tf.string)
    embed = embed_module(placeholder)
    session = tf.Session()
    session.run([tf.global_variables_initializer(), tf.tables_initializer()])
    logging.info('tf.Hub module is loaded.')

    logging.info("loading finnish models...")

    dir_path = os.path.dirname(os.path.realpath(__file__))
    local_file_name = os.path.join(dir_path, FINNISH_WORD2VEC_FILE)

    self._download_finnish_models(local_file_name)

    self.finnish_model =lwvlib.WV.load(local_file_name, MAX_RANK_MEM, MAX_RANK)

    print('Embedding util initialised.')

    def _embeddings_fn(sentences):
      computed_embeddings = session.run(
        embed, feed_dict={placeholder: sentences})
      return computed_embeddings

    self.embedding_fn = _embeddings_fn
    logging.info('Embedding utility initialised.')


  def _download_finnish_models(self, local_file_name):
    print('Downloading finnish word2vec model file {}'.format(local_file_name))

    wget.download(FINNISH_WORD2VEC_URL, local_file_name)

    print('File size: {} GB'.format(round(os.path.getsize(local_file_name) / float(1024 ** 3), 2)))


  def find_similarity(self, text1, text2, language):
    if language == 'english':
        embedding_matrix = self.embedding_fn([text1, text2])
        # item_ids = self.match_util.find_similar_items(query_embedding, num_matches)
        # items = self.datastore_util.get_items(item_ids)
        return np.inner(embedding_matrix, embedding_matrix)[0][1]
    elif language == 'finnish':
        return self.finnish_model.similarity_sentences([text1, text2])[0][1]

  def find_similarity_bulk(self, sentences, language):
    if language == 'english':
        embedding_matrix = self.embedding_fn(sentences)
        # item_ids = self.match_util.find_similar_items(query_embedding, num_matches)
        # items = self.datastore_util.get_items(item_ids)
        return np.inner(embedding_matrix, embedding_matrix)
    elif language == 'finnish':
        return self.finnish_model.similarity_sentences(sentences)



# if __name__ == '__main__':
#   search_util = SearchUtil()
#   search_util.search("this is a cat", "this is a dog")



