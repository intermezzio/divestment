import numpy as np
import pandas as pd

from flask import Flask, flash, redirect, render_template, request, session, abort, url_for, Response, send_file
app = Flask(__name__)
app.config.from_object(__name__)
app.config['SECRET_KEY'] = '1243bed87ac87eb87a87ed'

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
	spreadsheetData = pd.DataFrame(columns=["Month", "Salary", "401k"])

	monthly_salary = salary / 12
	
	# 401k
	