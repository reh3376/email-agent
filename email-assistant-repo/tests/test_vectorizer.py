from email_assistant.ml.vectorizer import HashingVectorizer
def test_vectorizer_basic():
    hv = HashingVectorizer(n_features=64).fit(["Hello world", "hello email world"])
    X = hv.transform(["world"])
    assert len(X[0]) == 64
