# sheetcode-nlp-api

## Requirements

You need to have your [GCP Project](https://cloud.google.com/resource-manager/docs/creating-managing-projects).
You can use [Cloud Shell](https://cloud.google.com/shell/docs/quickstart)
or [gcloud CLI](https://cloud.google.com/sdk/) to run all the commands in this
guideline.

## Setup a project

Follow the [instruction](https://cloud.google.com/resource-manager/docs/creating-managing-projects) and create a GCP project.

The use of CloudShell is recommended from the GCP console to run the below commands.
CloudShell starts with an environment already logged in to your account and set
to the currently selected project. The following commands are required only in a
workstation shell environment, they are not needed in the CloudShell.

```bash
gcloud auth login
gcloud auth application-default login
gcloud config set project [your-project-id]
gcloud config set compute/zone us-central1-a
```

## Setup python environment and sample code

Follow commands below to install required python packages.

```bash
git clone [this-repo]
cd [this-repo]

# Make sure you have python 3 environement
pip3 install -r requirements.txt

# install dependencies for the app for local testing
cd api/
# Make sure you have python 3 environement
pip3 install -r requirements.txt
```

## Deploy the API

Set your GCP project ID in the **api/deploy.sh** script file:

```bash
PROJECT=[your-project-ID]
```

Then, you can deploy the app to AppEngine by executing the **deploy.sh**
script file:

```bash
cd api
bash deploy.sh
```


## API description
The **api_test.py** files contains samples for the http requests for all the api endpoints.

The similarity api endpoints either take a sentence pair or a list of sentences as input. The sentences are converted into vectors using pre-trained word embeddings and the similarity is measured as the cosine distance between the two sentence vectors.

### Word similarity: /similarity
- method type: GET
- Url parameters: product_id, email, lang, text1, text2
- lang can either be "english" or "finnish"
- text1 and text2 can be words or url encoded sentences like "this%20is%20a%20dog"

The output value is a single number representing the similarity, eg. 0.85


### Sentence similarity: /similarity_bulk
- method type: POST
- Url parameters: product_id, email, lang, sentences
- lang can either be "english" or "finnish"

The structure of the json payload is:
```
{
    "product_id": "...",
    "email": "...",
    "lang": "english",
    "sentences": [
        "sentence 1...",
        "sentence 2..."
    ]
}
```

The returned value is a correlation matrix specifying the similarities between pairs of sentences. An example for two input sentences is:

```
{[
[1, 0.9],
[0.9, 1]
]}
```

If an error occurs, the error message is returned instead.

### Lemma: /lemma
- method type: POST
- Json parameters: product_id, email, words
- Only for english.

The structure of the json payload is:
```
{
    "product_id": "...",
    "email": "...",
    "sentences": [
        "sentence 1...",
        "sentence 2..."
    ]
}
```

The returned value is a list of lemmas for each of the sentences:

```
{[
["lemma1", "lemma2"],
["lemma3", "lemma4"],
...
]}
```
