# -*- coding: utf-8 -*-
"""PretrainedModels.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1U0GzZqHJjGTtM-1Tg01WKo8DLQAD2dvx
"""

from spacy.lang.hi import Hindi 
nlp = Hindi()

import requests 
url = "https://dl.fbaipublicfiles.com/fasttext/vectors-crawl/cc.hi.300.vec.gz"
r = requests.get(url, allow_redirects=True)
fpath = url.split("/")[-1]
with open(fpath, "wb") as fw:
  fw.write(r.content)

! python -m spacy init-model hi ./hi_vectors_wiki_lg --vectors-loc cc.hi.300.vec.gz

import spacy
nlp_hi = spacy.load("./hi_vectors_wiki_lg")

import numpy as np

def preprocess_data(with_pos_tag = False):
  total_states = []
  f = open("dataset.txt", "r",encoding = 'utf-8')
  lines = f.readlines()
  line = ""
  for word in lines:
    word = word.split('\t')

    if(len(word) != 1):
      tag = word[1].strip()
      word = word[0].strip()
      
      if(with_pos_tag == False):
        total_states.append(word)
      else:
        total_states.append(word + " " + tag)

  train_size = (len(total_states) * 80)//100

  train_set = total_states[:train_size]
  test_set = total_states[train_size:]

  X_train = []
  for word in range(len(train_set)):
    if(word%20000 == 0):
      print(word)
    doc = nlp_hi(train_set[word])
    current_vector = doc[0].vector
    X_train.append(current_vector)

  X_test = []
  for word in range(len(test_set)):
    if(word%20000 == 0):
      print(word)
    doc = nlp_hi(test_set[word])
    current_vector = doc[0].vector
    X_test.append(current_vector)

  X_train = np.array(X_train)
  X_test = np.array(X_test)
  return train_set, test_set, X_train, X_test

def measure_accuracy(train_set, test_set, Y_train, Y_test, with_pos_tag = True):
  file2 = open('hin-token-chunk-conll-treebank.txt', 'r')
  result_lines = file2.readlines()
  tags = {}

  for line in result_lines:
    word = line.split('\t')
    if(len(word) != 1):
      token = word[0].strip()
      word = word[1].strip()
      if(word[0] == 'B'):
        tags[token] = 0

      else:
        tags[token] = 1

  if(with_pos_tag == True):
    for i in range(len(train_set)):
      train_set[i] = train_set[i].split()[0]

    for i in range(len(test_set)):
      test_set[i] = test_set[i].split()[0]


  total_correct = 0
  for i in range(len(Y_train)):
    if(Y_train[i] == tags[train_set[i]]):
      total_correct += 1

  print("Training Accuracy is : ", max(100 - (total_correct / len(train_set)*100), (total_correct / len(train_set)*100)))
  train_accuracy = max(100 - (total_correct / len(train_set)*100), (total_correct / len(train_set)*100))
  total_correct = 0
  for i in range(len(test_set)):
    if(Y_test[i] == tags[test_set[i]]):
      total_correct += 1

  print("Testing Accuracy is : ", max(100 - (total_correct / len(test_set)*100), (total_correct / len(test_set)*100)))
  test_accuracy = max(100 - (total_correct / len(test_set)*100), (total_correct / len(test_set)*100))
  return train_accuracy, test_accuracy

train_set, test_set, X_train, X_test = preprocess_data()

from sklearn.cluster import KMeans
modelkmeans = KMeans(n_clusters=2, init='k-means++', n_init=10, n_jobs = -1)
modelkmeans.fit(X_train)

Y_train = modelkmeans.predict(X_train)
Y_test = modelkmeans.predict(X_test)

measure_accuracy(train_set, test_set, Y_train, Y_test)

!pip install hmmlearn

from hmmlearn import hmm

model = hmm.GaussianHMM(n_components=2)
model.fit(X_train)

Y_train = model.predict(X_train)
Y_test = model.predict(X_test)

measure_accuracy(train_set, test_set, Y_train, Y_test)

import pickle
pickle.dump(modelkmeans, open("model_embedding_without_pos_kmeans.pkl", "wb"))
pickle.dump(model, open("model_embedding_without_pos_hmm.pkl", "wb"))

from sklearn.decomposition import PCA

train_accuracy = []
test_accuracy = []
for components in range(1, 200):
  trying_vector = X_train.copy()
  pca = PCA(n_components=components)
  pca.fit(trying_vector)
  trying_vector = pca.transform(trying_vector)
  modelkmeans = KMeans(n_clusters=2, init='k-means++', n_init=10, n_jobs = -1)
  modelkmeans.fit(trying_vector)
  train_results = modelkmeans.predict(trying_vector)
  testing_vector = X_test.copy()
  testing_vector = pca.transform(testing_vector)
  test_results = modelkmeans.predict(testing_vector)
  train_acc, test_acc = measure_accuracy(train_set, test_set, train_results, test_results)
  train_accuracy.append(train_acc)
  test_accuracy.append(test_acc)
  if(components % 50 == 0):
    print(components)

import matplotlib.pyplot as plt

