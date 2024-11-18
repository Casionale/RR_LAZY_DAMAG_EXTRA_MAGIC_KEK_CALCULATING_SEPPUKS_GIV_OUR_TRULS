import json

from mozDecompress import mozlz4_to_text
from utils import Bot, Utils
import sqlite3

import mozDecompress

# Куки сессии
cookies = {}

def get_cookie_from_firefox(cookies_file_uri, session_file_uri):
	connection = sqlite3.connect(cookies_file_uri)

	cursor = connection.cursor()
	cursor.execute('''
	SELECT name, value FROM moz_cookies WHERE (name = ? OR name = ? OR name = ? OR name = ? OR name = ?) AND host = ?
	''',('rr', 'rr_add','rr_f', 'rr_id', 'PHPSESSID', 'rivalregions.com'))
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

cookies_file_uri = r'C:\Users\Admin\AppData\Roaming\Mozilla\Firefox\Profiles\9zr30oq8.default-release\cookies.sqlite'
session_file_uri = r'C:\Users\Admin\AppData\Roaming\Mozilla\Firefox\Profiles\9zr30oq8.default-release\sessionstore-backups\previous.jsonlz4'

cookies = get_cookie_from_firefox(cookies_file_uri, session_file_uri)

pass

url_main = 'https://rivalregions.com/#overview'
client = 'c2a2c96cdff39de636f0f4cee7debb41'

bot = Bot(cookies=cookies, client=client)


is_error = True

while is_error:
	try:
		data_main = bot.get_data_main(url=url_main)
		print(data_main)
		if data_main == 'Сессия устарела!' or 'Пустой ответ':
			#raise Exception
			pass
		is_error = False
	except:
		print('Новая попытка')





# Создаем и запускаем поток
bot.alive()

#defense_damage = bot.get_list_damage_from_war(632917, False)
#print(defense_damage)
#print(f'В защите {len(defense_damage)}')

#attack_damage = bot.get_list_damage_from_war(632917, True)
#print(attack_damage)
#print(f'В атаке {len(attack_damage)}')

#partys = bot.get_list_damage_from_war_partys(632917)
#print(partys)
#print(len(partys))

is_error = True

while is_error:
	print('Начинаю смотреть шо там по урону')
	ids = [633563,633662]
	is_attacks = [False,True]
	prices = [6000,6000]
	id_party = 140
	stop_at = ['4:46 18.11.2024', '23:59 18.11.2024']
	try:
		#print(Utils.sums_per_member_from_wars(Bot(cookies=cookies, client=client), ids, is_attacks, prices, id_party))
		print(Utils.sums_per_member_from_wars_witch_stop_word(Bot(cookies=cookies, client=client), ids, is_attacks,
															  prices, id_party, stop_at))
		is_error = False
	except Exception as e:
		print('Новая попытка', e)



print("Основная программа запущена. Сессия будет обновляться в фоновом режиме.")
# Здесь ваш основной код
# Например, можно использовать input() чтобы программа не завершалась сразу
input("Нажмите Enter для завершения программы...")