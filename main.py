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
from xml.etree import ElementTree
from multiprocessing import Process
from sympy import solveset, Eq, symbols

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


def make_spreadsheet(salary, status="single", state="CT", savings=0, age=20, perc401k=10, match401k=True, year=2019, fica=True):
	"""
	Spreadsheet Data Calculations

	"""
	
	# 401k
	save401k = salary * perc401k / 100
	company401k = save401k if match401k else 0
	total401k = save401k + company401k

	# Taxes
	fed_tax, st_tax, fica_tax = getAllIncomeTax(income=salary-save401k, status=status, state=state, year=year, fica=fica)

	usable_annual_salary = salary - save401k - fed_tax - st_tax - fica_tax

	# Expenses
	housing_cost = round(usable_annual_salary * 0.25, 2)
	tithe_or_charity_cost = round(usable_annual_salary * 0.1, 2)
	food_cost = 3600
	clothing_cost = 1200
	car_cost = 4200
	digital_cost = 1800
	misc_cost = 3000

	# salary to make money with
	afterstatic_annual_salary = usable_annual_salary - housing_cost - tithe_or_charity_cost - food_cost - clothing_cost - car_cost - digital_cost - misc_cost
	print("afterstatic_annual_salary:",afterstatic_annual_salary)
	
	optimal_savings_left = max(usable_annual_salary / 2 - savings,0) # 6 months of salary in savings

	years_to_40 = 40-age

	savings_interest_rate = .001

	save401k_interest_rate = .05

	invest_interest_rate = .08

	# annuity (initial, flow, interest, years)
	# solve for maximized discretionary spending
	ivst = symbols('ivst')
	investment_money = solveset(Eq(annuity(savings, 0, savings_interest_rate, years_to_40) + annuity(0, ivst, invest_interest_rate, years_to_40) + annuity(0, total401k, save401k_interest_rate, years_to_40),1e6), ivst)
	
	investment_money = tuple(investment_money)[0] # convert data types
	investment_money = round(investment_money,2) + 0.01
	print("investment_money:", investment_money)
	if investment_money > afterstatic_annual_salary:
		return False

	discretionary_expenses = investment_money - afterstatic_annual_salary

	budget = {
		"salary": salary,
		"save401k": save401k,
		"company401k": company401k,
		"total401k": total401k,

		"fed_tax": fed_tax,
		"st_tax": st_tax,
		"fica_tax": fica_tax,
		"tax": fed_tax + st_tax + fica_tax,

		"usable_annual_salary": usable_annual_salary,
		"tithe_or_charity_cost": tithe_or_charity_cost,
		"housing_cost": housing_cost,
		"food_cost": food_cost,
		"clothing_cost": clothing_cost,
		"car_cost": car_cost,
		"digital_cost": digital_cost,
		"misc_cost": misc_cost,

		"afterstatic_annual_salary": afterstatic_annual_salary,
		"investment_money": investment_money,
		"discretionary_expenses": discretionary_expenses
	}

	spreadsheetData = pd.DataFrame(columns=["Year", "Age", "401k", "Savings", "Investments"])
	spreadsheetData.loc[0] = [year, age, 0, savings, 0]
	for i in range(age,40):
		curr_year, curr_age, curr_401k, curr_savings, curr_investments = spreadsheetData.loc[spreadsheetData.shape[0]-1]
		curr_year += 1
		curr_age += 1
		curr_401k = annuity(curr_401k, total401k, save401k_interest_rate)
		curr_savings = annuity(curr_savings, 0, savings_interest_rate)
		curr_investments = annuity(curr_investments, investment_money, invest_interest_rate)
		spreadsheetData.loc[spreadsheetData.shape[0]] = [curr_year, curr_age, curr_401k, curr_savings, curr_investments]

	return budget, spreadsheetData


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
	print("Taxes:", fed_tax, st_tax, fica_tax)
	return fed_tax, st_tax, (fica_tax if fica else 0)

def searchStocks(fundType = None, diversified = False, sustainable = False, NUM_STOCKS = 4):
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

	sleep(1)
	htmltable = delayResponse()

	stocksDF = pd.read_html(htmltable)[0]
	print(stocksDF.shape[0], "funds")
	print(stocksDF.columns, "columns")
	stocksDF.drop(["Fossil fuels", "Clean200", "Sustainability mandate", "Net assets", "Group"], axis=1, inplace=True)

	fundNames = list()

	shortenedStocksDF = pd.DataFrame(columns=stocksDF.columns)

	for i in range(stocksDF.shape[0]):
		if len(fundNames) == NUM_STOCKS:
			break
		fname = stocksDF.loc[i,"Fund name"].split(" ")[0]
		if fname in fundNames:
			continue
		else:
			fundNames.append(fname)
			shortenedStocksDF.loc[shortenedStocksDF.shape[0]] = stocksDF.loc[i]

	# response_rendered = response.html.render()
	# response_html = BeautifulSoup(response, 'html.parser')
	
	# response_html.find('table')
	# stock_table = response_html.select('table')

	tickerFromName = np.vectorize(lambda name: name[name.index("Ticker: ")+8:])
	removeTicker = np.vectorize(lambda name: name[:name.index("Ticker: ")])
	tickerURL = np.vectorize(lambda ticker: f"https://www.marketwatch.com/investing/stock/{ticker}")

	

	shortenedStocksDF["Ticker"] = tickerFromName(shortenedStocksDF["Fund name"])
	shortenedStocksDF["Fund"] = removeTicker(shortenedStocksDF["Fund name"])
	shortenedStocksDF["URL"] = tickerURL(shortenedStocksDF["Ticker"])

	shortenedStocksDF.drop("Fund name", axis=1, inplace=True)

	return shortenedStocksDF


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

def annuity(initial, flow, interest, years=1):
	return flow * ((1+interest) ** years - 1) / interest + initial * (1+interest) ** years

if __name__ == "__main__":
	pass


# def priceFromTickers(ticker):
# 	"""
# 	get a price for a ticker

# 	"""
# 	# api_key = open("keys/iexcloud.txt", 'r').read().strip()
# 	# stockJSON = requests.get(f"https://sandbox.iexapis.com/stable/stock/AAAU/quote?token={api_key}").json()
# 	# # http://dev.markitondemand.com/MODApis/Api/v2/Quote?symbol=MSFT
# 	# tickerprice = stockJSON["latestPrice"]
# 	# # csv_data = requests.get()
# 	response = requests.get(f"http://dev.markitondemand.com/MODApis/Api/v2/Quote?symbol={ticker}")
# 	stockXML = ElementTree.fromstring(response.content)
# 	tickerprice = float(stockXML.find("LastPrice").text)
# 	return tickerprice

# pTickers = np.vectorize(priceFromTickers)


# def testPriceFromTickers(tickers):
# 	"""
# 	get a price for a ticker

# 	"""
# 	api_key = open("keys/worldtradingdata.txt", 'r').read().strip()
# 	stocks = ",".join(tickers)
# 	response = requests.get(f"https://api.worldtradingdata.com/api/v1/mutualfund?symbol={tickers}&api_token={api_key}").json()
# 	return response
# 	# prices = list()
# 	# for stock in response["data"]:
# 	# 	prices.append(stock["price"])

# 	# return prices
