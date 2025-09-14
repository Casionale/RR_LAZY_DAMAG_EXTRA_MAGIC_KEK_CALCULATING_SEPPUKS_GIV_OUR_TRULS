import csv
import json
import os
import sqlite3
import threading
import time
from datetime import datetime
from urllib.parse import urlparse

import cloudscraper
import dateutil
from bs4 import BeautifulSoup
import datetime

import re

from StatUtils import StatUtils
from mozDecompress import mozlz4_to_text

# Куки сессии
cookies = {}

url_main = 'https://rivalka.ru/#overview'
#url_main = 'https://m.rivalregions.com/#overview'
domain = 'https://rivalka.ru'
#domain = 'https://m.rivalregions.com'
client = ''

class Bot:

    def __init__(self, cookies, client):
        self.cookies = cookies
        self.client = client
        self.timeout = 1

    def get_data_main(self, url):
        scraper = cloudscraper.create_scraper(browser='firefox')
        response = scraper.get(url_main, cookies=self.cookies, timeout=(50, 100))

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

        time.sleep(self.timeout)
        Utils.log(f'Жду {self.timeout} сек')
        response = scraper.get(f'{domain}/main/get_hp?c={self.cookies["rr"]}', cookies=self.cookies)
        Utils.log(f'Запрос на {domain}/main/get_hp?c={self.cookies["rr"]}')

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
                time.sleep(self.timeout)
                Utils.log(f'Жду {self.timeout} сек')
                response = scraper.get(url_main, cookies=self.cookies)
                Utils.log(f'Запрос на {url_main}')

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
        time.sleep(self.timeout)
        Utils.log(f'Жду {self.timeout} сек')
        url = f"{domain}/war/damage/{id}/{0 if is_attack == True else 1}?c={self.client}"
        damages = self.get_damage_members(url)

        return damages

    def get_damage_members(self, url):
        scraper = cloudscraper.create_scraper(browser={'browser': 'firefox', 'platform': 'windows',
                                                       'mobile': False})
        is_error = True
        while is_error:
            time.sleep(self.timeout)
            Utils.log(f'Жду {self.timeout} сек')
            response = scraper.get(url, cookies=self.cookies, timeout=4000)
            Utils.log(f'Запрос на {url}')

            strip_response = response.text.replace('\n', '')
            if response.text == '':
                Utils.log(f'Пустой ответ на {url}')
                raise Exception
            # print(response.text)
            # print(strip_response)
            gmg = [x.group() for x in re.finditer(pattern=r'<tr(.|\n)*?</tr>', string=strip_response)]
            damages = []

            if len(gmg) > 0:
                is_error = False
            else:
                print(f'Попытка с пустым уроном, попробуй перейти по {url}')
                scraper.get(f'{domain}', cookies=self.cookies, timeout=4)
                Utils.log(f'Пустой урон, перешли на {domain}')
                time.sleep(3)

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

                    nme = soup.find_all('td', {'class': 'list_name pointer'})
                    if len(nme) > 0:
                        name = soup.find_all('td', {'class': 'list_name pointer'})[0].text.strip()
                    else:
                        name = soup.find_all('td', {'class': 'list_name pointer tip green'})[0].text.strip()

                    tr_tag = soup.find('tr', {'class': 'list_link header_buttons_hover'})
                    if tr_tag:
                        user = tr_tag.get('user')
                    else:
                        user = None

                    individual_damage = {
                        "name": name,
                        "lvl": lvl,
                        #"lvl": soup.find_all('span', {'class': 'yellow'})[0].text.strip(),
                        #"lvl": soup.find_all('td', {'class': 'yellow list_level'})[0].text.strip(),
                        "damage": dbg[1].contents[0].strip().replace('.', ''),
                        'id': soup.find('tr').attrs['user']
                    }
                except Exception as e:
                    Utils.log(f'Исключение {e}')
                    f = open('3.txt', 'w', encoding='utf-8')
                    f.write(g)
                    f.close()

                damages.append(individual_damage)
        return damages

    def get_list_damage_from_war_partys(self, id):
        time.sleep(self.timeout)
        Utils.log(f'Жду {self.timeout} сек')
        url = f'{domain}/listed/partydamage/{id}?c={self.client}'
        scraper = cloudscraper.create_scraper()
        response = scraper.get(url, cookies=self.cookies)
        Utils.log(f'Запрос на {url}')
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
            is_attack = 0 if is_attack == "True" else 1
            url = f'{domain}/war/damageparties/{id}/{is_attack}/{id_party}?c={self.client}'
            damages = self.get_damage_members(url)
            if type(damages) is not list or len(damages) == 0:
                is_error = True
                print('Пустой дамаг :с')
                Utils.log(f'Пустой дамаг')
            else:
                is_error = False
        return damages

    def get_damage(self, url):
        is_error = True
        while is_error:
            time.sleep(self.timeout)
            Utils.log(f'Жду {self.timeout} сек')
            scraper = cloudscraper.create_scraper()
            response = scraper.get(url, cookies=self.cookies, timeout=100)
            Utils.log(f'Запрос на {url}')

            error_str = '<script>\r\n$(document).ready(function() {\r\n\twindow.location="https://rivalka.ru";\r\n\t});\r\n</script>\r\n'
            if (error_str != response.text):
                is_error = False
            else:
                r = scraper.get(domain, cookies=self.cookies, timeout=40)
                Utils.log(f'Запрос на {domain}')

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
                Utils.log(f'Исключение {e}')
                return []
        return damage

    def get_part_from_dep(self, url):
        scraper = cloudscraper.create_scraper(browser={'browser': 'firefox', 'platform': 'windows',
                                                       'mobile': False})
        is_error = True
        items = []
        while is_error:
            time.sleep(self.timeout)
            Utils.log(f'Жду {self.timeout} сек')
            response = scraper.get(url, cookies=self.cookies, timeout=4000)
            Utils.log(f'Запрос на {url}')

            strip_response = response.text.replace('\n', '')

            error_str = '<script>\r\n$(document).ready(function() {\r\n\twindow.location="https://rivalka.ru";\r\n\t});\r\n</script>\r\n'
            if (error_str != response.text):
                scraper.get(domain, cookies=self.cookies, timeout=4)
                Utils.log(f'Пустые депы, перешли на {domain}')
                print(f'Пустые депы, перешли на {domain}')
                time.sleep(3)
                continue

            if  response.text == '':
                break

            error_str = '<script>\r\n$(document).ready(function() {\r\n\twindow.location="https://rivalka.ru";\r\n\t});\r\n</script>\r\n'
            if (error_str != response.text):
                is_error = False

            # print(response.text)
            #print(strip_response)
            groups = [x.group() for x in re.finditer(pattern=r'<tr(.|\n)*?</tr>', string=strip_response)]
            groups.remove(groups[0])

            pattern = (r'<tr(?:.|\n)*?action="slide/profile/(?P<id>\d+)(?:.|\n)*?<td action="slide/profile/\d+" class="list_name pointer">(?P<name>.+?) \(\+(?P<up>\d+)\)</td>(?:.|\n)*?" class="list_level">(?P<date>.+?)</td>')

            dt_now = datetime.datetime.today().strftime('%Y %m %d')
            dt_yesterday = (datetime.datetime.today() - datetime.timedelta(days=1)).strftime('%Y %m %d')

            for g in groups:

                matches = re.finditer(pattern=pattern, string=g)
                for match in matches:
                    profile_id = match.group("id")
                    name = match.group("name")
                    up = match.group("up")
                    date = match.group("date")

                    if "Сегодня" in  date:
                        date = date.replace('Сегодня',dt_now)
                        date = dateutil.parser.parse(date)
                    elif "Вчера" in date:
                        date = date.replace('Вчера',dt_yesterday)
                        date = dateutil.parser.parse(date)
                    else:
                        date = Utils.parse_russian_date(date)

                    items.append({'id':profile_id, 'name':name, 'up':up, 'date':date})

        return items

    def get_party_member(self, url):
        scraper = cloudscraper.create_scraper(browser={'browser': 'firefox', 'platform': 'windows',
                                                       'mobile': False})
        is_error = True
        items = []

        while is_error:
            time.sleep(self.timeout)
            Utils.log(f'Жду {self.timeout} сек')
            response = scraper.get(url, cookies=self.cookies, timeout=4000)
            Utils.log(f'Запрос на {url}')

            strip_response = response.text.replace('\n', '')

            error_str = '''<script>
$(document).ready(function() {
	window.location="https://rivalka.ru";
	});
</script>
'''
            er_str = error_str.strip()
            r_t_str = response.text.strip()

            er_str_normalized = error_str.replace('\r\n', '\n')
            r_t_str_normalized = response.text.replace('\r\n', '\n')

            if response.text == '':
                break

            if er_str_normalized == r_t_str_normalized:
                scraper.get(domain, cookies=self.cookies, timeout=4)
                Utils.log(f'Пустой список партии, перешли на {domain}')
                print(f'Пустой список партии, перешли на {domain}')
                time.sleep(3)
                continue
            else:
                is_error = False


            pattern=r'<tr(?:.|\n)*?action="slide/profile/(?P<id>\d+)(?:.|\n)*?'
            matches = re.finditer(pattern=pattern, string=strip_response)
            for match in matches:
                profile_id = match.group("id")
                items.append(profile_id)
        return items

    def get_party_members_images(self, members):
        scraper = cloudscraper.create_scraper(browser={'browser': 'firefox', 'platform': 'windows',
                                                       'mobile': False})

        items = {}

        for member in members:
            is_error = True

            while is_error:
                time.sleep(self.timeout)
                Utils.log(f'Жду {self.timeout} сек')

                url = f"{domain}/slide/profile/{member}"

                response = scraper.get(url, cookies=self.cookies, timeout=4000)
                Utils.log(f'Запрос на {url}')

                strip_response = response.text.replace('\n', '')

                error_str = '''<script>
    $(document).ready(function() {
        window.location="https://rivalka.ru";
        });
    </script>
    '''
                er_str = error_str.strip()
                r_t_str = response.text.strip()

                er_str_normalized = error_str.replace('\r\n', '\n')
                r_t_str_normalized = response.text.replace('\r\n', '\n')

                if response.text == '':
                    break

                if er_str_normalized == r_t_str_normalized:
                    scraper.get(domain, cookies=self.cookies, timeout=4)
                    Utils.log(f'Пустой профиль {domain}')
                    print(f'Пустой профиль, перешли на {domain}')
                    time.sleep(3)
                    continue
                else:
                    is_error = False


                pass
                pattern= r'<img[^>]*id="p_old_pic"[^>]*src="//?([^"]+)"'
                matches = re.finditer(pattern=pattern, string=strip_response)
                for match in matches:
                    avatar = match.group(1)
                    items[member] = avatar
            print(f"Закончен {member}")

        return items

    def download_image(self, url: str, save_dir: str) -> str:
        """
        Скачивает изображение по URL и сохраняет в указанную папку.
        Имя файла берётся из URL. Если в URL нет схемы, добавляет https://.
        Если файл уже существует, не скачивает заново и возвращает путь.
        Возвращает полный путь к сохранённому файлу.
        """
        scraper = cloudscraper.create_scraper(browser={'browser': 'firefox', 'platform': 'windows',
                                                       'mobile': False})
        # добавляем схему, если её нет
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "https:" + url if url.startswith("//") else "https://" + url

        os.makedirs(save_dir, exist_ok=True)

        # имя файла из URL
        filename = os.path.basename(urlparse(url).path)
        save_path = os.path.join(save_dir, filename)

        # если файл уже есть, просто возвращаем путь
        if os.path.exists(save_path):
            return save_path

        # скачиваем файл
        response = scraper.get(url)
        response.raise_for_status()

        with open(save_path, "wb") as f:
            f.write(response.content)

        return save_path



