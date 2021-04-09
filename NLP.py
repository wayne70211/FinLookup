import re

import pandas as pd
import plotly.graph_objects as go
from ckip_transformers.nlp import CkipWordSegmenter, CkipPosTagger, CkipNerChunker
from plotly.subplots import make_subplots
from sklearn.feature_extraction.text import TfidfVectorizer

stopwords = []
with open('./stopword.txt', 'r', encoding='UTF-8') as file:
    for data in file.readlines():
        data = data.strip()
        stopwords.append(data)
stopwords.append('蘋果日報')
stopwords.append('蘋果新聞網')

# Initialize drivers
ws_driver = CkipWordSegmenter(level=3)
pos_driver = CkipPosTagger(level=3)
ner_driver = CkipNerChunker(level=3)


def get_news(company_id, dir_):
    df = pd.read_csv(dir_ + company_id + '_News.csv')
    df = df.drop_duplicates(subset=['link'])
    df = df.sort_values(by=['date'], ascending=False)

    source = df['source'].tolist()

    df['title'] = df['title'].replace(source, "", regex=True)

    df = df.reset_index(drop=True)
    return df


def clean(content, remove_digit=True, stopwords=stopwords):
    clean_content = []
    for word in content:
        if remove_digit and re.search(r'\d+', word):
            continue
        if (len(word.strip()) < 2) or (word in stopwords):
            continue
        clean_content.append(word)
    return clean_content


def to_list(content):
    if type(content) == str:
        return content.split(', ')
    else:
        return None


def tokenize(content):
    if type(content) == str:

        # Initialize drivers
        sentence_list = content.split("，")
        word_sentence_list = ws_driver(sentence_list)
        return ", ".join(sum(word_sentence_list, []))
    else:
        return None


def NER_tokenize(content):
    if type(content) == str:
        sentence_list = content.split("，")

        # Initialize drivers
        entity_sentence_list = ner_driver(sentence_list)

        entity_sentence_set = set()
        for entity in entity_sentence_list:
            entity_sentence_set.update(entity)

        entity_sentence_list = list(entity_sentence_set)
        entity_list = []

        for entity in entity_sentence_list:
            entity_list.append((entity.ner, entity.word))

        return entity_list
    else:
        return None


def tokenNER(content):
    if content:
        return [word for tag, word in content if tag == 'ORG' or tag == 'PERSON']
    else:
        return []


def TFIDF(document, DATA, max_features=100, max_df=0.1, norm='l1'):
    tf_model = TfidfVectorizer(token_pattern=r"(?u)\b\w+\b", max_features=max_features, stop_words=['percentrank'],
                               max_df=max_df, smooth_idf=False, use_idf=False, norm=norm)
    tf = tf_model.fit_transform(document)
    df_tf = pd.DataFrame(tf.toarray(), columns=tf_model.get_feature_names(), index=DATA['date'])
    df_sum_tf = pd.DataFrame(df_tf.sum(axis=0), columns=['TF'])

    tfidf_model = TfidfVectorizer(token_pattern=r"(?u)\b\w+\b", max_features=max_features, stop_words=['percentrank'],
                                  max_df=max_df, smooth_idf=False, use_idf=True, norm=norm)
    tfidf = tfidf_model.fit_transform(document)
    df_tfidf = pd.DataFrame(tfidf.toarray(), columns=tfidf_model.get_feature_names(), index=DATA['date'])
    df_sum_tfidf = pd.DataFrame(df_tfidf.sum(axis=0), columns=['TF-IDF'])

    df_sum_tfidf = pd.concat([df_sum_tf, df_sum_tfidf], axis=1)
    df_sum_tfidf['IDF'] = df_sum_tfidf['TF-IDF'] / df_sum_tfidf['TF']
    df_sum_tfidf = df_sum_tfidf[['TF', 'IDF', 'TF-IDF']]
    df_sum_tfidf = df_sum_tfidf.sort_values(by='TF-IDF', ascending=False)

    return df_tf, df_tfidf, df_sum_tfidf


def Plot_freq(df_sum_tfidf, max_features=20, name=''):
    df = df_sum_tfidf[:max_features]

    fig = make_subplots(rows=2, cols=1,
                        shared_xaxes=True,
                        row_heights=[0.8, 0.2],
                        vertical_spacing=0.1)

    fig.add_trace(go.Bar(x=df.index, y=df['TF'], name='TF'), row=1, col=1)
    fig.add_trace(go.Bar(x=df.index, y=df['IDF'], name='IDF'), row=2, col=1)
    fig.add_trace(go.Bar(x=df.index, y=df['TF-IDF'], name='TF-IDF'), row=1, col=1)
    fig.update_layout(yaxis1=dict(range=[df['TF'].min() * 0.9, df['TF'].max() * 1.05]))
    fig.update_layout(yaxis2=dict(range=[df['IDF'].min() * 0.9, df['IDF'].max() * 1.05]))

    fig.update_layout(legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1), margin=dict(l=20, r=50, t=50, b=50), height=450, showlegend=False, hovermode='x unified')

    fig.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')
    return fig
