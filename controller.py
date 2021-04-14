import pandas as pd
import os
import plotly.graph_objs as go
from pandas.errors import EmptyDataError
from plotly.subplots import make_subplots
from datetime import datetime, date, timedelta
from wordcloud import WordCloud
import dash_bootstrap_components as dbc
import plotly.express as px
from utils import check_dir, get_data_from_finmind
from nlp import get_tfidf, get_news, Tokenizer


def open_collapse(n, is_open):
    if n:
        return not is_open
    return is_open


class Controller:
    def __init__(self, data_dir, font_dir, company_id):
        self.data_dir = data_dir
        self.dir_ = self.get_data_dir(data_dir, company_id)
        self.font_dir = font_dir
        self.company_id = str(company_id)

    def reset(self, company_id):
        self.company_id = str(company_id)

    @staticmethod
    def get_data_dir(data_dir, company_id):
        return data_dir + str(company_id) + "/"

    def get_data(self, eng_dict, token, online_mode):
        company_id = self.company_id

        check_dir(company_id, self.data_dir)

        dir_ = self.dir_
        alert = False
        error = []

        for dirPath, dirNames, fileNames in os.walk(dir_):
            if company_id + '_Price.csv' not in fileNames or online_mode:
                alert = True
                error.append(get_data_from_finmind("TaiwanStockPrice", company_id, token,
                                                   "2009-01-01", dir_ + company_id + '_Price.csv'))

            if company_id + '_Revenue.csv' not in fileNames or online_mode:
                alert = True
                error.append(get_data_from_finmind("TaiwanStockMonthRevenue", company_id, token,
                                                   "2008-01-01", dir_ + company_id + '_Revenue.csv'))

            if company_id + '_Investors_Buy_Sell.csv' not in fileNames or online_mode:
                alert = True
                error.append(get_data_from_finmind("TaiwanStockInstitutionalInvestorsBuySell", company_id, token,
                                                   "2008-01-01", dir_ + company_id + '_Investors_Buy_Sell.csv'))

            if company_id + '_PER.csv' not in fileNames or online_mode:
                alert = True
                error.append(get_data_from_finmind("TaiwanStockPER", company_id, token, (date.today(
                ) - timedelta(days=90)).isoformat(), dir_ + company_id + '_PER.csv'))
            if company_id + '_Financial_Statements.csv' not in fileNames or online_mode:
                alert = True
                error.append(get_data_from_finmind("TaiwanStockFinancialStatements", company_id, token,
                                                   "2008-01-01", dir_ + company_id + '_Financial_Statements.csv'))
            if company_id + '_Margin_Trading.csv' not in fileNames or online_mode:
                alert = True
                error.append(get_data_from_finmind("TaiwanStockMarginPurchaseShortSale", company_id, token,
                                                   "2008-01-01", dir_ + company_id + '_Margin_Trading.csv'))
            if company_id + '_Shareholding.csv' not in fileNames or online_mode:
                alert = True
                error.append(get_data_from_finmind("TaiwanStockShareholding", company_id, token,
                                                   "2008-01-01", dir_ + company_id + '_Shareholding.csv'))
            if company_id + '_News.csv' not in fileNames or online_mode:
                alert = True
                error.append(get_data_from_finmind("TaiwanStockNews", company_id, token,
                                                   (date.today() - timedelta(days=20)).isoformat(),
                                                   dir_ + company_id + '_News.csv'))
        if online_mode:
            alert = False

        return eng_dict[int(company_id)] + ' Information', company_id, alert, online_mode & (not any(error)), any(
            error), ' <br>\r\n'.join(error)

    def update_news(self):
        company_id = self.company_id
        dir_ = self.dir_
        try:
            data = pd.read_csv(dir_ + company_id + '_News.csv')
            data = data.sort_values(by=['date'], ascending=False)
            table = data[['date', 'title']].copy()
            table.columns = ['Date', 'Title']
        except EmptyDataError:
            table = pd.DataFrame(['No Data'], columns=['Status'])

        table = dbc.Table.from_dataframe(
            table, striped=True, bordered=False, hover=True, responsive=True)

        return table

    def update_price_figure(self, start_date, end_date):
        dir_ = self.dir_
        company_id = self.company_id
        df_price = pd.read_csv(dir_ + company_id + '_Price.csv')
        df_price.index = pd.to_datetime(df_price['date'])

        df_investors_buy_sell = pd.read_csv(
            dir_ + company_id + '_Investors_Buy_Sell.csv')
        df_investors_buy_sell.index = pd.to_datetime(df_investors_buy_sell['date'])

        df_margin_trading = pd.read_csv(
            dir_ + company_id + '_Margin_Trading.csv')
        df_margin_trading.index = pd.to_datetime(df_margin_trading['date'])

        latest_price = df_price.iloc[-1].close
        latest_date = "Latest updated at " + str(df_price.iloc[-1].date)
        latest_up_down = df_price.iloc[-1].close - df_price.iloc[-2].close
        latest_percent = latest_up_down * 100 / df_price.iloc[-2].close

        if latest_up_down > 0:
            latest_up_down = '▲ ' + \
                             str(round(latest_up_down, 2)) + \
                             " (" + str(round(latest_percent, 2)) + "%)"
            latest_color = 'green'
        else:
            latest_up_down = '▼ ' + \
                             str(-round(latest_up_down, 2)) + \
                             " (" + str(-round(latest_percent, 2)) + "%)"
            latest_color = 'red'

        latest_style = {'textAlign': 'center', 'color': latest_color}

        filtered_df_price = df_price[(df_price.index >= start_date)
                                     & (df_price.index <= end_date)].copy()

        filtered_df_investors_buy_sell = df_investors_buy_sell[(df_investors_buy_sell.index >= start_date)
                                                               & (df_investors_buy_sell.index <= end_date)].copy()

        filtered_df_margin_trading = df_margin_trading[(df_margin_trading.index >= start_date) & (
                df_margin_trading.index <= end_date)].copy()

        filtered_df_investors_buy_sell.insert(
            2, "Net", filtered_df_investors_buy_sell.buy - filtered_df_investors_buy_sell.sell, True)
        filtered_df_investors_buy_sell = filtered_df_investors_buy_sell.groupby(
            filtered_df_investors_buy_sell.index).sum()

        fig = make_subplots(rows=4, cols=1,
                            shared_xaxes=True,
                            row_heights=[0.8, 0.2, 0.2, 0.2],
                            vertical_spacing=0.08,
                            subplot_titles=("Price", "Volume",
                                            "Investors Buy & Sell", "Margin Trading & Short Selling")
                            )

        fig.add_trace(go.Bar(x=filtered_df_price.index,
                             y=filtered_df_price.Trading_Volume, name='Trading Volume'), row=2, col=1)
        fig.add_trace(go.Bar(x=filtered_df_investors_buy_sell.index,
                             y=filtered_df_investors_buy_sell.Net, name='Net Volume'), row=3, col=1)

        filtered_df_margin_trading.insert(2, "NetMarginTrading", filtered_df_margin_trading.MarginPurchaseBuy -
                                          filtered_df_margin_trading.MarginPurchaseSell -
                                          filtered_df_margin_trading.MarginPurchaseCashRepayment, True)

        filtered_df_margin_trading.insert(2, 'NetShortSelling', filtered_df_margin_trading.ShortSaleSell -
                                          filtered_df_margin_trading.ShortSaleBuy -
                                          filtered_df_margin_trading.ShortSaleCashRepayment, True)

        fig.add_trace(go.Bar(x=filtered_df_margin_trading.index,
                             y=filtered_df_margin_trading.NetMarginTrading, name='Margin Trading'), row=4, col=1)

        fig.add_trace(go.Bar(x=filtered_df_margin_trading.index,
                             y=filtered_df_margin_trading.NetShortSelling, name='Short Selling'), row=4, col=1)

        max_buy_sell = max([abs(buy_sell)
                            for buy_sell in filtered_df_investors_buy_sell.Net])

        max_margin_short = max([abs(value)
                                for value in filtered_df_margin_trading.NetMarginTrading.append(
                filtered_df_margin_trading.NetShortSelling)])

        fig.update_yaxes(range=[-max_buy_sell * 1.1,
                                max_buy_sell * 1.1], row=3, col=1)

        fig.update_yaxes(range=[-max_margin_short * 1.1,
                                max_margin_short * 1.1], row=4, col=1)

        fig.add_trace(go.Candlestick(x=filtered_df_price.index,
                                     open=filtered_df_price['open'],
                                     high=filtered_df_price['max'],
                                     low=filtered_df_price['min'],
                                     close=filtered_df_price['close'],
                                     name='Price'), row=1, col=1)

        fig.update_xaxes(
            rangeslider_visible=False)

        fig.update_layout(legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1), margin=dict(l=20, r=50, t=50, b=20), showlegend=False, height=900, hovermode='x unified')

        return fig, 'From ' + str(start_date) + ' to ' + str(end_date), str(round(latest_price, 2)), str(
            latest_up_down), latest_style, latest_style, latest_date

    def update_revenue_figure(self, start_date, end_date):
        dir_ = self.dir_
        company_id = self.company_id

        df_revenue = pd.read_csv(dir_ + company_id + '_Revenue.csv')
        df_revenue.date = df_revenue.date.copy().shift(1)
        df_revenue.index = pd.to_datetime(df_revenue['date'])

        df_revenue['MoM'] = (df_revenue.revenue /
                             df_revenue.revenue.shift(1) - 1) * 100
        df_revenue['YoY'] = (df_revenue.revenue /
                             df_revenue.revenue.shift(12) - 1) * 100

        df_revenue = df_revenue.round({'YoY': 2, 'MoM': 2})

        if (datetime.strptime(end_date, "%Y-%m-%d") - datetime.strptime(start_date, "%Y-%m-%d")) > timedelta(days=365):
            filtered_df_revenue = df_revenue[
                (df_revenue.index >= start_date)
                & (df_revenue.index <= end_date)]
        else:
            filtered_df_revenue = df_revenue[
                (df_revenue.index >= datetime(year=datetime.strptime(
                    end_date, "%Y-%m-%d").year - 1, month=1, day=1))
                & (df_revenue.index <= end_date)]

        fig = make_subplots(rows=2, cols=1,
                            shared_xaxes=True,
                            vertical_spacing=0.1,
                            subplot_titles=("Revenue", "YoY & MoM")
                            )

        fig.add_trace(go.Bar(x=filtered_df_revenue.index,
                             y=filtered_df_revenue['revenue'], name='Month Revenue'), row=1, col=1)

        fig.add_trace(go.Scatter(x=filtered_df_revenue.index,
                                 y=filtered_df_revenue['YoY'], mode="lines+markers", name='YoY'), row=2, col=1)
        fig.add_trace(go.Scatter(x=filtered_df_revenue.index,
                                 y=filtered_df_revenue['MoM'], mode="lines+markers", name='MoM'), row=2, col=1)

        max_ratio = max([abs(ratio) for ratio in list(
            filtered_df_revenue['YoY']) + list(filtered_df_revenue['MoM'])])

        fig.update_layout(legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1), margin=dict(l=20, r=50, t=50, b=50), showlegend=False, height=450, hovermode='x unified')

        fig.update_yaxes(range=[filtered_df_revenue['revenue'].min(
        ) * 0.9, filtered_df_revenue['revenue'].max() * 1.1], row=1, col=1)
        fig.update_yaxes(range=[-max_ratio * 1.1, max_ratio *
                                1.1], ticksuffix="%", row=2, col=1)

        table = filtered_df_revenue[['date', 'revenue', 'YoY', 'MoM']]

        table.loc[:, 'revenue'] = table['revenue'].to_numpy() / 1000000

        table.columns = ['Date', 'Revenue (M)', 'YoY (%)', 'MoM (%)']

        table = table.round({'Revenue (M)': 2})

        table = table.sort_values(by=['Date'], ascending=False)

        table = dbc.Table.from_dataframe(
            table, striped=True, bordered=False, hover=True, responsive=True)

        return fig, table, str(round(df_revenue['YoY'].iloc[-1], 1)) + '%', str(
            round(df_revenue['MoM'].iloc[-1], 1)) + '%'

    def update_financial_statements_figure(self, start_date, end_date):
        dir_ = self.dir_
        company_id = self.company_id
        df = pd.read_csv(dir_ + company_id + '_Financial_Statements.csv')
        df.index = pd.to_datetime(df['date'])

        latest_eps = df[df['type'] == 'EPS'].iloc[-1].value

        if (datetime.strptime(end_date, "%Y-%m-%d") - datetime.strptime(start_date, "%Y-%m-%d")) > timedelta(
                days=5 * 365):
            filtered_df = df[(df.index >= start_date)
                             & (df.index <= end_date)]
        else:
            filtered_df = df[
                (df.index >= datetime(year=datetime.strptime(end_date, "%Y-%m-%d").year - 5, month=1, day=1))
                & (df.index <= end_date)]

        fig = make_subplots(rows=2, cols=1,
                            shared_xaxes=True,
                            vertical_spacing=0.1,
                            subplot_titles=("EPS", "Gross Margin")
                            )
        gross_margin = round(filtered_df[filtered_df['type'] == 'GrossProfit'].value * 100 / filtered_df[
            filtered_df['type'] == 'Revenue'].value, 2)

        latest_gross_margin = round(gross_margin[-1], 1)

        fig.add_trace(go.Scatter(x=filtered_df[filtered_df['type'] == 'EPS'].index,
                                 y=filtered_df[filtered_df['type'] == 'EPS'].value, mode="lines+markers", name='EPS'),
                      row=1, col=1)
        fig.add_trace(go.Scatter(x=filtered_df[filtered_df['type'] == 'Revenue'].index,
                                 y=gross_margin, mode="lines+markers", name='Gross Margin'), row=2, col=1)

        fig.update_yaxes(ticksuffix="%", row=2, col=1)

        fig.update_layout(legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1), margin=dict(l=20, r=50, t=50, b=50), height=450, showlegend=False, hovermode='x unified')

        table = df[df['date'] == df.iloc[-1].date]

        value = []

        for row in table.iterrows():
            if row[1].type != 'EPS':
                value.append(round(row[1].value / 1000000, 2))
            else:
                value.append(row[1].value)

        table.loc[:, 'value'] = value

        table.columns = ['Date', 'Stock Id', 'Type', 'Value (M)', df.iloc[-1].date]
        table = table[[df.iloc[-1].date, 'Value (M)']]

        table = dbc.Table.from_dataframe(
            table, striped=True, bordered=False, hover=True, responsive=True)

        return fig, table, str(latest_eps), str(latest_gross_margin) + "%"

    def update_per_ratio(self):
        dir_ = self.dir_
        company_id = self.company_id
        df = pd.read_csv(dir_ + company_id + '_PER.csv')
        return str(df.iloc[-1].PER), str(df.iloc[-1].PBR)

    def update_shareholding(self, start_date, end_date):
        dir_ = self.dir_
        company_id = self.company_id
        df = pd.read_csv(dir_ + company_id + '_Shareholding.csv')
        df.index = pd.to_datetime(df['date'])

        if (datetime.strptime(end_date, "%Y-%m-%d") - datetime.strptime(start_date, "%Y-%m-%d")) > timedelta(
                days=5 * 365):
            filtered_df = df[(df.index >= start_date)
                             & (df.index <= end_date)]
        else:
            filtered_df = df[
                (df.index >= datetime(year=datetime.strptime(end_date, "%Y-%m-%d").year - 5, month=1, day=1))
                & (df.index <= end_date)]

        fig = make_subplots(subplot_titles=("Foreign Investors' Shareholding",))
        fig.add_trace(go.Scatter(x=filtered_df.index, y=round(100 * filtered_df.ForeignInvestmentShares /
                                                              filtered_df.NumberOfSharesIssued, 2), name="Shares Held",
                                 fill='tozeroy'))
        fig.add_trace(go.Scatter(x=filtered_df.index, y=round(100 * (filtered_df.ForeignInvestmentShares +
                                                                     filtered_df.ForeignInvestmentRemainingShares) /
                                                              filtered_df.NumberOfSharesIssued, 2),
                                 name="Upper Limit", fill='tonexty'))
        fig.add_trace(go.Scatter(x=filtered_df.index, y=round(100 * filtered_df.NumberOfSharesIssued /
                                                              filtered_df.NumberOfSharesIssued, 2), name="Total"))

        fig.update_layout(margin=dict(l=20, r=50, t=50, b=50),
                          showlegend=False, height=450, hovermode='x unified')

        fig.update_yaxes(ticksuffix="%")

        return fig

    def update_nlp_news(self, n):
        dir_ = self.dir_
        company_id = self.company_id
        if n % 2 == 1:
            df = get_news(company_id, dir_)
            tokenizer = Tokenizer()
            # df['Tokenized Title'] = df['title'].apply(tokenize)
            # df['Tokenized Title'] = df['Tokenized Title'].apply(to_list)
            # df['Tokenized Title'] = df['Tokenized Title'].apply(clean)
            df['NER'] = df['title'].apply(tokenizer.tokenize_ner)
            df['NER Content'] = df['NER'].apply(tokenizer.get_word_from_ner_dict)
            df['NER Content'] = df['NER Content'].apply(tokenizer.clean)
            # df.to_pickle(dir_ + company_id + "_News_NER.pkl")
            ner_document = [" ".join(content) for content in df['NER Content']]
            df_tf, df_tfidf, df_sum_tfidf = get_tfidf(ner_document, df)
            word_cloud = WordCloud(background_color='white', font_path=self.font_dir, width=800,
                                   height=400).generate_from_frequencies(frequencies=df_sum_tfidf['TF-IDF'].to_dict())

            # img = BytesIO()
            # word_cloud.to_image().save(img, format='PNG')
            # return 'data:image/png;base64,{}'.format(base64.b64encode(img.getvalue()).decode())
            fig = px.imshow(word_cloud)

        else:
            layout = go.Layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            fig = go.Figure(layout=layout)

        fig.update_xaxes(showticklabels=False)
        fig.update_yaxes(showticklabels=False)
        fig.update_layout(margin=dict(l=20, r=50, t=50, b=50),
                          showlegend=False)

        return fig, n
