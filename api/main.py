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
# See the License for the specific language governing permissions and
# limitations under the License.

from flask import Flask, request, jsonify
from nltk.corpus import stopwords
import requests
import json

# You will have to download the set of stop words the first time
import nltk
from nltk.stem import WordNetLemmatizer

import embedding as emb

emb_util = emb.EmbedUtil()

# download nltk files
nltk.download('wordnet')
nltk.download('stopwords')


app = Flask(__name__)

LICENCE_URL = 'https://sheetcode.dev/wp-json/wc-custom/v1/check/'
KEY = "ACYBGNTu5wStf7HpGihrfLxOuErro5AlOg"

@app.route('/')
def display_default():
  return """Welcome to the semantic similarity app!
         use GET /similarity?text1=<text1>&text2=<text2> to calculate similarity between the two texts.

         use POST /similarity_bulk with a list of urls to get pair-wise similarity.
         input json should have the following structure:
         {
              "sentences": ["dog","cat"]
          }

         use POST /lemma with a list of words to get the corresponding lemma."""


@app.route('/readiness_check')
def check_readiness():
  return 'App is ready!'


@app.route('/similarity', methods=['GET'])
def similarity():
  # stop_words = stopwords.words('english')
  try:
    language = request.args.get('lang')
    text1 = remove_stop_words(request.args.get('text1'), language)
    text2 = remove_stop_words(request.args.get('text2'), language)
    product_id = request.args.get("product_id")
    email = request.args.get("email")

    succ, msg = check_licence_valid(product_id, email)

    if succ:
      results = emb_util.find_similarity(text1, text2, language)
      # convert numpy float32 to python float
      results = float(results)
      print(results)
    else:
      results = msg

  except Exception as error:
    results = 'Unexpected error: {}'.format(error)

  response = jsonify(results)
  return response


@app.route('/similarity_bulk', methods=['POST'])
def similarity_bulk():
  # stop_words = stopwords.words('english')
  try:
    request_data = request.get_json()
    sentences = request_data['sentences']
    language = request_data['lang']
    product_id = request_data["product_id"]
    email = request_data["email"]

    succ, msg = check_licence_valid(product_id, email)

    if succ:
      sentences_without_stopwords = [remove_stop_words(sentence, language) for sentence in sentences]
      results = emb_util.find_similarity_bulk(sentences_without_stopwords, language).tolist()
    else:
      results = msg

  except Exception as error:
    results = 'Unexpected error: {}'.format(error)

  response = jsonify(results)
  return response



@app.route('/lemma', methods=['POST'])
def lemma():
  lemmatizer = WordNetLemmatizer()
  try:
    request_data = request.get_json()
    words = request_data['words']
    product_id = request_data["product_id"]
    email = request_data["email"]

    succ, msg = check_licence_valid(product_id, email)

    if succ:
      results = [lemmatizer.lemmatize(word.split(" ")[0].strip(), "v") for word in words]
    else:
      results = msg

  except Exception as error:
    results = 'Unexpected error: {}'.format(error)

  response = jsonify(results)
  return response


def check_licence_valid(product_id, email):
  # data = {'product_id':'TEST', 'email':'aparna@gmail.com', 'key': KEY}
  data = {'product_id': product_id, 'email':email, 'key': KEY}
  r = json.loads(requests.post(url = LICENCE_URL, data = data).json())
  return r["success"], r["msg"]


def remove_stop_words(text, language):
  # should be full language name, eg. english
  stop_words = stopwords.words(language)
  print(text)
  return " ".join([word for word in text.split(" ") if word not in stop_words])

if __name__ == '__main__':
  app.run(host='127.0.0.1', port=8000, debug=True)
