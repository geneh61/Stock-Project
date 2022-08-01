import re
import os
import nltk
import json
import random
import requests
import bs4 as bs
import pandas as pd
import yfinance as yf
from datetime import date
from datetime import datetime
from bs4 import BeautifulSoup
from yahoo_fin import stock_info as si
from nltk.sentiment import SentimentIntensityAnalyzer
from transformers import PegasusTokenizer, PegasusForConditionalGeneration

model_name = "human-centered-summarization/financial-summarization-pegasus"
tokenizer = PegasusTokenizer.from_pretrained(model_name)
model = PegasusForConditionalGeneration.from_pretrained(model_name)

api = 'JkPOzgcGkf5YtEFfjhTm01mrZDihS2YE7wFrXwSb'
opened_file = open("SimulatedStockInformation.txt", "a+")

heldStocks = []

exclude = ['maps', 'policies', 'preferences', 'accounts', 'support']
        
def getTickers():
    # gather stock symbols from major US exchanges
    df1 = pd.DataFrame( si.tickers_sp500() )
    df2 = pd.DataFrame( si.tickers_nasdaq() )
    df3 = pd.DataFrame( si.tickers_dow() )
    df4 = pd.DataFrame( si.tickers_other() )

    # convert DataFrame to list, then to sets
    sym1 = set( symbol for symbol in df1[0].values.tolist() )
    sym2 = set( symbol for symbol in df2[0].values.tolist() )
    sym3 = set( symbol for symbol in df3[0].values.tolist() )
    sym4 = set( symbol for symbol in df4[0].values.tolist() )

    # join the 4 sets into one. Because it's a set, there will be no duplicate symbols
    symbols = set.union( sym1, sym2, sym3, sym4 )

    # Some stocks are 5 characters. Those stocks with the suffixes listed below are not of interest.
    my_list = ['W', 'R', 'P', 'Q']
    del_set = set()
    sav_set = set()

    for symbol in symbols:
        if len( symbol ) > 4 and symbol[-1] in my_list:
            del_set.add( symbol )
        else:
            sav_set.add( symbol )

    return sav_set

