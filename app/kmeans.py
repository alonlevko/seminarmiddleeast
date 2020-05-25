from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import os
from sklearn.metrics import adjusted_rand_score
import pandas as pd
STOPWORDSFILENAME = "app/arabic_stop_words.txt"


def load_stop_word():
    print("load_stop_word: " + os.getcwd())
    file = open(STOPWORDSFILENAME, encoding='utf-8')
    words_list = []
    for line in file:
        words_list.append(line)
    file.close()
    return words_list


def apply_kmeans(cluster_number, text_list):
    print("apply_kmeans")
    print(text_list[:10])
    vectorizer = TfidfVectorizer(stop_words=load_stop_word(), encoding='unicode')
    X = vectorizer.fit_transform(text_list)

    model = KMeans(n_clusters=cluster_number, init='k-means++', max_iter=100, n_init=1)
    model.fit(X)

    print("Top terms per cluster:")
    order_centroids = model.cluster_centers_.argsort()[:, ::-1]
    terms = vectorizer.get_feature_names()
    output_string = ""
    for i in range(cluster_number):
        output_string += "Cluster %d:" + str(i) + "\n"
        for ind in order_centroids[i, :10]:
            output_string += str(terms[ind]) + "\n"
        output_string += "***********" + "\n"
    """
    output_string = ""
    output_string += "Cluster centers" + "\n"
    output_string += str(model.cluster_centers_)
    """
    output_string += "Actual Clusters:"
    output_string += str(model.labels_.tolist())
    file = open("predictions.txt", 'w', encoding='utf-8')
    file.write(output_string)
    file.close()

    # this code predict the cluster of the text in Y.
    """
    Y = vectorizer.transform(["chrome browser to open."])
    prediction = model.predict(Y)
    print(prediction)

    Y = vectorizer.transform(["My cat is hungry."])
    prediction = model.predict(Y)
    print(prediction)
    cluster_number
    """