import pickle

# LOAD MODEL
model = pickle.load(open("models/svm_model.pkl", "rb"))
vectorizer = pickle.load(open("models/vectorizer.pkl", "rb"))

def test(text):
    vec = vectorizer.transform([text])
    pred = model.predict(vec)[0]

    if pred == 1:
        print("REAL →", text)
    else:
        print("FAKE →", text)

# TEST CASES
test("Government announces new economic policy")
test("Aliens secretly controlling the world")