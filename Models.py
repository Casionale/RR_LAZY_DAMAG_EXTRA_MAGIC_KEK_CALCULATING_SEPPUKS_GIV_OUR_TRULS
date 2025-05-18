from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Создаем базу данных
Base = declarative_base()


class Account(Base):
    __tablename__ = 'account'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    tg = Column(String)
    url = Column(String)

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


# Настройка подключения к базе данных
#DATABASE_URL = "sqlite:///records.db"
conn_string = ""
with open("msql_connection_string.txt", "r", encoding="utf-8") as f:
    conn_string = f.read()

DATABASE_URL = conn_string
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

    def add_order(self, account_id, name, date, price):
        new_order = Order(account_id=account_id, name=name, date=date, price=price)
        self.session.add(new_order)
        self.session.commit()

    def add_account_inorder(self, account_id, order_id, damage):
        new_accountinorder = AccountInOrder(account_id=account_id, order_id=order_id)
        self.session.add(new_accountinorder)
        self.session.commit()
