import json
import sqlite3
import threading
import time
from asyncio import timeout
from datetime import datetime
from idlelib.iomenu import encoding

import cloudscraper
from bs4 import BeautifulSoup
import datetime

import re

from mozDecompress import mozlz4_to_text

# Куки сессии
cookies = {}

url_main = 'https://rivalregions.com/#overview'
client = ''

class Bot:

    def __init__(self, cookies, client):
        self.cookies = cookies
        self.client = client

    def get_data_main(self, url):
        scraper = cloudscraper.create_scraper(browser='firefox')
        response = scraper.get('https://rivalregions.com/#overview', cookies=self.cookies)

        if 'Sign in with Google' in response.text:
            return 'Сессия устарела!'
        if response.text == '':
            return 'Пустой ответ'

        soup = BeautifulSoup(response.text, 'html.parser')

        data_main = {
            "energy": soup.find(id="s").text.strip(),  # Энергия
            "stamina_increase": soup.find(id="header_stamina").text.strip(),
            "experience_points": soup.find(id="exp_points").text.strip(),
            "level": soup.find(id="exp_level").text.strip(),
            "money": soup.find(id="m").text.strip(),
            "gold": soup.find(id="g").text.strip()
        }

        try:
            time_string = str(soup.find_all('div', {'class': 'tip header_slide float_left hov pointer'})[0])
            time_string = re.search(r"\d\d:\d\d", time_string)
            time_string = time_string.group(0)
        except:
            time_string = 'Полная энергия'
        #print(time_string)

        response = scraper.get(f'https://rivalregions.com/main/get_hp?c={self.cookies['rr']}', cookies=self.cookies)

        data_energy = json.loads(response.text)

        data_main['energy'] = data_energy['hp']

        data_main = {
            'energy': data_energy['hp'],
            'stamina_refill_en': time_string,
            'stamina_refill': datetime.datetime.fromtimestamp(int(data_energy['refill'])),
            'stamina_next_time': data_energy['next_time'],
            'experience_points': data_main['experience_points'],
            'level': data_main['level'],
            'money': data_main['money'],
            'gold': data_main['gold']
        }

        return data_main

    def keep_session_alive(self):
        scraper = cloudscraper.create_scraper()
        while True:
            try:
                # Отправляем GET запрос на главную страницу
                response = scraper.get('https://rivalregions.com/#overview', cookies=self.cookies)
                if response.status_code == 200:
                    if 'Sign in with Google' not in response.text and response.text != '':
                        print('Сессия обновлена успешно')
                    else:
                        print("Сессия обновлена, но не очень хороший ответ")
                else:
                    print(f"Не удалось обновить сессию, статус-код: {response.status_code}")
            except Exception as e:
                if 'Sign in with Google' in response.text:
                    print('Сессия устарела!')
                else:
                    print(f"Ошибка при обновлении сессии: {e}")

            # Ждем 10 секунд перед следующим запросом
            time.sleep(10)

    def alive(self):
        session_thread = threading.Thread(target=self.keep_session_alive)
        session_thread.daemon = True  # Поток завершится, когда завершится основная программа
        session_thread.start()
        print('Поток alive запущен')

    def get_list_damage_from_war(self, id, is_attack):
        url = f"https://rivalregions.com/war/damage/{id}/{0 if is_attack == True else 1}?c={self.client}"
        damages = self.get_damage_members(url)
        return damages

    def get_damage_members(self, url):

        is_error = True
        while is_error:
            scraper = cloudscraper.create_scraper(browser='firefox')
            response = scraper.get(url, cookies=self.cookies, timeout=100)

            strip_response = response.text.replace('\n', '')
            if response.text == '':
                raise Exception
            # print(response.text)
            # print(strip_response)
            gmg = [x.group() for x in re.finditer(pattern=r'<tr(.|\n)*?</tr>', string=strip_response)]
            damages = []

            if len(gmg) > 0:
                is_error = False
            else:
                print('Попытка с пустым уроном, правильный ли ID битвы?')

        for g in gmg:
            if 'user' in g:
                # damages.append(g)


                soup = BeautifulSoup(g, 'html.parser')
                try:
                    dbg = soup.find_all('span', {'class': 'yellow'})
                    if len(dbg) > 0:
                        lvl = soup.find_all('span', {'class': 'yellow'})[0].text.strip()
                    else:
                        lvl = soup.find_all('td', {'class': 'yellow list_level'})[0].text.strip()
                    individual_damage = {
                        "name": soup.find_all('td', {'class': 'list_name pointer'})[0].text.strip(),
                        "lvl": lvl,
                        #"lvl": soup.find_all('span', {'class': 'yellow'})[0].text.strip(),
                        #"lvl": soup.find_all('td', {'class': 'yellow list_level'})[0].text.strip(),
                        "damage": soup.find_all('span', {'class': 'yellow'})[1].text.strip().replace('.', ''),
                        'id': soup.find('tr').attrs['user']
                    }
                except Exception as e:
                    f = open('3.txt', 'w', encoding='utf-8')
                    f.write(g)
                    f.close()

                damages.append(individual_damage)
        return damages

    def get_list_damage_from_war_partys(self, id):
        url = f'https://rivalregions.com/listed/partydamage/{id}?c={self.client}'
        scraper = cloudscraper.create_scraper()
        response = scraper.get(url, cookies=self.cookies)
        strip_response = response.text.replace('\n','')
        print(strip_response)

        prtys = [x.group() for x in re.finditer(pattern=r'<tr(.|\n)*?</tr>', string=strip_response)]
        partys = []

        for p in prtys:
            if 'user' in p:
                soup = BeautifulSoup(p, 'html.parser')
                party = {
                    'id':soup.find('tr').get('user'),
                    'name':soup.find_all('td',{'class':'list_name pointer'})[0].next,
                    'side':soup.find_all('td',{'class':'list_name pointer'})[0].text.replace(
                    soup.find_all('td',{'class':'list_name pointer'})[0].next, ''),
                    'damage':soup.find_all('td')[2].text.strip().replace('.',''),
                    'persent':soup.find_all('td')[3].text.strip(),
                }
                partys.append(party)

        return partys

    def get_list_damage_from_war_party_members(self, id, is_attack, id_party):
        is_error = True
        while is_error:
            url = f'https://rivalregions.com/war/damageparties/{id}/{0 if is_attack == True else 1}/{id_party}?c={self.client}'
            damages = self.get_damage_members(url)
            if type(damages) is not list or len(damages) == 0:
                is_error = True
                print('Пустой дамаг :с')
            else:
                is_error = False
        return damages

    def get_damage(self, url):
        is_error = True
        while is_error:
            scraper = cloudscraper.create_scraper()
            response = scraper.get(url, cookies=self.cookies, timeout=40)

            if '''<script>
$(document).ready(function() {
	window.location="https://rivalregions.com";
	});
</script>''' != response.text:
                is_error = False

            if response.text == '':
                return None


        f = open('1.txt', 'w', encoding='utf-8')
        f.write(response.text.replace('\n',''))
        f.close()

        dmg = [x.group() for x in re.finditer(pattern=r'<tr(.|\n)*?</tr>', string=response.text.replace('\n',''))]

        damage = []

        for d in dmg:
            if 'tr height' in d or '<th class="thc"><span class="pointer chat_link">Дата</span></th>' in d:
                continue

            f = open('2.txt', 'w', encoding='utf-8')
            f.write(d)
            f.close()

            soup = BeautifulSoup(d, 'html.parser')

            try:
                id_war_html = [x.group() for x in re.finditer(pattern=r'war/details(.*?)"', string=d)][0]

                damage1 = soup.find_all('span', {'class': 'pointer tip'})
                damage2 = soup.find_all('span', {'class': 'dot showbuf pointer tip'})
                damage3 = soup.find_all('td', {'class': 'yellow white list_level imp'})
                damage4 = soup.find_all('td', {'class': 'list_level imp'})
                damage5 = soup.find_all('td', {'class': 'list_level imp green'})
                damage6 = soup.find_all('td', {'class': 'yellow white list_level imp green'})

                if len(damage1) != 0:
                    damage_calc = soup.find_all('span', {'class': 'pointer tip'})[0].text.strip().replace('.', '')
                elif len(damage2) != 0:
                    damage_calc = soup.find_all('span', {'class': 'dot showbuf pointer tip'})[0].text.strip().replace('.', '')
                elif len(damage3) != 0:
                    damage_calc = soup.find_all('td', {'class': 'yellow white list_level imp'})[-1].attrs['rat']
                elif len(damage4) != 0:
                    damage_calc = soup.find_all('td', {'class': 'ylist_level imp'})[-1].attrs['rat']
                elif len(damage5) != 0:
                    damage_calc = soup.find_all('td', {'class': 'list_level imp green'})[-1].attrs['rat']
                elif len(damage6) != 0:
                    damage_calc = soup.find_all('td', {'class': 'yellow white list_level imp green'})[-1].attrs['rat']
                else:
                    pass


                damage.append({
                    'stamp': int(soup.find_all('td')[-1].attrs['rat']),
                    'time': datetime.datetime.fromtimestamp(int(soup.find_all('td')[-1].attrs['rat'])).strftime('%Y-%m-%d %H:%M:%S'),
                    'damage': damage_calc,
                    'id_war': id_war_html.replace('war/details/','').replace('"',''),
                })

            except Exception as e:
                return []
        return damage



