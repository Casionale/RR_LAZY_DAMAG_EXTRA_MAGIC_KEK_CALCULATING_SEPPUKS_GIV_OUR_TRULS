# Когда сетух покормит нас вкусными заказами...
## И жир напишет к роре достойное api
### Мир очистится и войны перенесутся исключительно в рору

# 1. Где я и как этим пользоваться?
**1.1** Для того, чтобы программа заработала и произошло подключение к роре, необходимо [перенести](#как-загрузить-в-программу-cookies) в программу cookies. Я не умею авторизовываться и вообще у меня лапки.

**1.2** После того, как cookies были перенесены любым из способов, необходимо заполнить [информацию](#3-круто-но-хотелось-бы-ещё-урон-посчитать) о войнах, которые необходимо посчитать.

**1.3** Зная всю информацию, необходимо тегнуть `@setux` и получить трюли для раздачи няшам-стесняшам синдиката.

# 2. А более конкретно-то можно?
#### Да.

### Как загрузить в программу cookies?
Для того, чтобы перенести в программу cookies из браузера есть два способа:

**I** Использовать браузер Firefox. При использовании этого браузера вы сохраняете куки роры с файле кук и куку сессии в отдельном файле с сессионными куками. Примеры путей до этих файлов в самом конце инструкции. 

**II** Записать куки вручную в файл настроек. Этот способ придётся использовать всем тем, кто использует браузере на движке Chromium (тысячи их), реализация загрузки кук оттуда не реализована в данный момент.

Теперь, когда был выбран способ загрузки кук, необходимо заполнить файл `SETTINGS.txt`, который представляет собой JSON файл (ДА, В ВИДЕ .txt ЧТОБЫ ВСЕ СРАЗУ ОТКРЫЛИ). В этом файле необходимо заполнить:

Поле `cookies_file_uri` : путь к файлу базы данных кук **браузера**

Поле `session_file_uri` : путь к файлу сессионных кук **браузера**

Поле `rr` : Только при **ручном** вводе кук

Поле `rr_add`  Только при **ручном** вводе кук

Поле `rr_f` : Только при **ручном** вводе кук

Поле `rr_id` : Только при **ручном** вводе кук

Поле `PHPSESSID` : Только при **ручном** вводе кук

Поле `client` : параметр `?c='`, который рора вставляет в каждый запрос. Можно посмотреть в браузере на вкладке Network при включенном режиме разработчика `F12`

Пример файла `SETTINGS.txt`:
Одновременно заполнять и пути для кук браузера и сами куки - не надо.
Однако заполнить `client` необходимо в обоих случаях.

    {
    "cookies_file_uri": "C:\Users\UserName\AppData\Roaming\Mozilla\Firefox\Profiles\4xg38uk5.default-release\cookies.sqlite",
    "session_file_uri": "C:\Users\UserName\AppData\Roaming\Mozilla\Firefox\Profiles\4xg38uk5.default-release\sessionstore-backups\previous.jsonlz4",
    "client": "c8f3e25e2b0e4f88729228cec821dac2",
    "rr": "970e99eb8ff60516a15873cc801c6276",
    "rr_add": "605f5240ba47bf0bd47a165eff35ee63",
    "rr_f": "f766e1ff6688f354523633e7dc1e6ad7",
    "rr_id": "2001633759",
    "PHPSESSID": "fhSWnxQyxRhWJBaOwxVkoYWTvD"
    }

# 3. Круто, но хотелось бы ещё урон посчитать

Для того чтобы посчитать урон и оплату, необходимо заполнить файл `BATTLES.txt`.

Пример файла `BATTLES.txt`:

    633744	False	6000	140	23:59 20.11.2024
    634081	False	6000	140	23:59 20.11.2024

### Я ничего не понял, что это???

Давайте разберёмся. Файл состоит из 5 колонок и неограниченного количества строк.
Данные столбцов разделены меж собой `tab`!

#### ~~Сейчас я вам покажу откуда готовилось наступление~~

| Столбец     | Что это?                                      | Откудава брать и что писать                                                                   |
|-------------|-----------------------------------------------|-----------------------------------------------------------------------------------------------|
| ID войны    | Это id войны из ссылки на войну               | Из ссылки, например `https://m.rivalregions.com/#war/details/633744` id войны будет **633744** |
| Сторона     | Обороняющиеся или атакующая сторона конфликта | Из заказа, оборона **False**, атака **True**                                                  |
| Цена урона  | У урона есть цена, впиши её и получишь ценник | Из заказа, например `6/1` будет **6000**                                                      |
| ID партии   | Это id партии.                                | Из ссылки на партию, например СК это **140**                                                  |
| Время стопа | Время, после которого мы льём 0/1             | Из заказа. Премя представлено в виде `часы:минуты день.месяц.год`                               |

