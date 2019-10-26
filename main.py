import numpy as np
import pandas as pd
import requests
from timeit import timeit
from time import sleep

from contextlib import closing
from bs4 import BeautifulSoup

from flask import Flask, flash, redirect, render_template, request, session, abort, url_for, Response, send_file
app = Flask(__name__)
app.config.from_object(__name__)
app.config['SECRET_KEY'] = '1243bed87ac87eb87a87ed'

from requests_html import HTMLSession
session = HTMLSession()

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
		"Authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJBUElfS0VZX01BTkFHRVIiLCJodHRwOi8vdGF4ZWUuaW8vdXNlcl9pZCI6IjVkYjQ4M2Y4MjdlMzNmM2M2ZjViNzEwNSIsImh0dHA6Ly90YXhlZS5pby9zY29wZXMiOlsiYXBpIl0sImlhdCI6MTU3MjExMTM1Mn0.8wdZGHypbECS025jwPr0Xy4YrsNg-n1o6TEBuZvwdKM",
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

def searchStocks():
	"""
	returns a list of tickers
	"""
	global session

	# https://fossilfreefunds.org/funds?dsc=false&srt=usd_relative_footprint&typ=FO
	url = "https://fossilfreefunds.org/funds?dsc=false&srt=usd_relative_footprint&typ=FO"
	response = session.get(url, verify=False)
	response_rendered = response.html.render()
	response_html = BeautifulSoup(response, 'html.parser')
	
	# response_html.find('table')
	# stock_table = response_html.select('table')
	return response_html
	# return response