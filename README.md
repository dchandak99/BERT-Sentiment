# Sentiment Analysis by BERT:
[BERT](https://github.com/google-research/bert) is state-of-the-art natural language processing model from Google. Using its latent space, it can be repurpossed for various NLP tasks, such as sentiment analysis.  

I am using [Hugging Face Transformers](https://github.com/huggingface/transformers) and Pytorch and the task is predicting positivity / negativity on IMDB reviews.

### Data:  
Firstly, you need to prepare [IMDB data](https://www.kaggle.com/lakshmi25npathi/imdb-dataset-of-50k-movie-reviews) which is publicly available. Format used here is one review per line, with first 12500 lines being positive, followed by 12500 negative lines. Positive has been encoded with 0 and negative with 1.  
  
You can download data and weights (in the correct format) directly from my drive link [here](https://drive.google.com/drive/folders/1kgy7_0XwGGfbWsY6Y5PUpoCLwoSLt_Rc?usp=sharing).

### Results:  
|              | precision | recall | f1-score | support |
|--------------|-----------|--------|----------|---------|
|          0.0 |      0.90 |   0.93 |     0.91 |   12500 |
|          1.0 |      0.93 |   0.90 |     0.91 |   12500 |
|              |           |        |          |         |
|     accuracy |           |        |     0.91 |   25000 |
|    macro avg |      0.91 |   0.91 |     0.91 |   25000 |
| weighted avg |      0.91 |   0.91 |     0.91 |   25000 |

### Optimization:  
I will optimize the hyperparameters later to get as close to the sota as possible.

### Code:  
[Code](BERT-IMDB.ipynb) has been uploaded as a notebook.
