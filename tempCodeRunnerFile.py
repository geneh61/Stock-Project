from datetime import date
from datetime import datetime

opened_file = open("SimulatedStockInformation.txt", "a+")
opened_file.seek(0)
readlines = opened_file.readlines()
today = datetime.today()
dates = []
for line in readlines:
    if len(line) == 11:
        print(line[0:4], line[5:7])
        dates.append(datetime(int(line[0:4]), int(line[5:7]), int(line[8:10])))
print(dates)
test = str(min(dates, key = lambda x: abs(x - today)))[:10]
print(test)