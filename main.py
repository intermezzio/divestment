import re
import os
import numpy as np
import pandas as pd
import requests
from timeit import timeit
from time import sleep
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

from flask import Flask, flash, redirect, render_template, request, session, abort, url_for, Response, send_file
app = Flask(__name__)
app.config.from_object(__name__)
app.config['SECRET_KEY'] = '1243bed87ac87eb87a87ed'


driver = webdriver.Firefox()

@app.route("/", methods=["GET", "POST"])
def homepage():
	"""
	Take in data from the form and calculate stuff with it
	"""
	if request.method == "POST":
		req = request.form
		


	return render_template("public/index.html")

# @app.route("/calculate", methods=["GET", "POST"])
# def calculate():
# 	return render_template("public/index.html")


def make_spreadsheet(salary, savings=0, age=20, perc401k=10, match401k=True):
	"""
	Spreadsheet Data Calculations

	"""
	spreadsheetData = pd.DataFrame(columns=["Month", "Age", "Salary", "401k"])

	monthly_salary = salary / 12
	
	# 401k
	save401k = monthly_salary * perc401k
	company401k = save401k if match401k else 0
	total401k = save401k + company401k

	monthly_salary_minus_401k = monthly_salary - save401k


def getFederalIncomeTax(income, status="single"):
	"""given an income and filing status, return the annual income tax"""
	if status not in ("single", "married", "hoh"):
		raise AttributeError("Bad Status")

	response = requests.get(f"https://api.taxapi.net/income/{status}/{income}")
	tax = response.json()
	
	return tax

def getAllIncomeTax(income, status="single", state="CT", year=2019, fica=True):
	"""	
	Use taxee.io to get more advanced tax data
	"""
	headers = {
		"Authorization": open("keys/taxee.txt", 'r').read().strip(),
		"Content-Type": "application/x-www-form-urlencoded"
	}
	data = {
		"pay_rate": income,
		"filing_status": status,
		"state": state
	}
	response = requests.post(
		f'https://taxee.io/api/v2/calculate/{year}',
		headers=headers,
		data=data
	)

	tax_annual = response.json()["annual"]

	fed_tax, st_tax, fica_tax = [tax_annual[form]["amount"] or 0 for form in ("federal", "state", "fica")]
	print(fed_tax, st_tax, fica_tax)
	return sum([fed_tax, st_tax, (fica_tax if fica else 0)])

def searchStocks(fundType = None, diversified = False, sustainable = False):
	"""
	returns a list of tickers and info about stocks in the form of a DataFrame
	fundType: None, FO (Open Ended Funds), FE (ETFs)
	"""
	global driver # firefox browser

	# go to this site
	url = "https://fossilfreefunds.org/funds?"
	params = list()
	params.append(f"type={fundType}") if fundType in ("FO", "FE") else None # fundType
	params.append(f"div=false") if diversified else None
	params.append(f"sri=true&srt=ussif") if sustainable else None # sustainability
	params.append(f"dsc=false")
	params.append(f"srt=usd_relative_footprint")
	url += "&".join(params)
	print(url)
	response = driver.get(url)
	# print("driver:\n",driver)
	clickButton(driver, b_id="tutorial-close___3g8eR")
	clickButton(driver, b_id="more-funds___2L89j")
	clickButton(driver, b_id="more-funds___2L89j")
	clickButton(driver, b_id="more-funds___2L89j")	

	sleep(1)
	htmltable = delayResponse()

	stocksDF = pd.read_html(htmltable)[0]
	print(stocksDF.shape[0], "funds")
	# response_rendered = response.html.render()
	# response_html = BeautifulSoup(response, 'html.parser')
	
	# response_html.find('table')
	# stock_table = response_html.select('table')

	tickerFromName = np.vectorize(lambda name: name[name.index("Ticker: ")+8:])
	removeTicker = np.vectorize(lambda name: name[:name.index("Ticker: ")])

	stocksDF["Ticker"] = tickerFromName(stocksDF["Fund name"])
	stocksDF["Fund"] = removeTicker(stocksDF["Fund name"])

	stocksDF.drop("Fund name", axis=1, inplace=True)

	return stocksDF

def priceFromTicker(tickers):
	"""
	get a price for a ticker

	"""
	api_key = open("keys/iexcloud.txt", 'r').read().strip()
	stockJSON = requests.get(f"https://sandbox.iexapis.com/stable/stock/AAAU/quote?token={api_key}").json()

	tickerprice = stockJSON["latestPrice"]
	# csv_data = requests.get()
	return tickerprice

def clickButton(driver, b_id="tutorial-close___3g8eR", tries=0):
	try:
		driver.find_element_by_css_selector(f"button.{b_id}").click()
	except Exception:
		if(tries > 100):
			raise Exception("Wifi is Terrible!")
		sleep(0.5)
		print("clickDelay", b_id)
		clickButton(driver, b_id=b_id, tries=tries+1)

def delayResponse(tries=0):
	try:
		x = driver.find_element_by_tag_name('table').get_attribute('outerHTML')
		if x:
			return x
		else:
			sleep(0.5)
			print("delayResponse")
			delayResponse(tries=tries+1)
	except Exception:
		if(tries > 100):
			raise Exception("Wifi is Terrible!")
		sleep(0.5)
		print("delayResponse")
		delayResponse(tries=tries+1)

if __name__ == "__main__":
	pass