import os
import requests
import pandas as pd


def create_folder(directory):
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
    except OSError:
        print('Error: Creating directory. ' + directory)


def check_dir(company_id, directory):
    for dirPath, dirNames, fileNames in os.walk(directory):
        if company_id not in dirNames:
            create_folder(directory + str(company_id))


def get_data_from_finmind(dataset, company_id, token, start_date, output_dir):
    url = "https://api.finmindtrade.com/api/v4/data"
    parameter = {
        "dataset": dataset,
        "data_id": str(company_id),
        "start_date": start_date,
        "token": token,
    }
    try:
        resp = requests.get(url, params=parameter)
        data = resp.json()
        data = pd.DataFrame(data["data"])
        data.to_csv(output_dir, index=False)
    except RuntimeError:
        error = "Read " + dataset + " Failed"
    else:
        error = ""
    return error


def get_stock_dict():
    stock_table = pd.read_json('StockTable.json')
    tw_dict = pd.Series(stock_table['公司簡稱'].values, stock_table['公司代號']).to_dict()
    eng_dict = pd.Series(stock_table['英文簡稱'].values, stock_table['公司代號']).to_dict()
    return tw_dict, eng_dict





