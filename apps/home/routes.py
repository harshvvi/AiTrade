# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from apps.home import blueprint
from flask import Flask,render_template, request, session, redirect, url_for,flash
from flask_login import login_required
from jinja2 import TemplateNotFound
from .utils import make_trade, get_trade_info
from .form import AddMoney,WithdrawMoney, TradeForm
from flask_login import current_user
from apps.authentication.models import Users
from apps.home.models import Transaction, Trade
from apps import db
import json
import requests


stock_prediction_url = 'http://localhost:8000'


@blueprint.route('/dashboard')
@login_required
def dashboard():
    transactions = Transaction.query.all()
    stock_investments = {}
    global_investment =0
    for transaction in transactions:
        stock_name = transaction.Stock_name
        price = transaction.Price
        quantity = transaction.quantity
        total_investment = price * quantity
        global_investment += price

        if stock_name in stock_investments:
            stock_investments[stock_name] += total_investment
        else:
            stock_investments[stock_name] = total_investment

    
    sorted_investments = dict(sorted(stock_investments.items(), key=lambda item: item[1], reverse=True))

    top_four = dict(list(sorted_investments.items())[:4])
    remaining = dict(list(sorted_investments.items())[4:])
    past = []
    future = []
    if len(sorted_investments) > 0: 
        top = list(sorted_investments.items())[-1]
        top = top[0]
        top = top.replace('&', '%26')
        url = f'http://localhost:8000/get_compant_prediction?pdays=60&&fdays=8&&company_name={top}'
    
        res = requests.get(url)
        
        if res.status_code == 200:
            jsondata = res.json()
            
            future = jsondata[top]['future']
            for re in jsondata[top]['past']:
                past += [re['Close']]
        
        past = list(reversed(past))
        past = json.dumps(past)
        future = json.dumps(future)       
            
    remaining_total_investment = sum(remaining.values())

    # Create a list for the chart data
    chart_data = [{'label': stock_name, 'data': total_investment} for stock_name, total_investment in top_four.items()]
    chart_data.append({'label': 'Remaining', 'data': remaining_total_investment})

    # Convert chart_data to JSON strings
    labels_json = json.dumps([item['label'] for item in chart_data])
    data_json = json.dumps([item['data'] for item in chart_data])

    trade=Trade.query.all()

    return render_template('home/index.html', transaction=transactions, labels_json=labels_json, data_json=data_json, total_investment=global_investment,trade=trade, past=past, future=future)

@blueprint.route('/stocklist/nifty50')
@login_required
def stocklistn50():
    url = stock_prediction_url + '/get_data_NIFTY_50_prediction?fdays=8&&pdays=60'
    try:
        data = {}
        res = requests.get(url=url)
        if res.status_code == 200:
            data = res.json()
  
        

        tosend = []
        for company, record in data.items():
            temp = {}
            temp['current_price'] = record["past"][0]["Close"]
            temp['company'] = company
            temp['future'] = record['future']
            temp['past'] = list(reversed([x['Close'] for x in record['past'] ]))
            temp['pre_change_past'] = 100 * ((- record["past"][1]["Close"] + record["past"][0]["Close"])/record["past"][1]["Close"])
            temp['pre_change_future'] = 100 * (( - record["past"][0]["Close"] + record["future"][0])/record["past"][0]["Close"])
            tosend.append(temp)
       
        jsondata = json.dumps(tosend)
        return render_template("home/" + "stocklist.html", data=tosend, category="Nifty50", jsondata=jsondata)

    except TemplateNotFound:
        return render_template('home/page-404.html'), 404

    except Exception as e:
        print("here ", e)
        return render_template('home/page-500.html'), 500


