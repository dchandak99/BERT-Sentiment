# -*- coding: utf-8 -*-
"""BERT-IMDB

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1zaT4-IV-QdWAY5xRAiUL5-sRCUTknc8f
"""

from google.colab import drive
drive.mount('/content/gdrive')

!pip install transformers

import re
import os

import numpy as np
import torch
from torch.nn import CrossEntropyLoss
from torch.utils.data import DataLoader
from torch.utils.data import RandomSampler
from tqdm import tqdm, trange
from transformers import AdamW, get_linear_schedule_with_warmup
from transformers import BertConfig, BertForSequenceClassification, BertTokenizer

PAD_TOKEN_LABEL_ID = CrossEntropyLoss().ignore_index

BATCH_SIZE = 16
LEARNING_RATE_MODEL = 1e-5
LEARNING_RATE_CLASSIFIER = 1e-3
WARMUP_STEPS = 0
GRADIENT_ACCUMULATION_STEPS = 1
MAX_GRAD_NORM = 1.0
SEED = 42
NO_CUDA = False

def rpad(array, n):         # pad till atleast length n
  current_len = len(array)
  if current_len > n:
    return array[:n]
  extra = n - current_len
  return array + ([0] * extra)

def convert_to_embedding(tokenizer, sentences_with_labels):
  for sentence, label in sentences_with_labels:
    tokens = tokenizer.tokenize(sentence)
    tokens = tokens[:250]   # take only first 250
    
    to_send = tokenizer.convert_tokens_to_ids(["CLS"] + tokens + ["SEP"])
    bert_sent = rpad(to_send, n = 256)

    #Reference: https://www.geeksforgeeks.org/use-yield-keyword-instead-return-keyword-python/

    yield torch.tensor(bert_sent), torch.tensor(label, dtype = torch.int64)

def clean_line(line):
  line = line.strip().lower()
  line = line.replace("&nbsp;", " ")
  line = re.sub(r'<br(\s\/)?>', ' ', line)
  line = re.sub(r' +', ' ', line)  # merge multiple spaces into one

  return line

def read_imdb(file):
  data = []
  for line in open(file, 'r', encoding = "utf-8"):
    data.append(clean_line(line))

  return data

read_imdb("/content/gdrive/My Drive/BERT_sentiment/imdb_train.txt")

def make_dataloader(tokenizer, sampler = RandomSampler, train = False):

    file = "/content/gdrive/My Drive/BERT_sentiment/imdb_train.txt" if train else "/content/gdrive/My Drive/BERT_sentiment/imdb_test.txt"

    data = read_imdb(file)

    y = np.append(np.zeros(12500), np.ones(12500))
    #Format used here is one review per line, with first 12500 lines being positive(0), 
    #followed by 12500 negative lines(1).    

    sentences_with_labels = zip(data, list(y))

    dataset = list(convert_to_embedding(tokenizer, sentences_with_labels))
    
    sampler_func = sampler(dataset) if sampler is not None else None

    dataloader = DataLoader(dataset, sampler=sampler_func, batch_size = BATCH_SIZE)

    return dataloader

#tokenizer = BertTokenizer.from_pretrained('bert-base-uncased', do_lower_case=True)
#print(make_dataloader(tokenizer, train=True))





