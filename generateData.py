#! /Users/spencerbraun/dev/virtualenvs/venv3/bin/python
import argparse
import json
import os
import pickle
import sys
from collections import defaultdict
from datetime import datetime

import pandas as pd

from marketAPI import AlphaVantage


TODAY = pd.Timestamp.today()
TODAY_DATE_STR = TODAY.date().strftime("%Y%m%d")
TODAY_TIMESTAMP = TODAY.timestamp()

LIST_DICT = {
    'active': "https://finance.yahoo.com/most-active",
    'gainers': "https://finance.yahoo.com/screener/predefined/day_gainers",
    'losers': "https://finance.yahoo.com/screener/predefined/day_losers"
}

ROBINHOOD_POP = "https://robinhood.com/collections/100-most-popular"

def shortConvert(cap):
    multiplier = cap[-1]
    number = {'M': 1e6, 'B': 1e9, 'T': 1e12}
    
    return float(cap[:-1]) * number.get(multiplier)


def processList(market_df):
    renameDict = {
        'Price (Intraday)': 'Price',
        '% Change': 'PercentChange',
        'Today': 'PercentChange'
    }
    market_df.rename(columns=renameDict, inplace=True)
    market_df.PercentChange = market_df.PercentChange.apply(lambda x: float(str(x).strip("+%")))
    market_df.loc[:, 'Market Cap'] = market_df.loc[:, 'Market Cap'].apply(shortConvert)
    
    
    return market_df
    

def robinList():
    listPath = f'data_{TODAY_DATE_STR}/robinList.pkl'
    if os.path.exists(listPath):
        if os.path.getsize(listPath) > 0:
            with open(listPath, 'rb') as f:
                robin = pickle.load(f)
    else:
        robin_df = pd.read_html(ROBINHOOD_POP)[0]
        robin = robin_df[['Symbol', 'Name']].to_records(index=False)
        with open(listPath, 'wb') as f:
            pickle.dump(robin, f)
    
    return robin
        

def chooseSym(sourceURL, criterion='PercentChange', type='winner'):
    
    market_df = pd.read_html(sourceURL)[0]
    processed = processList(market_df)
    
    robin = robinList()
    robinSyms = [x[0] for x in robin]
    
    select = processed.loc[processed.Symbol.isin(robinSyms)]
    index = -1 if type == 'winner' else 0
    
    if not select.empty:
        symbol, name = (
            select
            .sort_values(criterion)
            .iloc[index]
            [['Symbol', 'Name']]
            .tolist()
        )
        
    else:
        symbol, name = (
            processed
            .sort_values(criterion)
            .loc[processed['Market Cap'] > 2e10]
            .iloc[index]
            [['Symbol', 'Name']]
            .tolist()
        )
        
    return symbol, name
    

def getMarketData(symbol, name):
    
    interval="5min"

    av = AlphaVantage()
    intraday = av.intradayStock(symbol, interval=interval, size="compact")
    daily = av.dailyAdjStock(symbol, size='full')
    
    
    intradayData = intraday[f'Time Series ({interval})']
    intradayDict = defaultdict(dict)
    for k, v in intradayData.items():
        date_key = datetime.strptime(k, "%Y-%m-%d %H:%M:%S")
        intradayDict[date_key]['close'] = v['4. close']
        intradayDict[date_key]['volume'] = v['5. volume']

    dailyData = daily[f'Time Series (Daily)']
    dailyDict = defaultdict(dict)
    for k, v in dailyData.items():
        date_key = datetime.strptime(k, "%Y-%m-%d")
        dailyDict[date_key]['close'] = v['5. adjusted close']
        dailyDict[date_key]['volume'] = v['6. volume']
    
    with open(f'data_{TODAY_DATE_STR}/name.csv', 'w') as f:
        f.write(f'{name}')
    
    (
        pd.DataFrame(dailyDict).T
        .iloc[:200]
        .reset_index()
        .rename(columns={'index': 'date'})
        .to_csv(f'data_{TODAY_DATE_STR}/{symbol}_daily_{TODAY_TIMESTAMP}.csv', index=False)
    )
    
    
    (
        pd.DataFrame(intradayDict).T
        .reset_index()
        .rename(columns={'index': 'time'})
        .to_csv(f'data_{TODAY_DATE_STR}/{symbol}_intraday_{TODAY_TIMESTAMP}.csv', index=False)
    )


def main():
    parser = argparse.ArgumentParser(description='Args for data generation')
    parser.add_argument('--criterion', default='PercentChange', type=str)
    parser.add_argument('-l', '--list', help=('Stock list to reference. '
        'Choose from active, gainers, losers')
        )

    args = parser.parse_args()
    
    if not os.path.exists(f'data_{TODAY_DATE_STR}'):
        os.mkdir(f'data_{TODAY_DATE_STR}')
    
    sourceURL = LIST_DICT.get(args.list)
    listType = 'loser' if args.list == 'losers' else 'winner'
    symbol, name = chooseSym(sourceURL, criterion='PercentChange', type=listType)
    
    
    getMarketData(symbol, name)
    
    
    
if __name__ == '__main__':
    main()
