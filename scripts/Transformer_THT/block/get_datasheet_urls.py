#!/usr/bin/env python3
from bs4 import BeautifulSoup
import requests
import sys
import re
import csv

def get_url(name, outputs=""):
    splitted = name.replace('/', '').replace(',', '').split('-')
    series = splitted[0].lower()
    power = splitted[1]
    if len(splitted) > 2:
        outputs = splitted[2]
    else:
        outputs = outputs
    voltage = 12 # seems to exist always

    return ("https://www.block.eu/en_EN/productversion/"
            f"{series}-{power}{outputs}{voltage}/")

delimiter = ";"
out = []
with open(sys.argv[1], 'r') as f:
    for row in csv.reader(f, delimiter=delimiter):
        if row[1]:
            out.append(row)
        else:
            print(f"Fetching datasheet for {row[0]}")
            url = get_url(row[0])
            print(url)
            page = requests.get(url).text
            soup = BeautifulSoup(page, "lxml")
            link = soup.find_all("a", href=re.compile("datasheet"))
            href = link[0].get('href')
            print(href)
            out.append([row[0], href] + row[2:])

with open(sys.argv[1], 'w') as f:
    writer = csv.writer(f, delimiter=delimiter, quoting=csv.QUOTE_MINIMAL)
    writer.writerows(out)
