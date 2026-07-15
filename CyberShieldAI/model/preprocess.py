import re
import string

import nltk
from nltk.corpus import stopwords


_STOPWORDS = None


def get_stopwords():
    global _STOPWORDS
    if _STOPWORDS is None:
        try:
            _STOPWORDS = set(stopwords.words("english"))
        except LookupError:
            nltk.download("stopwords", quiet=True)
            _STOPWORDS = set(stopwords.words("english"))
    return _STOPWORDS


def remove_emoji(text):
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"
        "\U0001F300-\U0001F5FF"
        "\U0001F680-\U0001F6FF"
        "\U0001F1E0-\U0001F1FF"
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "]+",
        flags=re.UNICODE,
    )
    return emoji_pattern.sub(" ", text)


def clean_text(text):
    text = str(text).lower()
    text = re.sub(r"https?://\S+|www\.\S+", " ", text)
    text = remove_emoji(text)
    text = text.translate(str.maketrans("", "", string.punctuation))
    text = re.sub(r"\d+", " ", text)
    words = [word for word in text.split() if word not in get_stopwords()]
    return re.sub(r"\s+", " ", " ".join(words)).strip()