x = [i for i in range(1, 200)]
y = train_accuracy
y2 = test_accuracy
plt.plot(x, y, label = "train-accuracy")
plt.plot(x, y2, label = "test-accuracy")

plt.xlabel('Number of Components')
plt.ylabel('Accuracy')
plt.title('PCA Prediction!')

plt.legend()
plt.show()
plt.savefig('Pretrained_embedding_kmean_without_pos.png')

train_accuracy = []
test_accuracy = []
for components in range(1, 200):
  trying_vector = X_train.copy()
  pca = PCA(n_components=components)
  pca.fit(trying_vector)
  trying_vector = pca.transform(trying_vector)
  modelkmeans = hmm.GaussianHMM(n_components=2)
  modelkmeans.fit(trying_vector)
  train_results = modelkmeans.predict(trying_vector)
  testing_vector = X_test.copy()
  testing_vector = pca.transform(testing_vector)
  test_results = modelkmeans.predict(testing_vector)
  train_acc, test_acc = measure_accuracy(train_set, test_set, train_results, test_results)
  train_accuracy.append(train_acc)
  test_accuracy.append(test_acc)
  if(components % 50 == 0):
    print(components)

import matplotlib.pyplot as plt

x = [i for i in range(1, 200)]
y = train_accuracy
y2 = test_accuracy
plt.plot(x, y, label = "train-accuracy")
plt.plot(x, y2, label = "test-accuracy")

plt.xlabel('Number of Components')
plt.ylabel('Accuracy')
plt.title('PCA Prediction!')

plt.legend()
plt.show()
plt.savefig('Pretrained_embedding_hmm_without_pos.png')

train_set, test_set, X_train, X_test = preprocess_data(with_pos_tag = True)

from sklearn.cluster import KMeans

modelkmeans = KMeans(n_clusters=2, init='k-means++', n_init=10, n_jobs = -1)
modelkmeans.fit(X_train)

Y_train = modelkmeans.predict(X_train)
Y_test = modelkmeans.predict(X_test)

measure_accuracy(train_set, test_set, Y_train, Y_test, with_pos_tag = True)

!pip install hmmlearn
from hmmlearn import hmm

model = hmm.GaussianHMM(n_components=2)
model.fit(X_train)

Y_train = model.predict(X_train)
Y_test = model.predict(X_test)

measure_accuracy(train_set, test_set, Y_train, Y_test)

import pickle
pickle.dump(modelkmeans, open("model_embedding_with_pos_kmeans.pkl", "wb"))
pickle.dump(model, open("model_embedding_with_pos_hmm.pkl", "wb"))

from sklearn.decomposition import PCA
from sklearn.cluster import KMeans

train_accuracy = []
test_accuracy = []
for components in range(1, 200):
  trying_vector = X_train.copy()
  pca = PCA(n_components=components)
  pca.fit(trying_vector)
  trying_vector = pca.transform(trying_vector)
  modelkmeans = KMeans(n_clusters=2, init='k-means++', n_init=10, n_jobs = -1)
  modelkmeans.fit(trying_vector)
  train_results = modelkmeans.predict(trying_vector)
  testing_vector = X_test.copy()
  testing_vector = pca.transform(testing_vector)
  test_results = modelkmeans.predict(testing_vector)
  train_acc, test_acc = measure_accuracy(train_set, test_set, train_results, test_results)
  train_accuracy.append(train_acc)
  test_accuracy.append(test_acc)
  if(components % 50 == 0):
    print(components)

import matplotlib.pyplot as plt

x = [i for i in range(1, 200)]
y = train_accuracy
y2 = test_accuracy
plt.plot(x, y, label = "train-accuracy")
plt.plot(x, y2, label = "test-accuracy")

plt.xlabel('Number of Components')
plt.ylabel('Accuracy')
plt.title('PCA Prediction!')

plt.legend()
plt.show()
plt.savefig('Pretrained_embedding_kmean_with_pos.png')

!pip install hmmlearn
from hmmlearn import hmm

train_accuracy = []
test_accuracy = []
for components in range(1, 200):
  trying_vector = X_train.copy()
  pca = PCA(n_components=components)
  pca.fit(trying_vector)
  trying_vector = pca.transform(trying_vector)
  modelkmeans = hmm.GaussianHMM(n_components=2)
  modelkmeans.fit(trying_vector)
  train_results = modelkmeans.predict(trying_vector)
  testing_vector = X_test.copy()
  testing_vector = pca.transform(testing_vector)
  test_results = modelkmeans.predict(testing_vector)
  train_acc, test_acc = measure_accuracy(train_set, test_set, train_results, test_results)
  train_accuracy.append(train_acc)
  test_accuracy.append(test_acc)
  if(components % 50 == 0):
    print(components)

import matplotlib.pyplot as plt

x = [i for i in range(1, 200)]
y = train_accuracy
y2 = test_accuracy
plt.plot(x, y, label = "train-accuracy")
plt.plot(x, y2, label = "test-accuracy")

plt.xlabel('Number of Components')
plt.ylabel('Accuracy')
plt.title('PCA Prediction!')

plt.legend()
plt.show()
plt.savefig('Pretrained_embedding_hmm_without_pos.png')
