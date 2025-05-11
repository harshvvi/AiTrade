from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, IntegerField
from wtforms.validators import DataRequired, Length, Email, EqualTo,ValidationError

class AddMoney(FlaskForm):
    moneytoadd = StringField('MoneytoAdd',
                         id='moneytoadd',
                         validators=[DataRequired()])

class WithdrawMoney(FlaskForm):
    moneytowithdraw = StringField('MoneytoWithdraw', id='moneytowith', validators=[DataRequired()])


class TradeForm(FlaskForm):
    choices = ['Nifty50', 'Mid Cap', 'Small Cap']
    category = SelectField('Category', id='category', choices=choices, validators=[DataRequired()])
    tradelimit = StringField('Amount to Invest', id='tradelimit', validators=[DataRequired()])
    # stockpricelimit = StringField('StockPriceLimit', id='stockpricelimit', validators=[DataRequired()])
    duration = StringField('Duration', id="duration", validators=[DataRequired()])
    moneytowithdraw = StringField('MoneytoWithdraw', id='moneytowithdraw', validators=[DataRequired()])

