from Models import Database, AccountInOrder, Account, Order


class StatUtils:
    @staticmethod
    def order_participants(list_orders):
        accounts_count = {}
        session = Database.session
        for order in list_orders:
            list_accounts = session.query(AccountInOrder).filter_by(order_id=order.id).all()
            for a in list_accounts:
                if a.account_id not in accounts_count:
                    accounts_count[a.account_id] = 1
                else:
                    accounts_count[a.account_id] += 1
        ret = StatUtils.print_order_partocopants(accounts_count)
        if ret == 0:
            return 0
        else:
            return 1

    @staticmethod
    def print_order_partocopants(accounts_count):
        csv_data = 'Имя;tg;Заказов;\n'
        txt_data = ''
        for a in accounts_count:
            account = Database.session.query(Account).filter_by(id=a).first()
            count = accounts_count[a]
            csv_data += f'{account.name};{account.tg};{count}\n'
            txt_data += f'{account.tg} = {count}\n'

        with open('Статистика участия.csv', 'w', encoding='utf-8') as f:
            f.write(csv_data)
        with open('Статистика участия.txt', 'w', encoding='utf-8') as f:
            f.write(txt_data)

        return 0

    @staticmethod
    def get_account_by_url(url_end):
        try:
            session = Database.session
            account = session.query(Account).filter(Account.url.like(f"%{url_end}")).first()
            return account
        except:
            return None

    @staticmethod
    def set_avatar_account_by_id(account_id, value):
        try:
            session = Database.session
            account = session.query(Account).filter(Account.id == account_id).first()
            account.avatar = value
            session.flush()
            session.commit()
        except:
            return None