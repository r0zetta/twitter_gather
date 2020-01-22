#Clustering of tweets based on textual content using meta embeddings and community detection

This directory contains the code detailed in our blog post entitled "Identification And Categorization Of Toxic Twitter Posts Via Clustering" that can be found at: https://github.com/r0zetta/meta_embedding_clustering

In order to replicate our experiments, you'll need to gather some data from Twitter. To gather input data in the correct format for the toolchain provide here, use the twitter_gatherer.py tool from https://github.com/r0zetta/twitter_gather

If you run the twitter_gatherer.py tool in this directory, it should save data to the correct location for use in subsequent steps.

The notebooks here require a few python modules to be installed in order to work. Those modules are the following:

  - spacy https://spacy.io/
  - textacy https://chartbeat-labs.github.io/textacy/index.html
  - numba http://numba.pydata.org/
  - networkx https://networkx.github.io/
  - Louvain for networkx https://github.com/taynaud/python-louvain
  - sklearn https://scikit-learn.org/stable/
  - textblob https://textblob.readthedocs.io/en/dev/
  - gensim https://radimrehurek.com/gensim/auto_examples/index.html
  - word2vec https://radimrehurek.com/gensim/models/word2vec.html
  - doc2vec https://radimrehurek.com/gensim/models/doc2vec.html
  - sentence-transformers https://github.com/UKPLab/sentence-transformers

Once you have collected data, run each jupyter notebook in numbered order. Follow instructions provided in code comments within the notebooks.

Enjoy!