@blueprint.route('/stocklist/midCap')
@login_required
def stocklistmc():
    url = stock_prediction_url + '/get_data_midcap_prediction?fdays=10&&pdays=60'
    try:
        data = {}
        res = requests.get(url=url)
        if res.status_code == 200:
            data = res.json()
  
        tosend = []
        for company, record in data.items():
            temp = {}
            temp['current_price'] = record["past"][-1]["Close"]
            temp['company'] = company
            temp['future'] = record['future']
            temp['past'] = [x['Close'] for x in record['past'] ]
            temp['pre_change_past'] = 100 * ((record["past"][-1]["Close"] - record["past"][-2]["Close"])/record["past"][-1]["Close"])
            temp['pre_change_future'] = 100 * ((record["future"][0] - record["past"][-1]["Close"])/record["future"][0])
            tosend.append(temp)
        jsondata = json.dumps(tosend)
        return render_template("home/" + "stocklist.html", data=tosend, category="Mid Cap", jsondata=jsondata)

    except TemplateNotFound:
        return render_template('home/page-404.html'), 404

    except Exception as e:
        print("here ", e)
        return render_template('home/page-500.html'), 500



@blueprint.route('/stocklist/smallCap')
@login_required
def stocklistsc():
    url = stock_prediction_url + '/get_data_smallcap_prediction?fdays=10&&pdays=60'
    try:
        data = {}
        res = requests.get(url=url)
        if res.status_code == 200:
            data = res.json()
  
        

        tosend = []
        for company, record in data.items():
            temp = {}
            temp['current_price'] = record["past"][-1]["Close"]
            temp['company'] = company
            temp['future'] = record['future']
            temp['past'] = [x['Close'] for x in record['past'] ]
            temp['pre_change_past'] = 100 * ((record["past"][-1]["Close"] - record["past"][-2]["Close"])/record["past"][-1]["Close"])
            temp['pre_change_future'] = 100 * ((record["future"][0] - record["past"][-1]["Close"])/record["future"][0])
            tosend.append(temp)
        jsondata = json.dumps(tosend)
        return render_template("home/" + "stocklist.html", data=tosend, category="Small Cap", jsondata=jsondata)

    except TemplateNotFound:
        return render_template('home/page-404.html'), 404

    except Exception as e:
        print("here ", e)
        return render_template('home/page-500.html'), 500

@blueprint.route('/wallet', methods=['POST','GET'])
@login_required
def wallet():
    add_money = AddMoney(request.form)
    withdraw_money = WithdrawMoney(request.form)

    if 'moneytoadd' in request.form:
        money = request.form["moneytoadd"]
        user_id = session["user_id"]
        username = session["user_name"]
        user = Users.query.filter_by(id=user_id).first()
        user.current_balance+= int(money)
        db.session.commit()

    if 'withdraw' in request.form:
        money = request.form["moneytowithdraw"]
        user_id = session["user_id"]
        username = session["user_name"]
        user = Users.query.filter_by(id=user_id).first()
        if user.current_balance >= int(money):
            user.current_balance -= int(money)
            db.session.commit()
        else:
            flash("Insufficient balance for withdrawal.", "error")


    transaction = Transaction.query.all()
    return render_template("home/wallet.html",add_form=add_money, withdraw_form=withdraw_money,transaction=transaction)


@blueprint.route('/aitrade')
@login_required
def aitrade():

    user_id = session['user_id']
    data = get_trade_info(user_id=user_id)
    return render_template("home/aitrade.html", data=data)

@blueprint.route('/create_trade', methods=['POST', 'GET'])
@login_required
def create_trade():
    form = TradeForm(request.form)

    if 'category' in request.form:
        category = request.form["category"]
        amount = request.form['tradelimit']
        duration = request.form['duration']
        uname = session['user_name']

        # print(f"category = {category}, amount = {amount}, duration = {duration}, uid = {uname}")
        make_trade(uname, amount, duration, stock_cap=category)
        
        return redirect( url_for('home_blueprint.dashboard'))
        
        
    return render_template("home/tradeform.html", form=form)






@blueprint.route('/<template>')
@login_required
def route_template(template):

    try:

        if not template.endswith('.html'):
            template += '.html'

        # Detect the current page
        segment = get_segment(request)

        # Serve the file (if exists) from app/templates/home/FILE.html
        return render_template("home/" + template)

    except TemplateNotFound:
        return render_template('home/page-404.html'), 404

    except:
        return render_template('home/page-500.html'), 500



# Helper - Extract current page name from request
def get_segment(request):

    try:

        segment = request.path.split('/')[-1]

        if segment == '':
            segment = 'index'

        return segment

    except:
        return None
