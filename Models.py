from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from db_config import get_database_url

# Создаем базу данных
Base = declarative_base()


class Account(Base):
    __tablename__ = 'account'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    tg = Column(String)
    url = Column(String)
    payable = Column(Boolean, nullable=False, default=False)
    avatar = Column(Boolean, nullable=False, default=0)

class Order(Base):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    date = Column(String)
    price = Column(Float)
    limit = Column(String, nullable=True)

class AccountInOrder(Base):
    __tablename__ = 'account_inorder'
    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey('account.id'))
    order_id = Column(Integer, ForeignKey('orders.id'))
    damage = Column(Float)

class Payment(Base):
    __tablename__ = 'payment'
    id = Column(Integer, primary_key=True)
    account_inorder_id = Column(Integer, ForeignKey('account_inorder.id'))
    cash = Column(Integer)
    limiter = Column(Boolean)


DATABASE_URL = get_database_url()
engine = create_engine(DATABASE_URL)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

class Database:
    session = Session()

    def __init__(self):
        self.session = Session()

    def add_account(self, name):
        new_account = Account(name=name)
        self.session.add(new_account)
        self.session.commit()

    def add_order(self, name, date, price, limit=None):
        new_order = Order(name=name, date=date, price=price, limit=limit)
        self.session.add(new_order)
        self.session.commit()

    def add_account_inorder(self, account_id, order_id, damage):
        new_accountinorder = AccountInOrder(account_id=account_id, order_id=order_id, damage=damage)
        self.session.add(new_accountinorder)
        self.session.commit()