class Utils:

    @staticmethod
    def parse_russian_date(date_str: str) -> datetime:
        months = {
            "Января": "01", "Февраля": "02", "Марта": "03", "Апреля": "04",
            "Мая": "05", "Июня": "06", "Июля": "07", "Августа": "08",
            "Сентября": "09", "Октября": "10", "Ноября": "11", "Декабря": "12"
        }

        parts = date_str.split()
        if len(parts) == 4:
            day, month, year, time = parts
            month_num = months.get(month)
            if month_num:
                return datetime.datetime.strptime(f"{day}.{month_num}.{year} {time}", "%d.%m.%Y %H:%M")

        raise ValueError(f"Некорректный формат даты: {date_str}")

    @staticmethod
    def get_all_attack_sorted_by_stamp(un_unic_damage):
        all_attack = []
        for member in un_unic_damage:
            for dmg in un_unic_damage[member][0]:
                n_dmg = dmg
                n_dmg['owner'] = member

                all_attack.append(n_dmg)
        all_attack = sorted(all_attack, key=lambda d: d['stamp'])
        return all_attack
    @staticmethod
    def get_stop_at_by_limit(all_damage_sorted_by_stamp, limit, id):
        attacks = []
        current = 0
        war_attack = [damage for damage in all_damage_sorted_by_stamp if int(damage['id_war']) == id]
        for attack in war_attack:
            dmg = int(attack['damage'])
            if (current + dmg) < (limit + dmg):
                current += dmg
                attacks.append(attack)

        timestamp_limit = attacks[-1]['stamp']
        return timestamp_limit




    @staticmethod
    def parse_number(string):
        suffixes = {
            'k': 10 ** 3,
            'kk': 10 ** 6,
            'kkk': 10 ** 9,
            'kkkk': 10**12,
        }

        string = string.strip().lower()

        for suffix, multiplier in sorted(suffixes.items(), key=lambda x: -len(x[0])):
            if string.endswith(suffix):
                number = float(string[:-len(suffix)])
                return int(number * multiplier)

        try:
            return int(string)
        except ValueError:
            raise ValueError(f"Некорректный формат строки: {string}")

    @staticmethod
    def calculate_truls_for_war(damage, id_war, price, stop_time, name = ''):
        damage = damage[0]
        sum = 0
        sum_damage = 0
        no_pay_sum = 0
        str_check = f'{name:^50}\n'
        if type(stop_time) != int:
            stop_time = int(datetime.datetime.strptime(stop_time, "%H:%M %d.%m.%Y").timestamp())
        for dmg in damage:
            if dmg['stamp'] <= stop_time:
                if int(dmg['id_war']) == id_war:
                    add_sum = int(dmg['damage']) * price
                    sum += add_sum
                    sum_damage += int(dmg['damage'])
                    str_check += f'{dmg["time"]} {dmg["damage"]}  * {price} = {add_sum}\n'

                    if add_sum == 0:
                        pass
            else:
                if int(dmg['id_war']) == id_war:
                    no_pay_sum += int(dmg['damage']) * price

        str_check += f'ИТОГО: {sum} | Не оплачиваемая сумма {no_pay_sum}\n\n'

        return {'sum': sum, 'log': str_check, 'damage':sum_damage, 'no_pay': no_pay_sum}

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
    def sums_per_member_from_wars_witch_stop_word(bot, ids, is_attacks, prices, id_party, stop_at, limit, is_limit):
        members = {}
        un_unic_damage = {}
        results = []
        logs = []

        un_unic_damage = {}

        for i in range(len(ids)):
            date_time_obj = datetime.datetime.strptime(stop_at[i], '%H:%M %d.%m.%Y')

            is_error = True
            while is_error:
                try:
                    damage_members = bot.get_list_damage_from_war_party_members(ids[i], is_attacks[i], id_party)
                    is_error = False
                except Exception as e:
                    pass



            for member in damage_members:
                if member['name'] not in un_unic_damage:
                    attacks = []

                    url_damage = f'{domain}/slide/damage/{member["id"]}'

                    is_more_need = True
                    iters = 0
                    while is_more_need:
                        if iters == 0:
                            part_damage = bot.get_damage(url_damage) # Нада таво етаво по 60
                        else:
                            part_damage = bot.get_damage(f'{url_damage}/{60 * iters}')

                        if part_damage is not None and len(part_damage) > 0:
                            for d in part_damage:
                                attacks.append(d)
                            iters += 1
                        else:
                            is_more_need = False

                    if member['name'] in un_unic_damage:
                        un_unic_damage[member['name']].extend(attacks)
                    else:
                        un_unic_damage[member['name']] = [attacks]
                print(f'Законечена загрузка урона {member["name"]}')
                Utils.log(f'Законечена загрузка урона {member["name"]}')

            results.append(f'Война {ids[i]}')

            sum = 0

            csv_file_data = ''
            no_pay_data = ''
            csv_file_data_2 = ''

            all_damage_sorted_by_stamp = Utils.get_all_attack_sorted_by_stamp(un_unic_damage)

            #Если по лимиту
            if is_limit[i] == 'True':
                new_stop_at = Utils.get_stop_at_by_limit(all_damage_sorted_by_stamp, limit[i], ids[i])
                stop_at[i] = new_stop_at

            #ТУТ ВСЁ УЖЕ ДОЛЖНО БЫТЬ ИЗВЕСТНО!

            for member in un_unic_damage:
                result = Utils.calculate_truls_for_war(un_unic_damage[member], ids[i], prices[i], stop_at[i], member)
                if result['damage'] > 0:
                    #results.append(f'{member["name"]:<30}: {result["sum"]:<15} Rivals')
                    m = member
                    r = result['sum']
                    results.append(f'{m:<40}: {str(r):<15} Rivals')

                    logs.append(result['log'])
                    sum += result['sum']

                    csv_file_data += f'{m};{result["damage"]};\n'
                    no_pay_data += f'{m:<40}: {result["no_pay"]}\n'

                    id = next(item for item in damage_members if item["name"] == m)
                    csv_file_data_2 += f'{m};{result["damage"]};{domain}/#slide/profile/{id["id"]};\n'

            results.append(f'ИТОГО: {sum} Rivals\n')

            f = open(f'Война {ids[i]}.csv', 'w', encoding='utf-8')
            f.write(csv_file_data)
            f.close()

            f = open(f'Неоплаченное {ids[i]}.txt', 'w', encoding='utf-8')
            f.write(no_pay_data)
            f.close()

            f = open(f'Война 2.0 {ids[i]}.csv', 'w', encoding='utf-8')
            f.write(csv_file_data_2)
            f.close()

        f = open('Money.txt', 'w', encoding='utf-8')
        for r in results:
            f.write(r + '\n')
        f.close()

        f = open('ResultLogs.txt', 'w', encoding='utf-8')
        for r in logs:
            f.write(r + '\n')
        f.close()

        print('Готово! Рассмотри файлы Money.txt, ResultLogs.txt и csv файлы с уроном.')

    @staticmethod
    def get_cookies(settings):

        def get_cookie_from_firefox(cookies_file_uri, session_file_uri):
            connection = sqlite3.connect(cookies_file_uri)

            cursor = connection.cursor()
            cursor.execute('''
    	SELECT name, value FROM moz_cookies WHERE (name = ? OR name = ? OR name = ? OR name = ? OR name = ?) AND host = ?
    	''', ('rr', 'rr_add', 'rr_f', 'rr_id', 'PHPSESSID', f'{domain.replace("https://","")}'))
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
                if cookie['host'] == f'{domain}' and cookie['name'] == 'PHPSESSID':
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
                    Utils.log(f'Сессия устарела или пустой ответ')
                    pass
                is_error = False
            except Exception as e:
                Utils.log(f'Исключение {e}')
                print('Новая попытка посчитать')

        is_error = True
        while is_error:
            print('Начинаю смотреть шо там по урону')


            ids = []
            is_attacks = []
            prices = []
            id_party = 0
            stop_at = []
            limit = []
            is_limit = []

            for b in data['table_data']:
                ids.append(b[0])
                is_attacks.append(b[1])
                prices.append(b[2])
                id_party = b[3]
                stop_at.append(b[4])
                limit.append(b[5])
                is_limit.append(b[6])

            try:
                if is_simple:
                    print(Utils.sums_per_member_from_wars(Bot(cookies=cookies, client=client), ids, is_attacks, prices,
                                                          id_party, limit, is_limit))
                else:
                    print(Utils.sums_per_member_from_wars_witch_stop_word(Bot(cookies=cookies, client=client), ids,
                                                                          is_attacks,
                                                                          prices, id_party, stop_at, limit, is_limit))
                is_error = False
            except Exception as e:
                print('Новая попытка', e)

    @staticmethod
    def old_main(data):
        try:
            global client

            if data['table_data'][0][6] == 'True':
                data['table_data'][0][5] = Utils.parse_number(data['table_data'][0][5])

            is_firefox_cookies = data['use_browser']

            if is_firefox_cookies:
                print('Извращенец ~(˘▾˘~)')

            client = data['client']

            if is_firefox_cookies:
                cookies = Utils.get_cookies(data)
            else:
                cookies = Utils.get_manual_cookies(data)

            Utils.kek_calculating(data, cookies, False)
        except Exception as e:
            Utils.log(f'Исплючение {e}')

    @staticmethod
    def log(message):
        f = open('log.txt', 'a+', encoding='utf-8')
        current_datetime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        f.write(f'{current_datetime} : {message}\n')
        f.close()

    @staticmethod
    def deps(data, settings):
        print('Начинаю смотреть что там по депам')
        prepared_info = []
        for r in data:
            row = {}
            row['id'] = r['id']
            row['price'] = r['цена']
            row['start_date'] = r['начало']
            if r['лимит'] == '' or r['лимит'] == 0 or r['лимит'] == '0':
                row['end_date'] = r['конец']
            else:
                row['limit'] = r['лимит']
            row['deps'] = [i+1 for i, val in enumerate(r['чекбоксы']) if val]
            row['party'] = r['партия']
            prepared_info.append(row)

        DEPS_DEBUG = False

        if not DEPS_DEBUG:
            info = Utils.dep_method1(prepared_info, settings)
            copy_info = info


            result = None

            for id in copy_info:
                for d in copy_info[id]:
                    for item in copy_info[id][d]:
                        item['date'] = str(item['date'])
                pass

            json_info = json.dumps(copy_info, indent=4)

            if not os.path.exists('departments.json'):
                with open('departments.json', 'w', encoding='utf-8') as f:
                    f.write(json_info)
                result = info
            else:
                from_file = ''
                with open('departments.json', 'r', encoding='utf-8') as f:
                    from_file = f.read()

                from_json = json.loads(from_file)
                for_save = Utils.get_with_new_in_deps(copy_info, from_json)
                result = for_save
                with open('departments.json', 'w', encoding='utf-8') as f:
                    for_save = json.dumps(for_save, indent=4)
                    f.write(for_save)
        else:
            from_file = ''
            with open('departments.json', 'r', encoding='utf-8') as f:
                from_file = f.read()

            result = json.loads(from_file)
        deps = ['Строительный департамент',
                'Департамент золота',
                'Департамент нефти',
                'Департамент руды',
                'Департамент алмазов',
                'Департамент урана',
                'Департамент жидкого кислорода',
                'Департамент гелия 3',
                'Департамент танков',
                'Департамент космических исследований',
                'Военно-морское училище']
        res = Utils.get_info_deps_with_settings(prepared_info, settings, result, deps)

        DEPS_FILENAME = "deps.txt"
        DEPS_CSV_FILENAME = "deps.csv"

        txt_strings = ''

        for info in prepared_info:
            if info['id'] != 0:
                txt_strings += f'{info["start_date"]}, {deps[info["deps"][0]-1]}\n'
                for i in res:
                    if info['deps'][0] in res[i].keys(): #Если нужный деп
                        name = res[i]['name']
                        up = res[i][info['deps'][0]]
                        money = up * info['price']
                        txt_strings += f'{name}: {up} * {info["price"]} = {money}\n'

        with open(DEPS_FILENAME, 'w', encoding='utf-8') as f:
            f.write(txt_strings)


        print(f'Расчёты по партии готовы! Просмотри файл {DEPS_FILENAME}')



    @staticmethod
    def get_info_deps_with_settings(prepared_info, settings, result, deps):
        members = Utils.get_patry_member(settings, prepared_info[0]['party'])
        result_work = {}
        log = ''
        csv_strings = ''
        for info in prepared_info:
            if info['id'] != 0:
                log += f'Гос id {info["id"]}\n'

                is_limit = False
                limit = 0
                start_date = datetime.datetime.strptime(info['start_date'], "%d.%m.%y %H:%M")
                if 'end_date' in info:
                    end_date = datetime.datetime.strptime(info['end_date'], "%d.%m.%y %H:%M")
                else:
                    is_limit = True

                try:
                    data = result[str(info['id'])]
                except:
                    data = result[info['id']]
                it = 0
                for dep in data:
                    if it != 0:
                        continue
                    log += f'Деп : {deps[dep-1]}\n'
                    for item in data[dep]:
                        if item['id'] in members: # ЕСЛИ НАШ СЛОНЯРА
                            if is_limit:
                                limit += int(item['up'])
                                if limit > info['limit']-int(item['up']):
                                    continue
                            dt = datetime.datetime.strptime(item['date'], "%Y-%m-%d %H:%M:%S")
                            if dt >= start_date:
                                if item['id'] in result_work.keys():
                                    if dep in result_work[item['id']].keys():
                                        result_work[item['id']][dep] += int(item['up'])
                                        log += f'{item["date"]} {result_work[item["id"]]["name"]} + {item["up"]} Лимит {limit}\n'
                                        csv_strings+=f'{item["date"]};{result_work[item["id"]]["name"]};{item["up"]};{limit}\n'
                                    else:
                                        result_work[item['id']][dep] = int(item['up'])
                                        log += f'{item["date"]} {result_work[item["id"]]["name"]} + {item["up"]} Лимит {limit}\n'
                                        csv_strings += f'{item["date"]};{result_work[item["id"]]["name"]};{item["up"]};{limit}\n'
                                else:
                                    result_work[item['id']] = {}
                                    result_work[item['id']]['name'] = item['name']
                                    result_work[item['id']][dep] = int(item['up'])
                                    log += f'{item["date"]} {result_work[item["id"]]["name"]} + {item["up"]} Лимит {limit}\n'
                                    csv_strings += f'{item["date"]};{result_work[item["id"]]["name"]};{item["up"]};{limit}\n'
                    it+=1

        with open('dep_log.txt', 'w', encoding='utf-8') as f:
            f.write(log)

        with open('deps.csv', 'w', encoding='utf-8') as f:
            f.write(csv_strings)

        return result_work

    @staticmethod
    def get_patry_member(settings, id_party):
        cookies = Utils.get_cookies(settings)
        bot = Bot(cookies=cookies, client=client)
        url = f'{domain}/listed/party/{id_party}'
        members = bot.get_party_member(url)
        return members


    @staticmethod
    def get_with_new_in_deps(old, new):
        new_items = 0
        for id in new:
            if int(id) in old.keys():
                for dep in new[id]:
                    if int(dep) in old[int(id)].keys():
                        for item in new[id][dep]:
                            if item not in old[int(id)][int(dep)]:
                                old[int(id)][int(dep)].append(item)
                                new_items += 1
                    else:
                        old[int(id)][int(dep)] = new[id][dep]
                        print('Новый деп полностью добавлен')
            else:
                old[int(id)] = new[id]
                print('Новый гос полностью добавлен')


        print(f"Новых записей: {new_items}")
        return old



    @staticmethod
    def dep_method1(prepared_info, settings):
        cookies = Utils.get_cookies(settings)
        bot = Bot(cookies=cookies, client=client)
        all_info = {}
        for p in prepared_info:
            if p['id'] == 0:
                continue

            all_info[p['id']] = {}

            for dep in p['deps']:
                all_info[p['id']][dep]=[]
                url = f'{domain}/listed/professors/{dep}/{p["id"]}'

                all_info[p['id']][dep].extend(bot.get_part_from_dep(url))

                is_continue = True
                iterator = 0
                while is_continue:
                    iterator += 1
                    new = bot.get_part_from_dep(url+f'/{iterator*60}')
                    all_info[p['id']][dep].extend(new)
                    if len(new) == 0:
                        is_continue = False
                    print(f"Получено записей: {len(all_info[p['id']][dep])}")

        return all_info

    @staticmethod
    def new_main(order_data, cookies):
        try:
            return Utils.new_kek_calculating(order_data, cookies, False)

        except Exception as e:
            Utils.log(f'Исплючение {e}')

    @staticmethod
    def new_kek_calculating(order_data, cookies, is_simple=False):
        is_error = True
        while is_error:
            try:
                bot = Bot(cookies=cookies, client=client)
                data_main = bot.get_data_main(url=url_main)
                print(data_main)
                if data_main == 'Сессия устарела!' or 'Пустой ответ':
                    # raise Exception
                    Utils.log(f'Сессия устарела или пустой ответ')
                    pass
                is_error = False
            except Exception as e:
                Utils.log(f'Исключение {e}')
                print('Новая попытка посчитать')

        is_error = True
        while is_error:
            print('Начинаю смотреть шо там по урону')

            ids = order_data[0]
            is_attacks = order_data[1]
            prices = order_data[2]
            id_party = 140
            stop_at = order_data[3]
            limit = order_data[4]
            is_limit = order_data[5]

            try:
                return Utils.new_sums_per_member_from_wars_witch_stop_word(Bot(cookies=cookies, client=client), ids,
                                                                          is_attacks,
                                                                          prices, id_party, stop_at, limit, is_limit)
                is_error = False
            except Exception as e:
                print('Новая попытка', e)

    @staticmethod
    def new_sums_per_member_from_wars_witch_stop_word(bot, ids, is_attacks, prices, id_party, stop_at, limit, is_limit):
        members = {}
        un_unic_damage = {}
        results = []
        logs = []

        un_unic_damage = {}


        date_time_obj = datetime.datetime.strptime(stop_at, '%H:%M %d.%m.%Y')

        is_error = True
        while is_error:
            try:
                is_attacks = "False" if not is_attacks else "True"
                damage_members = bot.get_list_damage_from_war_party_members(ids, is_attacks, id_party)
                is_error = False
            except Exception as e:
                pass

        for member in damage_members:
            if member['name'] not in un_unic_damage:
                attacks = []

                url_damage = f'{domain}/slide/damage/{member["id"]}'

                is_more_need = True
                iters = 0
                while is_more_need:
                    if iters == 0:
                        part_damage = bot.get_damage(url_damage)  # Нада таво етаво по 60
                    else:
                        part_damage = bot.get_damage(f'{url_damage}/{60 * iters}')

                    if part_damage is not None and len(part_damage) > 0:
                        for d in part_damage:
                            attacks.append(d)
                        iters += 1
                    else:
                        is_more_need = False

                if member['name'] in un_unic_damage:
                    un_unic_damage[member['name']].extend(attacks)
                else:
                    un_unic_damage[member['name']] = [attacks]
            print(f'Законечена загрузка урона {member["name"]}')
            Utils.log(f'Законечена загрузка урона {member["name"]}')

        results.append(f'Война {ids}')

        sum = 0

        all_damage_sorted_by_stamp = Utils.get_all_attack_sorted_by_stamp(un_unic_damage)

        # Если по лимиту
        if is_limit == 'True':
            new_stop_at = Utils.get_stop_at_by_limit(all_damage_sorted_by_stamp, limit, ids)
            stop_at = new_stop_at

        # ТУТ ВСЁ УЖЕ ДОЛЖНО БЫТЬ ИЗВЕСТНО!

        return un_unic_damage, damage_members

        for member in un_unic_damage:
            result = Utils.calculate_truls_for_war(un_unic_damage[member], ids, prices, stop_at, member)
            if result['damage'] > 0:
                m = member
                r = result['sum']
                results.append(f'{m:<40}: {str(r):<15} Rivals')

                logs.append(result['log'])
                sum += result['sum']


        results.append(f'ИТОГО: {sum} Rivals\n')

    @staticmethod
    def kek_avatars(data, id_party=140):
        is_error = True
        while is_error:
            try:
                is_firefox_cookies = data['use_browser']
                client = data['client']
                if is_firefox_cookies:
                    cookies = Utils.get_cookies(data)
                else:
                    cookies = Utils.get_manual_cookies(data)

                bot = Bot(cookies=cookies, client=client)

                #url = f'{domain}/listed/party/{id_party}'

                OUTPUT_PATRY_URLS_AVATARS_DIR = "output_avatars_urls"

                # создаём папку, если нет
                if not os.path.exists(OUTPUT_PATRY_URLS_AVATARS_DIR):
                    os.makedirs(OUTPUT_PATRY_URLS_AVATARS_DIR)

                # формируем имя файла по текущей дате
                today = datetime.datetime.now()
                filename = f"{today.day}_{today.month}_{today.year}.json"
                filepath = os.path.join(OUTPUT_PATRY_URLS_AVATARS_DIR, filename)

                members = Utils.get_patry_member(data, 140)

                # если файл с сегодняшней датой уже есть, загружаем из него
                if os.path.exists(filepath):
                    print('Загружаю сегодняший файл со ссылками')
                    with open(filepath, "r", encoding="utf-8") as f:
                        info = json.load(f)
                else:
                    # иначе выполняем получение данных
                    print('Собираю ссылки снова')

                    info = bot.get_party_members_images(members=members)

                    # сохраняем в файл
                    with open(filepath, "w", encoding="utf-8") as f:
                        json.dump(info, f, ensure_ascii=False, indent=4)
                        print(f'Файл со ссылками был сохранён {filepath}')

                avatars = {}

                for i in info:
                    file_path = bot.download_image(info[i], f'{OUTPUT_PATRY_URLS_AVATARS_DIR}/outputs')
                    avatars[i]=file_path
                    print(f'Скачал {file_path}')

                avatar_check_result = {}

                for a in avatars:
                    result = Utils.check_pixels(avatars[a], "config_points.json", success_percent=50)
                    avatar_check_result[a]=result

                csv_result = f'account; tg; uri; result\n'

                for m in members:
                    try:
                        account = StatUtils.get_account_by_url(m)
                        if account is None:
                            csv_result += f"-; -; {m}; {avatar_check_result[m]}\n"
                        else:
                            csv_result += f"{account.name}; {account.tg}; {m}; {avatar_check_result[m]}\n"
                    except Exception as e:
                        pass


                filename = f"AVATAR CHECK {today.day}_{today.month}_{today.year}.csv"
                filepath = os.path.join(OUTPUT_PATRY_URLS_AVATARS_DIR, filename)

                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(csv_result)
                    print(f'Файл результата был сохранён {filepath}')

                is_error = False
            except Exception as e:
                Utils.log(f'Исключение {e}')
                print('Новая попытка чекать авы')



    @staticmethod
    def check_pixels(image_path: str, config_path: str, success_percent: float = 80) -> bool:
        """
        Проверяет пиксели на изображении.

        image_path - путь к изображению
        config_path - путь к JSON конфигу
        success_percent - процент совпадений для успеха
        """
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        from PIL import Image

        img = Image.open(image_path).convert("RGBA")
        width, height = img.size

        total_points = 0
        matched_points = 0

        for color_name, color_info in config.items():
            target_r, target_g, target_b = tuple(int(color_info["color"][i:i + 2], 16) for i in (1, 3, 5))
            target_alpha = int(color_info["alpha"] * 255)
            for x, y in color_info["points"]:
                total_points += 1
                if 0 <= x < width and 0 <= y < height:
                    r, g, b, a = img.getpixel((x, y))
                    if (r, g, b, a) == (target_r, target_g, target_b, target_alpha):
                        matched_points += 1

        actual_percent = (matched_points / total_points) * 100 if total_points else 0
        return actual_percent >= success_percent