def createStock(tickerInput):
    currentPrice = currPrice(tickerInput)
    addedStock = {
        "ticker" : tickerInput,
        "Avg Bought Price" : currentPrice,
        "Bought Date" : date.today(),
        "Number of Stocks" : 1000 // currentPrice, # (getPortfolioValue() / 100) // currPrice(tickerInput),
        "Total Value" : currentPrice * (1000 // currentPrice),
        "Current Price" : "",
        "Total Profit" : ""
    }
    return addedStock

def createStockFromFile(tickerInput):
    copiedStock = {}
    with open("SimulatedStockInformation.txt") as f:
        readtemp = f.readlines()
        location = 0
        for line in readtemp:
            if line.find(tickerInput) != -1:
                break
            location += 1
        for line2 in readtemp:
            if location != 0:
                location -= 1
                continue
            if line2.find("Sold At Price") != -1:
                return
            if len(copiedStock) == 7:
                break
            if line2 != '\n':
                k = (line2.split(':'))
                print(k)
                copiedStock[k[0][:-1]] = k[1][1:-1]
    return copiedStock

def addToHeld(tickerInput):
    heldStocks.append(createStock(tickerInput))
    return

def nearest():
    opened_file.seek(0)
    readlines = opened_file.readlines()
    today = datetime.today()
    dates = []
    for line in readlines:
        if len(line) == 11:
            dates.append(datetime(int(line[0:4]), int(line[5:7]), int(line[8:10])))
    return str(min(dates, key = lambda x: abs(x - today)))[:10]

def fileToHeld():
    nearestDate = nearest()
    location = 0
    opened_file.seek(0)
    file_lines = opened_file.readlines()
    for line in file_lines:
        if line.find(nearestDate) != -1:
            location = opened_file.tell()
            break
    opened_file.seek(location)
    for line in file_lines:
        if line.find("ticker") != -1:
            temp = line.replace(" ","")
            heldStocks.append(createStockFromFile(temp[7:-1]))
    return

def updateHeld(tickerInput):
    if recommendComparison(tickerInput) == -1:
        sell(tickerInput)
        return
    elif recommendComparison(tickerInput) == 1:
        buy(tickerInput)
        return
    toUpdate = getHeldStock(tickerInput)
    pricenow = currPrice(tickerInput)
    numStocks = float(toUpdate["Number of Stocks"])
    boughtAt = float(toUpdate["Avg Bought Price"])
    if numStocks == 0:
        updateValues = {
            "Current Price" : pricenow
        }
    else:
        updateValues = {
            "Current Price" : pricenow,
            "Total Profit" : (pricenow - boughtAt) * numStocks,
            "Total Value" : (numStocks * pricenow)
        }
    toUpdate.update(updateValues)
    return toUpdate

def getHeldTickers():
    heldTickers = []
    for i in range(len(heldStocks)):
        heldTickers.append(heldStocks[i]['ticker'])

    print(heldTickers)
    return heldTickers

def getRandomTickers():
    tickers = []
    templist = list(getTickers())
    for i in range(5):
        tickers.append(random.choice(templist))
    return tickers

def updateFile():
    opened_file.write(f"\n{date.today()}")
    for i in getHeldTickers():
        updateHeld(i)
    for i in getHeldTickers():
        writeToFile(i)
    return

def getHeldStock(tickerInput):
    location = 0
    for location in range(len(heldStocks)):
        if tickerInput == heldStocks[location]["ticker"]:           
            break
    return heldStocks[location]

def getPortfolioValue():
    value = 0
    for i in heldStocks:
        value += i["Total Value"]
    return value

def currPrice(tickerInput):
    stock_info = getChart(tickerInput)
    print(stock_info['meta'])
    return stock_info['meta']['regularMarketPrice']

def getChart(tickerInput):
    api_key = '9ETfGuQElE6hHrKUV6TaW3ZCdIRUlfrQ2OmUKMs5'
    url = 'https://yfapi.net/v8/finance/chart/' + tickerInput + '?region=US&lang=en'
    headers = {
        'x-api-key': api
    }
    response = requests.request("GET", url, headers=headers)
    json_obj = response.json()
    return json_obj['chart']['result'][0]

def yfRecommend(tickerInput):
    if tickerInput.upper() not in getTickers():
        print ("Ticker not valid")
        return
    api_key = '9ETfGuQElE6hHrKUV6TaW3ZCdIRUlfrQ2OmUKMs5'
    url = 'https://yfapi.net/ws/insights/v1/finance/insights?symbol=' + tickerInput
    headers = {
        'x-api-key': api
    }
    response = requests.request("GET", url, headers=headers)
    json_obj = response.json()
    try:
        return json_obj['finance']['result']['instrumentInfo']['recommendation']['rating']
    except:
        return 0

def readFromFile():
    opened_file

def addRandomToFile():
    tickers = getRandomTickers()
    opened_file.write(f"\n{date.today()}")
    for i in tickers:
        heldStocks.append(createStock(i))
        writeToFile(i)
    return

def writeToFile(tickerInput):
    for key, line in getHeldStock(tickerInput).items(): # hits first mention of ticker in file 
        opened_file.write(f"\n{key} : {line}")
    opened_file.write("\n")

def search_for_stock_news_urls(ticker):
    search_url = "https://www.google.com/search?q=yahoo+finance+{}&tbm=nws".format(ticker)
    r = requests.get(search_url)
    soup = BeautifulSoup(r.text, 'html.parser')
    atags = soup.find_all('a')
    hrefs = [link['href'] for link in atags]
    return hrefs 

def strip_unwanted_urls(urls, exclude):
    val = []
    for url in urls: 
        if 'https://' in url and not any(exclude_word in url for exclude_word in exclude):
            res = re.findall(r'(https?://\S+)', url)[0].split('&')[0]
            val.append(res)
    return list(set(val))

def scrape_and_process(URLs):
    ARTICLES = []
    for url in URLs: 
        r = requests.get(url)
        soup = BeautifulSoup(r.text, 'html.parser')
        paragraphs = soup.find_all('p')
        text = [paragraph.text for paragraph in paragraphs]
        words = ' '.join(text).split(' ')[:350]
        ARTICLE = ' '.join(words)
        ARTICLES.append(ARTICLE)
    return ARTICLES

def summarize(articles):
    summaries = []
    for article in articles:
        input_ids = tokenizer.encode(article, return_tensors='pt')
        output = model.generate(input_ids, max_length=55, num_beams=5, early_stopping=True)
        summary = tokenizer.decode(output[0], skip_special_tokens=True)
        summaries.append(summary[:511])
    return set(summaries)

def sentiment(dictionary, tickerInput):  
    sia = SentimentIntensityAnalyzer()
    summaries = dictionary.get(tickerInput)
    scores = []
    for value in summaries:
        scores.append(sia.polarity_scores(value))
    return scores

def recommendComparison(tickerInput):
    if tickerInput.upper() not in getTickers():
        print ("Ticker not valid")
        return
    yf = yfRecommend(tickerInput)
    articleScores = getSummaries(tickerInput)
    articleAvg = 0
    for i in articleScores:
        articleAvg += i['compound']
    articleAvg /= len(articleScores)
    print(yf)
    print(articleAvg)
    if yf == 'BUY':
        yf = 0.5
    elif yf == 'SELL':
        yf = -0.5
    elif yf == 'HOLD':
        yf = 0
    else:
        yf = 10

    if yf == 10:
        if articleAvg >= -1 and articleAvg < -0.25:
            return -1
        if articleAvg >= -0.25 and articleAvg <= 0.25:
            return 0
        if articleAvg > 0.25 and articleAvg <= 1:
            return 1
    elif yf == -0.5:
        if articleAvg < 0:
            return -1
        if articleAvg >= 0 and articleAvg < 0.5:
            return 0
        if articleAvg >= 0.5:
            return 1
    elif yf == 0:
        if articleAvg < -0.5:
            return -1
        if articleAvg >= -0.5 and articleAvg < 0.5:
            return 0
        if articleAvg >= 0.5:
            return 1
    elif yf == 0.5:
        if articleAvg < -0.5:
            return -1
        if articleAvg >= -0.5 and articleAvg < 0:
            return 0
        if articleAvg >= 0:
            return 1
    return

def buy(tickerInput):
    toUpdate = getHeldStock(tickerInput) # heldStocks[0] is wrong => filetoheld needs to change (addtoheld)
    pricenow = currPrice(tickerInput)
    numStocks = float(toUpdate["Number of Stocks"])
    buying = (1000 // pricenow)
    boughtAt = float(toUpdate["Avg Bought Price"])
    avgBought = (boughtAt * numStocks + pricenow * buying) / (numStocks * buying)
    updateValues = {
        "Avg Bought Price" : avgBought,
        "Number of Stocks" : numStocks + buying,
        "Current Price" : pricenow,
        "Total Profit" : ((numStocks + buying) * pricenow) - ((numStocks + buying) * avgBought),
        "Total Value" : ((numStocks + buying) * pricenow)
    }
    toUpdate.update(updateValues)
    return

def sell(tickerInput):
    toUpdate = getHeldStock(tickerInput) # heldStocks[0] is wrong => filetoheld needs to change (addtoheld)
    pricenow = currPrice(tickerInput)
    numStocks = float(toUpdate["Number of Stocks"])
    boughtAt = float(toUpdate["Avg Bought Price"])
    updateValues = {
        "Number of Stocks" : 0,
        "Sold At Price" : pricenow,
        "Current Price" : pricenow,
        "Total Profit" : (pricenow - boughtAt) * numStocks,
        "Total Value" : 0
    }
    toUpdate.update(updateValues)
    return

def getSummaries(tickerInput):
    raw_urls = {tickerInput:search_for_stock_news_urls(tickerInput)}
    cleaned_urls = {tickerInput:strip_unwanted_urls(raw_urls[tickerInput], exclude)}
    articles = {tickerInput:scrape_and_process(cleaned_urls[tickerInput])}
    summaries = {tickerInput:summarize(articles[tickerInput])}
    return(sentiment(summaries, tickerInput))


fileToHeld()
if getHeldTickers() == None:
    addRandomToFile()
updateFile()


"""
apikey = JkPOzgcGkf5YtEFfjhTm01mrZDihS2YE7wFrXwSb
apikey2 = 9ETfGuQElE6hHrKUV6TaW3ZCdIRUlfrQ2OmUKMs5
apikey3 = 4nHh2yxwg3aqWVa3Xprif449XSPWiwt84l4AOgK1
apikey4 = 7mUZmoXDDJ7Di7F9CbaUuagJD5Es7dma8sERLmeF
""" # free api keys used (100 requests/day)
