import json

from mozDecompress import mozlz4_to_text
from utils import Bot, Utils
import sqlite3

import mozDecompress


# Куки сессии
cookies = {}

url_main = 'https://rivalregions.com/#overview'
client = ''

def get_cookies(settings):
	global cookies

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
	cookies = get_cookie_from_firefox(cookies_file_uri, session_file_uri)

def get_manual_cookies(settings):
	global cookies
	cookies = {
		'PHPSESSID': settings['PHPSESSID'],
		'rr': settings['rr'],
		'rr_add': settings['rr_add'],
		'rr_f': settings['rr_f'],
		'rr_id': settings['rr_id'],
	}

def kek_calculating(is_simple = False):
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

	is_error = True
	while is_error:
		print('Начинаю смотреть шо там по урону')
		ids = [633662, 633657]
		is_attacks = [True, False]
		prices = [6000, 9000]
		id_party = 140
		stop_at = ['23:59 18.11.2024', '23:59 18.11.2024']

		f = open('BATTLES.txt', 'r', encoding='utf-8')
		battles_txt = f.read()
		f.close()

		ids = []
		is_attacks = []
		prices = []
		id_party = 0
		stop_at = []

		try:
			lines = battles_txt.split('\n')
			for i in range(len(lines)):
				if lines[i] != '':
					line = lines[i]
					parts = line.split('\t')
					ids.append(int(parts[0]))
					is_attacks.append(True if 'True' in parts[1] else False)
					prices.append(int(parts[2]))
					id_party = int(parts[3])
					stop_at.append(parts[4])

		except:
			print('Проверь файл BATTLES.txt')
			return

		try:
			if is_simple:
				print(Utils.sums_per_member_from_wars(Bot(cookies=cookies, client=client), ids, is_attacks, prices, id_party))
			else:
				print(Utils.sums_per_member_from_wars_witch_stop_word(Bot(cookies=cookies, client=client), ids, is_attacks,
																  prices, id_party, stop_at))
			is_error = False
		except Exception as e:
			print('Новая попытка', e)


def main():
	global client
	print(f'╔{"═"*40}╗')
	print(f'║{"@setux где деньги?":^40}║')
	print(f'╚{"═"*40}╝')

	print(f'╭⋟{"─"*39}╮')
	print(f'│{"Использовать ли куки из FurryFox?":^40}│')
	print(f'│{"1. Да, они там есть и я ленюся":<40}│')
	print(f'│{"2. Нет, использовать заполненный мною":<40}│')
	print(f'╰{"─" * 39}⋞╯')
	firefox_cookies_answer = input(f'Каков твой выбор: ')
	is_firefox_cookies = True if firefox_cookies_answer == '1' else False

	if is_firefox_cookies:
		print('Извращенец ~(˘▾˘~)')

	settings = None

	f = open('SETTINGS.txt', 'r', encoding='utf-8')
	settings_txt = f.read()
	f.close()
	settings = json.loads(settings_txt.replace('\r', ' ').replace('\n',' ').replace("\\", "\\\\"))

	client = settings['client']

	if is_firefox_cookies:
		get_cookies(settings)
	else:
		get_manual_cookies(settings)

	print(f'╭⋟{"─" * 39}╮')
	print(f'│{"МЕНЮ":^40}│')
	print(f'│{"1. Шо там по деньгам ДО 46 часов!":<40}│')
	print(f'│{"2. Шо там вообще по деньгам-то?":<40}│')
	print(f'╰{"─" * 39}⋞╯')

	choose = input("Ну так што: ")
	if choose == '1':
		kek_calculating(False)
	if choose == '2':
		kek_calculating(True)



	pass


main()

#get_cookies()

#bot = Bot(cookies=cookies, client=client)

#kek_calculating()

input("Нажмите Enter для завершения программы...")