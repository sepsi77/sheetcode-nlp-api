import requests
import json

# BASE_URL = "https://semantic-similarity-dot-content-audit-tool.appspot.com/"
BASE_URL = "https://content-audit-tool.appspot.com/"
# BASE_URL = "http://127.0.0.1:5000/"

email = "aparna@gmail.com"
product_id = "TEST"

def test_similarity():
    print("sending data to /similarity endpoint for english...")
    data ={
            "email": email,
            "product_id": product_id,
            "lang": "english",
            "text1": "dog",
            "text2": "cat"
    }
    print(data)
    req = requests.get(url = BASE_URL + "similarity", params = data)
    # r = json.loads()
    print("response from /similarity endpoint for english...")
    print(req.text)

    print("sending data to /similarity endpoint for finnish...")
    data ={
            "email": email,
            "product_id": product_id,
            "lang": "finnish",
            "text1": "uros",
            "text2": "koira"
    }
    print(data)
    req = requests.get(url = BASE_URL + "similarity", params = data)
    # r = json.loads()
    print("response from /similarity endpoint for finnish...")
    print(req.text)


def test_similarity_bulk():
    print("sending data to /similarity_bulk endpoint for english...")
    data ={
            "email": email,
            "product_id": product_id,
            "lang": "english",
            "sentences": ["this is a dog", "this is a cat"]
    }
    print(data)
    req = requests.post(url = BASE_URL + "similarity_bulk", json = data)
    # r = json.loads()
    print("response from /similarity_bulk endpoint for english...")
    print(req.text)

    print("sending data to /similarity_bulk endpoint for finnish...")
    data ={
            "email": email,
            "product_id": product_id,
            "lang": "finnish",
            "sentences": ["uros", "koira"]
    }
    print(data)
    req = requests.post(url = BASE_URL + "similarity_bulk", json = data)
    # r = json.loads()
    print("response from /similarity_bulk endpoint for finnish...")
    print(req.text)


def test_lemma():
    print("sending data to /lemma endpoint...")
    data ={
            "email": email,
            "product_id": product_id,
            "sentences": [
                "dogs",
                "reading"
            ]
    }
    print(data)
    req = requests.post(url = BASE_URL + "lemma", json = data)
    # r = json.loads()
    print("response from /lemma endpoint...")
    print(req.text)


if __name__ == '__main__':
    test_similarity()
    test_similarity_bulk()
    test_lemma()
