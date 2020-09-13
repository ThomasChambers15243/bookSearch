import urllib.request
import json
import textwrap
import time


def bookSearchISBN(bookISBN):
    #   Many thanks to:
    #   https://gist.github.com/AO8/faa3f52d3d5eac63820cfa7ec2b24aa7

    #   API specific
    #   https://developers.google.com/books/docs/v1/using#api_params


    base_api_link = "https://www.googleapis.com/books/v1/volumes?q=isbn:"

    with urllib.request.urlopen(base_api_link + bookISBN) as f:
        text = f.read()

    decoded_text = text.decode("utf-8")

    decoded_text = text.decode("utf-8")
    obj = json.loads(decoded_text) # deserializes decoded_text to a Python object
    if obj["totalItems"] == 0:
        return False
    obj_item = obj["items"][0]



    bookValues = {
        "title" : obj_item["volumeInfo"]["title"],
        "fullDescription" : obj_item["volumeInfo"]["description"],
        "pageCount" : obj_item["volumeInfo"]["pageCount"],
        "author(s)" : obj_item["volumeInfo"]["authors"],
        "isInPublicDomain" :  obj_item["accessInfo"]["publicDomain"],
        "publisher" : obj_item["volumeInfo"]["publisher"],
        "publishedDate" : obj_item["volumeInfo"]["publishedDate"],
        "language" : obj_item["volumeInfo"]["language"],
        "isEBook" : obj_item["saleInfo"]["isEbook"],
        "img" : obj_item["volumeInfo"]["imageLinks"]["thumbnail"]
        }
    return bookValues

def timeToReadBook(wpm, pageCount):
    #conservative 400 words per page from https://howardcc.libanswers.com/faq/69833
    pagePerMin = 400 * wpm
    totalTimeInSeconds = pagePerMin * pageCount * 60
    return time.strftime("%H:%M:%S", time.gmtime(totalTimeInSeconds))