class Transformers:
  model = None

  def __init__(self, tokenizer):
    self.pad_token_label_id = PAD_TOKEN_LABEL_ID
    self.device = torch.device("cuda" if torch.cuda.is_available() and not NO_CUDA else "cpu")
    self.tokenizer = tokenizer

  def predict(self, sentence):
        if self.model is None or self.tokenizer is None:
            self.load()

        embeddings = list(convert_to_embedding([(sentence, -1)]))
        preds = self._predict_tags_batched(embeddings)
        return preds

  def evaluate(self, dataloader):
        from sklearn.metrics import classification_report
        y_pred = self._predict_tags_batched(dataloader)
        y_true = np.append(np.zeros(12500), np.ones(12500))

        score = classification_report(y_true, y_pred)
        print(score)

  def _predict_tags_batched(self, dataloader):
        preds = []
        self.model.eval()
        for batch in tqdm(dataloader, desc="Computing NER tags"):
            batch = tuple(t.to(self.device) for t in batch)

            with torch.no_grad():
                outputs = self.model(batch[0])
                _, is_neg = torch.max(outputs[0], 1)
                preds.extend(is_neg.cpu().detach().numpy())

        return preds

  def train(self, dataloader, model, epochs):
        assert self.model is None  # make sure we are not training after load() command
        model.to(self.device)
        self.model = model

        t_total = len(dataloader)    # GRADIENT_ACCUMULATION_STEPS * epochs

        # Prepare optimizer and schedule (linear warmup and decay)
        optimizer_grouped_parameters = [
            {"params": model.bert.parameters(), "lr": LEARNING_RATE_MODEL},
            {"params": model.classifier.parameters(), "lr": LEARNING_RATE_CLASSIFIER}
        ]
        optimizer = AdamW(optimizer_grouped_parameters)
        scheduler = get_linear_schedule_with_warmup(
            optimizer, num_warmup_steps=WARMUP_STEPS, num_training_steps=t_total)

        # Train!
        print("***** Running training *****")
        print("Training on %d examples", len(dataloader))
        print("Num Epochs = %d", epochs)
        print("Total optimization steps = %d", t_total)

        global_step = 0
        tr_loss, logging_loss = 0.0, 0.0
        model.zero_grad()
        train_iterator = trange(epochs, desc="Epoch")
        self._set_seed()
        for _ in train_iterator:
            epoch_iterator = tqdm(dataloader, desc="Iteration")
            for step, batch in enumerate(epoch_iterator):
                model.train()
                batch = tuple(t.to(self.device) for t in batch)
                outputs = model(batch[0], labels=batch[1])
                loss = outputs[0]  # model outputs are always tuple in pytorch-transformers (see doc)

                if GRADIENT_ACCUMULATION_STEPS > 1:
                    loss = loss / GRADIENT_ACCUMULATION_STEPS

                loss.backward()

                tr_loss += loss.item()
                if (step + 1) % GRADIENT_ACCUMULATION_STEPS == 0:
                    torch.nn.utils.clip_grad_norm_(model.parameters(), MAX_GRAD_NORM)

                    scheduler.step()  # Update learning rate schedule
                    optimizer.step()
                    model.zero_grad()
                    global_step += 1

        self.model = model

        return global_step, tr_loss / global_step

  def _set_seed(self):
    torch.manual_seed(SEED)
    if self.device == 'gpu':
      torch.cuda.manual_seed_all(SEED)

  def load(self, model_dir='weights/'):
    self.tokenizer = BertTokenizer.from_pretrained(model_dir)
    self.model = BertForSequenceClassification.from_pretrained(model_dir)
    self.model.to(self.device)

def train(epochs=20, output_dir="weights/"):
    num_labels = 2  # negative and positive reviews
    config = BertConfig.from_pretrained('bert-base-uncased', num_labels=num_labels)
    tokenizer = BertTokenizer.from_pretrained('bert-base-uncased', do_lower_case=True)
    model = BertForSequenceClassification.from_pretrained('bert-base-uncased', config=config)

    dataloader = make_dataloader(tokenizer, train=True)
    predictor = Transformers(tokenizer)
    predictor.train(dataloader, model, epochs)

    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)

def evaluate(model_dir="weights/"):
    tokenizer = BertTokenizer.from_pretrained('bert-base-uncased', do_lower_case=True)

    dataloader = make_dataloader(tokenizer, train=False, sampler=None)
    predictor = Transformers(tokenizer)
    predictor.load(model_dir=model_dir)
    predictor.evaluate(dataloader)


path = '/content/gdrive/My Drive/BERT_sentiment/weights/'
#os.makedirs(path, exist_ok=True)
train(epochs=10, output_dir=path)
evaluate(model_dir=path)

a = np.array([1,2,3])
list(a)

prll

!nvidia-smi

