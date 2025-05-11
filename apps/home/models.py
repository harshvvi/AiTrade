from apps import db

class Transaction(db.Model):
    __tablename__ = 'Transaction'

    uid=db.Column(db.Integer,db.ForeignKey('Users.id'),nullable=False)
    tran_id = db.Column(db.Integer,  primary_key=True)
    date_time = db.Column(db.DateTime, nullable=False)
    Stock_name = db.Column(db.String(64),nullable=False)
    buySell = db.Column(db.Integer,nullable=False)
    buyprice = db.Column(db.Integer,nullable=False)
    Price = db.Column(db.Integer,nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    Trade=db.relationship('Trade',backref='transaction')

    def __repr__(self):
        str(self.tran_id)

class Trade(db.Model):
    __tablename__='Trade'

    user_id=db.Column(db.Integer,db.ForeignKey('Users.id'),nullable=False)
    trade_id = db.Column(db.Integer,nullable=False, primary_key=True)
    tran_id = db.Column(db.Text, db.ForeignKey('Transaction.tran_id'), nullable=False)
    category=db.Column(db.String(20), nullable=False)
    duration=db.Column(db.Integer,nullable=False)
    amount=db.Column(db.Integer,nullable=False)