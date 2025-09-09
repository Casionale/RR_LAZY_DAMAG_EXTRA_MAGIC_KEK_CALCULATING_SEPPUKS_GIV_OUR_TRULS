from sqlalchemy import (
    Column, Integer, String, BigInteger, ForeignKey,
    DECIMAL, Text, Boolean, TIMESTAMP
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class BotRole(Base):
    __tablename__ = "BOT_ROLE"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(45), nullable=False)

    users = relationship("NsUser", back_populates="bot_role")


class NsRole(Base):
    __tablename__ = "NS_ROLE"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(45), nullable=False)

    users = relationship("NsUser", back_populates="ns_role")


class NsAccount(Base):
    __tablename__ = "NS_ACCOUNT"

    id = Column(Integer, primary_key=True, autoincrement=True)
    url = Column(String(200), nullable=False)
    name = Column(String(45), nullable=False)
    payment_select = Column(Integer, nullable=False)  # tinyint → Integer

    in_orders = relationship("NsAccountInOrder", back_populates="account")
    payments = relationship("NsPayment", back_populates="account")
    users = relationship("NsUserAccount", back_populates="account")


class NsOrder(Base):
    __tablename__ = "NS_ORDER"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(20), nullable=False)
    url = Column(String(20), nullable=False)
    start_date = Column(TIMESTAMP, nullable=False)
    price = Column(DECIMAL(8, 2), nullable=False)
    limit = Column(BigInteger, nullable=False)
    is_end = Column(Boolean, nullable=False)
    is_attack = Column(Boolean, nullable=False)
    msg = Column(String(200), nullable=True)
    end_date = Column(TIMESTAMP, nullable=True)

    in_accounts = relationship("NsAccountInOrder", back_populates="order")
    payments = relationship("NsPayment", back_populates="order")


class NsAccountInOrder(Base):
    __tablename__ = "NS_ACCOUNT_IN_ORDER"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ns_account_id = Column("NS_ACCOUNT", Integer,
                           ForeignKey("NS_ACCOUNT.id", ondelete="CASCADE", onupdate="CASCADE"),
                           nullable=False)
    ns_order_id = Column("NS_ORDER", Integer,
                         ForeignKey("NS_ORDER.id", ondelete="CASCADE", onupdate="CASCADE"),
                         nullable=False)

    account = relationship("NsAccount", back_populates="in_orders")
    order = relationship("NsOrder", back_populates="in_accounts")


class NsPayment(Base):
    __tablename__ = "NS_PAYMENT"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ns_account_id = Column("NS_ACCOUNT", Integer,
                           ForeignKey("NS_ACCOUNT.id", ondelete="CASCADE", onupdate="CASCADE"),
                           nullable=False)
    ns_order_id = Column("NS_ORDER", Integer,
                         ForeignKey("NS_ORDER.id", ondelete="CASCADE", onupdate="CASCADE"),
                         nullable=False)
    cash = Column(DECIMAL(18, 2), nullable=False)
    limiter = Column(Integer, nullable=False)  # tinyint → Integer

    account = relationship("NsAccount", back_populates="payments")
    order = relationship("NsOrder", back_populates="payments")


class NsUser(Base):
    __tablename__ = "NS_USER"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tg = Column(BigInteger, unique=True, nullable=False)
    is_active = Column(Boolean, nullable=False)
    ns_role_id = Column("NS_ROLE_ID", Integer,
                        ForeignKey("NS_ROLE.id", ondelete="CASCADE", onupdate="CASCADE"),
                        nullable=False)
    bot_role_id = Column("BOT_ROLE_ID", Integer,
                         ForeignKey("BOT_ROLE.id", ondelete="CASCADE", onupdate="CASCADE"),
                         nullable=False)
    approved = Column(Boolean, nullable=False)
    tg_name = Column(String(45), nullable=False)

    ns_role = relationship("NsRole", back_populates="users")
    bot_role = relationship("BotRole", back_populates="users")
    accounts = relationship("NsUserAccount", back_populates="user")


class NsUserAccount(Base):
    __tablename__ = "NS_USER_ACCOUNT"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ns_user_id = Column("NS_USER_ID", Integer,
                        ForeignKey("NS_USER.id", ondelete="CASCADE", onupdate="CASCADE"),
                        nullable=False)
    ns_account_id = Column("NS_ACCOUNT_ID", Integer,
                           ForeignKey("NS_ACCOUNT.id", ondelete="CASCADE", onupdate="CASCADE"),
                           nullable=False)

    user = relationship("NsUser", back_populates="accounts")
    account = relationship("NsAccount", back_populates="users")
