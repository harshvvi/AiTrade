import json
import random
from apps.authentication.models import Users
from apps.home.models import Transaction
from apps.home.models import Trade
from jinja2 import TemplateNotFound
from datetime import date
from flask import Flask,render_template, request, session, redirect, url_for,flash
from apps import db
import numpy as np
import json
import requests


stock_prediction_url = 'http://localhost:8000'


def predicted_profit(username):
    user = Users.query.filter_by(username=username).first()
    trades = Trade.query.all()
    
    total_invested = 0
    predicted_valuation = 0
    for trade in trades:
        if trade.user_id == user.id:
            total_invested += trade.amount
            company_name = []
            buy_price = []
            quantity_bought = []
            
            tran_ids = [int(x.strip()) for x in trade.tran_id.split(' ')]
            
            for tran_id in tran_ids:
                tran = Transaction.query.filter_by(tran_id = tran_id).first()
                company_name.append(tran.Stock_name)
                buy_price.append(tran.Price)
                quantity_bought.append(tran.quantity)

            for i in range(len(company_name)):
                url = stock_prediction_url + f"/get_company_prediction?company_name={company_name[i]}&&fdays=10&&pdays=0"
                try:
                    data = {}
                    res = requests.get(url=url)
                    if res.status_code == 200:
                        data = res.json()
                except TemplateNotFound:
                    return render_template('home/page-404.html'), 404

                except Exception as e:
                    print("here ", e)
                    return render_template('home/page-500.html'), 500
                
                future = []
                for company, record in data.items():
                    future = record["future"]

                predicted_price = future[-1]
                predicted_valuation += predicted_price * quantity_bought[i]

            
    return predicted_valuation-total_invested



def make_trade(username, amount, duration, stock_cap="Nifty50"):

    cap = ""
    if stock_cap == "Nifty50":
        cap = "NIFTY_50"
    elif stock_cap == "Small Cap":
        cap = "small_cap"
    else:
        cap = "mid_cap"

    url = stock_prediction_url + f"/get_{cap}_sigmoid"
    try:
        invest = {}
        res = requests.get(url=url)
        if res.status_code == 200:
            invest = res.json()



        user = Users.query.filter_by(username=username).first()

        
        amount = float(amount)
        duration = int(duration)
        
        if user.current_balance < amount :
            """
                Display a "Insufficient Balance" message to user
            """
            pass
        else:
            user.current_balance -= amount

        portions = [amount * factor for factor in invest['prob']]
        quantities = [portion/float(cur_price) for cur_price, portion in zip(invest['cur_price'], portions)]
        i = 0
        print("port", portions)
        print("QUAN", quantities)
        print("CURPR", invest['cur_price'])
        print("PROB", invest['prob'])
        print("portion", np.sum(portions))
        print(amount)
        
        transaction_id = []
        for company in invest['comp']:
            transaction = Transaction(uid = user.id, date_time = date.today(), Stock_name = company, buySell = 1, buyprice=invest['cur_price'][i], Price=portions[i], quantity = quantities[i])
            db.session.add(transaction)
            db.session.flush()
            transaction_id.append(transaction.tran_id)
            i += 1

        print(transaction_id)
        tran_string = " ".join([str(x) for x in transaction_id])
        trade = Trade(user_id = user.id, tran_id = tran_string, category = stock_cap, duration = duration, amount = amount)
        
        db.session.add(trade)
        db.session.commit()

    except TemplateNotFound:
        return render_template('home/page-404.html'), 404

    except Exception as e:
        print("here ", e)
        return render_template('home/page-500.html'), 500