class Utils:

    @staticmethod
    def calculate_truls_for_war(damage, id_war, price, stop_time, name = ''):
        damage = damage[0]
        sum = 0
        sum_damage = 0
        no_pay_sum = 0
        str_check = f'{name:^50}\n'
        stop_time = int(datetime.datetime.strptime(stop_time, "%H:%M %d.%m.%Y").timestamp())
        for dmg in damage:
            if dmg['stamp'] < stop_time:
                if int(dmg['id_war']) == id_war:
                    add_sum = int(dmg['damage']) * price
                    sum += add_sum
                    sum_damage += int(dmg['damage'])
                    str_check += f'{dmg["time"]} {dmg['damage']}  * {price} = {add_sum}\n'

                    if add_sum == 0:
                        pass
            else:
                if int(dmg['id_war']) == id_war:
                    no_pay_sum += int(dmg['damage']) * price

        str_check += f'ИТОГО: {sum} | Не оплачиваемая сумма {no_pay_sum}\n\n'

        return {'sum': sum, 'log': str_check, 'damage':sum_damage}

    @staticmethod
    def sums_per_member_from_wars(bot, ids, is_attacks, prices, id_party):
        members = {}

        for i in range(len(ids)):

            is_error = True
            while is_error:
                try:
                    damage_members = bot.get_list_damage_from_war_party_members(ids[i], is_attacks[i], id_party)
                    is_error = False
                except Exception as e:
                    pass

            for member in damage_members:
                money = int(member['damage']) * prices[i]

                if member['name'] in members:
                    members[member['name']] += money
                else:
                    members[member['name']] = money

        str_ret = ''
        for key, value in members.items():
            str_ret +=f'{key}, {value: }\n'
        return str_ret

    @staticmethod
    def sums_per_member_from_wars_witch_stop_word(bot, ids, is_attacks, prices, id_party, stop_at):
        members = {}
        un_unic_damage = {}
        results = []
        logs = []

        for i in range(len(ids)):
            date_time_obj = datetime.datetime.strptime(stop_at[i], '%H:%M %d.%m.%Y')

            is_error = True
            while is_error:
                try:
                    damage_members = bot.get_list_damage_from_war_party_members(ids[i], is_attacks[i], id_party)
                    is_error = False
                except Exception as e:
                    pass

            un_unic_damage = {}

            for member in damage_members:
                if member['name'] not in un_unic_damage:
                    attacks = []

                    url_damage = f'https://rivalregions.com/slide/damage/{member['id']}'

                    is_more_need = True
                    iters = 0
                    while is_more_need:
                        if iters == 0:
                            part_damage = bot.get_damage(url_damage) # Нада таво етаво по 60
                        else:
                            part_damage = bot.get_damage(f'{url_damage}/{60 * iters}')

                        if part_damage is not None:
                            for d in part_damage:
                                attacks.append(d)
                            iters += 1
                        else:
                            is_more_need = False

                    if member['name'] in un_unic_damage:
                        un_unic_damage[member['name']].extend(attacks)
                    else:
                        un_unic_damage[member['name']] = [attacks]
                print(f'Законечен {member['name']}')

            results.append(f'Война {ids[i]}')

            sum = 0

            csv_file_data = ''

            for member in un_unic_damage:
                result = Utils.calculate_truls_for_war(un_unic_damage[member], ids[i], prices[i], stop_at[i], member)
                #results.append(f'{member["name"]:<30}: {result["sum"]:<15} Rivals')
                m = member
                r = result['sum']
                results.append(f'{m:<40}: {str(r):<15} Rivals')

                logs.append(result['log'])
                sum += result['sum']

                csv_file_data += f'{m};{result['damage']};\n'

            results.append(f'ИТОГО: {sum} Rivals\n')

            f = open(f'Война {ids[i]}.csv', 'w', encoding='utf-8')
            f.write(csv_file_data)
            f.close()
            f.close()

        f = open('Money.txt', 'w', encoding='utf-8')
        for r in results:
            f.write(r + '\n')
        f.close()

        f = open('ResultLogs.txt', 'w', encoding='utf-8')
        for r in logs:
            f.write(r + '\n')
        f.close()

        print('Готово! Рассмотри файлы Money.txt и ResultLogs.txt')

    @staticmethod
    def get_cookies(settings):

        def get_cookie_from_firefox(cookies_file_uri, session_file_uri):
            connection = sqlite3.connect(cookies_file_uri)

            cursor = connection.cursor()
            cursor.execute('''
    	SELECT name, value FROM moz_cookies WHERE (name = ? OR name = ? OR name = ? OR name = ? OR name = ?) AND host = ?
    	''', ('rr', 'rr_add', 'rr_f', 'rr_id', 'PHPSESSID', 'rivalregions.com'))
            results = cursor.fetchall()

            connection.close()

            cookies = {}

            for row in results:
                cookies[row[0]] = row[1]

            session_cookies = mozlz4_to_text(session_file_uri)
            txt = session_cookies.decode('utf-8')
            session_cookies = json.loads(txt)
            session_cookies = session_cookies['cookies']
            cookies['PHPSESSID'] = ''

            for cookie in session_cookies:
                if cookie['host'] == 'rivalregions.com' and cookie['name'] == 'PHPSESSID':
                    cookies['PHPSESSID'] = cookie['value']

            return cookies

        cookies_file_uri = settings['cookies_file_uri']
        session_file_uri = settings['session_file_uri']
        return get_cookie_from_firefox(cookies_file_uri, session_file_uri)

    def get_manual_cookies(settings):

        return  {
            'PHPSESSID': settings['PHPSESSID'],
            'rr': settings['rr'],
            'rr_add': settings['rr_add'],
            'rr_f': settings['rr_f'],
            'rr_id': settings['rr_id'],
        }

    @staticmethod
    def kek_calculating(data, cookies, is_simple=False):
        is_error = True
        while is_error:
            try:
                bot = Bot(cookies=cookies, client=client)
                data_main = bot.get_data_main(url=url_main)
                print(data_main)
                if data_main == 'Сессия устарела!' or 'Пустой ответ':
                    # raise Exception
                    pass
                is_error = False
            except Exception as e:
                print('Новая попытка посчитать')
                f = open('ERROR новая попытка.txt')
                f.write(e)
                f.close()

        is_error = True
        while is_error:
            print('Начинаю смотреть шо там по урону')


            ids = []
            is_attacks = []
            prices = []
            id_party = 0
            stop_at = []

            for b in data['table_data']:
                ids.append(b[0])
                is_attacks.append(b[1])
                prices.append(b[2])
                id_party = b[3]
                stop_at.append(b[4])

            try:
                if is_simple:
                    print(Utils.sums_per_member_from_wars(Bot(cookies=cookies, client=client), ids, is_attacks, prices,
                                                          id_party))
                else:
                    print(Utils.sums_per_member_from_wars_witch_stop_word(Bot(cookies=cookies, client=client), ids,
                                                                          is_attacks,
                                                                          prices, id_party, stop_at))
                is_error = False
            except Exception as e:
                print('Новая попытка', e)

    @staticmethod
    def old_main(data):
        global client

        is_firefox_cookies = data['use_browser']

        if is_firefox_cookies:
            print('Извращенец ~(˘▾˘~)')

        client = data['client']

        if is_firefox_cookies:
            cookies = Utils.get_cookies(data)
        else:
            cookies = Utils.get_manual_cookies(data)

        Utils.kek_calculating(data, cookies, False)






