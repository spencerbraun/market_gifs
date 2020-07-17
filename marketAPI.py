import datetime
import json
import sys

import requests
import pandas as pd


class AlphaVantage(object):
    def __init__(self):
        self.token = "HCIC00DMLUKHGMVE"
        self.base = "https://www.alphavantage.co/query?"

    def handleReq(self, url):
        urlAuth = url + f"&apikey={self.token}"
        req = requests.get(urlAuth)
        try:
            package = json.loads(req.content)
        except json.decoder.JSONDecodeError as e:
            print("JSONDecodeError, returning raw")
            package = req.content

        return package

    def stock(self, symbol: str, function: str, interval="15min", outputsize="full"):

        interval_str = f"&interval={interval}" if interval else ""
        size_str = f"&outputsize={outputsize}" if outputsize else ""
        url = f"{self.base}function={function}&symbol={symbol}{interval_str}{size_str}"

        return self.handleReq(url)

    def indicator(
        self,
        symbol: str,
        function: str,
        interval="15min",
        time_period="50",
        series_type="close",
    ):

        interval_str = f"&interval={interval}"
        time_str = f"&time_period={time_period}"
        series_str = f"&series_type={series_type}"
        url = f"{self.base}function={function}&symbol={symbol}{interval_str}{time_str}{series_str}"

        return self.handleReq(url)

    def intradayStock(self, symbol: str, interval="15min", size="compact"):

        return self.stock(symbol, "TIME_SERIES_INTRADAY", interval, size)

    def dailyStock(self, symbol: str, size="compact"):

        return self.stock(symbol, "TIME_SERIES_DAILY", interval=None, outputsize=size)

    def dailyAdjStock(self, symbol: str, size="compact"):

        return self.stock(
            symbol, "TIME_SERIES_DAILY_ADJUSTED", interval=None, outputsize=size
        )

    def lastQuote(self, symbol: str):

        return self.stock(symbol, "GLOBAL_QUOTE", interval=None, outputsize=None)

    def stockSMA(
        self, symbol: str, interval="15min", time_period="50", series_type="close"
    ):

        return self.indicator(symbol, "SMA", interval, time_period, series_type)


class IEXConnect(object):
    def __init__(self):
        self.token = "pk_f5dd907130be4fd2a0f079860ad31c3a"
        self.base = "https://cloud.iexapis.com/stable"

    def handleReq(self, url, connector):
        urlAuth = url + f"{connector}token={self.token}"
        req = requests.get(urlAuth)
        try:
            package = json.loads(req.content)
        except json.decoder.JSONDecodeError:
            print("JSONDecodeError, returning raw")
            package = req.content

        return package

    def stock(self, symbol: str):
        url = f"{self.base}/stock/{symbol}/quote"

        return self.handleReq(url, "?")

    def bulk(self, symbols: list):
        symString = ",".join(symbols).lower()
        url = f"{self.base}/stock/market/batch?symbols={symString}&types=quote"

        return self.handleReq(url, "&")


class YahooConnect(object):
    def __init__(self, ticker, startDate, endDate):
        self.ticker = ticker
        self.startDate = self.dateParse(startDate)
        self.endDate = self.dateParse(endDate)

    @staticmethod
    def numTest(data):
        try:
            float(data)
            return True
        except ValueError:
            return False

    @staticmethod
    def stamp(datetime):
        return str(int(datetime.timestamp()))

    @staticmethod
    def dateParse(date) -> datetime:
        if isinstance(date, (int, float)):
            return datetime.datetime.strptime(str(int(date)), "%Y%m%d")
        elif isinstance(date, str):

            try:
                if len(date) == 8:
                    if "/" in date:
                        return datetime.datetime.strptime(date, "%m/%d/%y")
                    else:
                        return datetime.datetime.strptime(date, "%Y%m%d")
                elif len(date) == 10:
                    if "-" in date:
                        return datetime.datetime.strptime(date, "%Y-%m-%d")
                    else:
                        return datetime.datetime.strptime(date, "%m/%d/%Y")
                else:
                    return datetime.datetime.strptime(date, "%b %d, %Y")
            except ValueError:
                raise DateException("Could not parse date format")
        elif isinstance(date, datetime.datetime):
            return date
        else:
            raise DateException("Could not determine date datatype")

    def dateChunk(self, interval):
        dateDiff = self.endDate - self.startDate
        chunkNumber = math.ceil(dateDiff.days / interval)

        dateBounds = [
            self.startDate + (dateDiff * i / chunkNumber) for i in range(chunkNumber)
        ]
        dateBounds.append(self.endDate)

        return dateBounds

    def stockPrices(self, breaks=False):
        dateList = self.dateChunk(100)
        dfList = []

        for i in range(len(dateList) - 1):
            startStamp = self.stamp(dateList[i])
            endStamp = self.stamp(dateList[i + 1])
            link = (
                f"https://finance.yahoo.com/quote/{self.ticker}"
                f"/history?period1={startStamp}&period2={endStamp}"
                f"&interval=1d&filter=history&frequency=1d"
            )

            response = requests.get(link)
            soup = bs4.BeautifulSoup(response.text, "lxml")

            df = pd.read_html(
                soup.find("table", {"data-test": "historical-prices"}).prettify()
            )[0]

            df.columns = map(lambda x: x.replace("*", ""), df.columns)
            prices = df[df.Close.apply(self.numTest)].copy()
            dfList.append(prices)
            if breaks:
                sleep(2)

        allDates = pd.concat(dfList)
        allDates.Date = allDates.Date.apply(self.dateParse)
        allDates = allDates.sort_values("Date").drop_duplicates().reset_index(drop=True)

        return allDates
