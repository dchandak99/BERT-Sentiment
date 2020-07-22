# Sentiment Analysis by BERT:
[BERT](https://github.com/google-research/bert) is state-of-the-art natural language processing model from Google. Using its latent space, it can be repurpossed for various NLP tasks, such as sentiment analysis.  

I am using [Hugging Face Transformers](https://github.com/huggingface/transformers) and Pytorch and the task is predicting positivity / negativity on IMDB reviews.

### Data:  
Firstly, you need to prepare [IMDB data](https://www.kaggle.com/lakshmi25npathi/imdb-dataset-of-50k-movie-reviews) which is publicly available. Format used here is one review per line, with first 12500 lines being positive, followed by 12500 negative lines. Positive has been encoded with 0 and negative with 1.

### Code:  
Currently, you can view the code [here](https://colab.research.google.com/drive/1zaT4-IV-QdWAY5xRAiUL5-sRCUTknc8f?usp=sharing). It will be uploaded on completion.