def reevaluation(app):
    app_context = app.app_context()
    app_context.push()


    ############# Calling end point at server to predict data for next 10 days and store ###########
    url = stock_prediction_url + '/store_predictions'
    requests.get(url = url)


    ############# Code for calling finetuning function to fine tune model everyday ###########

    url = stock_prediction_url + '/finetune'
    requests.get(url=url)

    ############# Code for reevaluation of every trade in the trade table ####################

    trades = Trade.query.all()

    for trade in trades:
        trade.duration -= 1

        user = Users.query.filter_by(id = trade.user_id).first()
        tran_ids = [int(x.strip()) for x in trade.tran_id.split(' ')]
        company_name = []
        buy_price = []
        quantity_bought = []
        trade_loss_threshold = 15
        company_loss_threshold = 10
        invested_amount = trade.amount

        
        for tran_id in tran_ids:
            tran = Transaction.query.filter_by(tran_id = tran_id).first()
            company_name.append(tran.Stock_name)
            buy_price.append(tran.Price)
            quantity_bought.append(tran.quantity)

        if trade.duration <= 0:
            for tran_id in tran_ids:
                Transaction.query.filter_by(tran_id = tran_id).delete()
            Trade.query.filter_by(trade_id = trade.trade_id).delete()
            user.current_balance += sum([x * y for x, y in zip(curr_price, quantity_bought)])
            db.session.commit()
            app_context.pop()
            continue

        curr_price = []
        for company in company_name:
            url = stock_prediction_url + f"/get_current_data?company_name={company}&&days=1"
            try:
                data = {}
                res = requests.get(url=url)
                if res.status_code == 200:
                    data = res.json()
            except TemplateNotFound:
                return render_template('home/page-404.html'), 404

            except Exception as e:
                print("here ", e)
                return render_template('home/page-500.html'), 500
            
            curr_price.append(int(data["Close"]))

        total_loss = 0

        for i in range(len(buy_price)):
            total_loss += ((buy_price[i]*quantity_bought[i]) - (curr_price[i]*quantity_bought[i]))

    
        tran_to_be_deleted = []
        new_inestment_amount = 0


        if total_loss >= ((trade_loss_threshold * invested_amount)/100):
            for tran_id in tran_ids:
                Transaction.query.filter_by(tran_id = tran_id).delete()
            Trade.query.filter_by(trade_id = trade.trade_id).delete()
            user.current_balance += sum([x * y for x, y in zip(curr_price, quantity_bought)])
            """
                Display to user that his trade has been deleted as
                the loss exceeded beyond threshold
            """
        else:
            for i in range(len(company_name)):
                tran = Transaction.query.filter_by(tran_id = tran_ids[i]).first()
                company_amount_invested = tran.Price * tran.quantity
                if buy_price[i]*quantity_bought[i]-curr_price[i]*quantity_bought[i] >= ((company_loss_threshold * company_amount_invested)/100):
                    tran_to_be_deleted.append(tran.tran_id)
                    new_inestment_amount += curr_price[i]*quantity_bought[i]

            keep_transactions = []
            for tran_id in tran_ids:
                if tran_id not in tran_to_be_deleted:
                    keep_transactions.append(tran_id)

            cap = ""
            if trade.category == "Nifty50":
                cap = "NIFTY_50"
            elif trade.category == "Small Cap":
                cap = "small_cap"
            else:
                cap = "mid_cap"
            url = stock_prediction_url + f"/get_{cap}_sigmoid"
            try:
                invest = {}
                res = requests.get(url=url)
                if res.status_code == 200:
                    invest = res.json()
            except TemplateNotFound:
                return render_template('home/page-404.html'), 404

            except Exception as e:
                print("here ", e)
                return render_template('home/page-500.html'), 500

            company_new_invest = invest["comp"]
            curr_price_new_invest = invest["cur_price"]
            probability = invest["prob"]
            
            sorted_combined_new_invest = sorted(list(zip(company_new_invest, curr_price_new_invest, probability)), key = lambda x: x[2])
            company_new_invest, curr_price_new_invest, probability = zip(* sorted_combined_new_invest)

            company_new_invest = company_new_invest[:len(tran_to_be_deleted)]
            curr_price_new_invest = curr_price_new_invest[:len(tran_to_be_deleted)]



            probability = probability[:len(tran_to_be_deleted)]
            exp_prob = np.exp(probability)
            exp_prob = exp_prob/sum(exp_prob)
            
            probability = exp_prob

            portions = [new_inestment_amount * factor for factor in probability]
            quantities = [cur_price/portion for cur_price, portion in zip(curr_price, portions)]

            for i in range(len(tran_to_be_deleted)):
                transaction = Transaction(uid = user.id, date_time = date.today(), Stock_name = company, buySell = 1, Price=portions[i], quantity = quantities[i])
                db.session.add(transaction)
                db.session.flush()
                keep_transactions.append(transaction.tran_id)

            
            tran_string = " ".join([str(x) for x in keep_transactions])
            trade.tran_id = tran_string
            
            for tran_id in tran_to_be_deleted:
                Transaction.query.filter_by(tran_id = tran_id).delete()

        db.session.commit()
        app_context.pop()



def get_trade_info(user_id):
    trades = Trade.query.filter_by(user_id=user_id).all()

    if (len(trades) == 0):
        return {}
    data = []

    for trade in trades:
        temp = {}
        temp['amount'] = trade.amount
        temp['duration'] = trade.duration

        temp['transactions'] = []
        sett = []
        tran_ids = [int(x.strip()) for x in trade.tran_id.split(' ')]
        total_profit = 0
        for id in tran_ids:
            transaction = Transaction.query.filter_by(tran_id=id).first()

            trans_temp = {}
            company = transaction.Stock_name
            sett +=[company]
            companystr = company.upper().replace('&', '%26')
            res = requests.get(stock_prediction_url + f'/get_current_data?company_name={companystr}&&pdays=2')
            current_price = 0
            if res.status_code == 200:
                response = res.json()
                print(response)
                current_price = float(response[company.upper()][0]['Close'])
            
            trans_temp['current_price'] = current_price
            trans_temp['company'] = company
            trans_temp['buy_price'] = transaction.buyprice
            trans_temp['quantity'] = transaction.quantity
            trans_temp['action'] = transaction.buySell
            trans_temp['invest'] = transaction.Price
            

            
            total_profit += (current_price) * transaction.quantity
            print(current_price, transaction.quantity, (current_price) * transaction.quantity)

            temp['transactions'].append(trans_temp)
        temp['stock_count'] = len(set(sett))
        temp['expected_profit'] = total_profit
       
        data.append(temp)

    return data
            

