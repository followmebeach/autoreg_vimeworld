import string
import requests
from bs4 import BeautifulSoup
from time import sleep
import json
import random
from getch import pause_exit

user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36"

# Конфиг
try:
    with open("config.json", "r", encoding="utf-8") as config:
        config = json.loads(config.read())[0]
except FileNotFoundError:
    print("Не найден config.json\n")
    pause_exit(0, "Нажмите любую клавишу для выхода....")

rucaptcha_key = config["rucaptcha_key"]
nickname_offset = config["nickname_offset"]
amount_accounts = 1


def generate():
    global amount_accounts
    global nickname_offset

    # Генерируем ник
    if config["generate_type"] == 1:
        username = ""
        for i in range(random.randint(6, 16)):
            username += random.choice(string.ascii_lowercase)
        username = str(username[0]).upper() + username[1:]
    else:
        username = config["nickname"] + str(nickname_offset)

    # Генерируем пароль
    if config["pass_as_nick"]:
        password = username
    else:
        password = ""
        for i in range(10):
            password += random.choice(string.ascii_lowercase)

    # Получаем GoogleKey для решения капчи
    source = requests.get("https://cp.vimeworld.ru/register", headers={"User-Agent": user_agent}).text
    soup = BeautifulSoup(source, "html.parser")
    google_key = soup.find("div", {"class": "g-recaptcha"}).get("data-sitekey")

    # Заливаем капчу на RuCaptcha и получаем её id
    captcha_id = requests.get(f"https://2captcha.com/in.php?key={rucaptcha_key}&method=userrecaptcha&googlekey={google_key}&pageurl=https://cp.vimeworld.ru/register").text
    if captcha_id[:2] != "OK":
        if captcha_id == "ERROR_ZERO_BALANCE":
            print("Error: Недостаточно средств на аккаунте RuCaptcha.\n")
            pause_exit(0, "Нажмите любую клавишу для выхода....")
        else:
            print("Error: Произошла неизвестная ошибка. Проверьте ключ API\n")
            pause_exit(0, "Нажмите любую клавишу для выхода....")

    captcha_id = captcha_id[3:]

    sleep(15)

    # Проверяем решина ли капча
    while True:
        try:
            recaptcha_response = requests.get(f"https://2captcha.com/res.php?key={rucaptcha_key}&action=get&id={captcha_id}").text
            if recaptcha_response == "CAPCHA_NOT_READY":
                pass
            elif recaptcha_response == "ERROR_CAPTCHA_UNSOLVABLE":
                print(f"{username}:{password} | Answer: Не удалось решить капчу")
                return
            else:
                break
            sleep(2)
        except requests.exceptions.ConnectionError:
            sleep(10)

    recaptcha_response = recaptcha_response[3:]

    # Отправляем запрос на регистрацию
    vimeworld = requests.post("https://cp.vimeworld.ru/register", data={"username": username, "password": password, "password_confirm": password, "email": f"{username}@mail.ru", "g-recaptcha-response": recaptcha_response, "rules": "accept", "register": "Регистрация"}).text
    vimeworld_parse = BeautifulSoup(vimeworld, "html.parser")
    status = vimeworld_parse.find("div", {"class": "alert"}).text.replace('×', '').replace('\n', '')
    print(f"{username}:{password} | Answer: {status}")

    if status == "Регистрация прошла успешно":
        amount_accounts += 1

        with open("accounts.txt", "a") as log:
            log.write(f"{username}:{password}\n")

    nickname_offset += 1


if __name__ == "__main__":
    # Выводим баланс RuCaptcha
    balance = requests.get(f"http://rucaptcha.com/res.php?key={rucaptcha_key}&action=getbalance").text
    if balance == "ERROR_WRONG_USER_KEY":
        print("Error: API ключ должен иметь длину в 32 символа.\n")
        pause_exit(0, "Нажмите любую клавишу для выхода....")
    elif balance == "ERROR_KEY_DOES_NOT_EXIST":
        print("Error: Неверный ключ API\n")
        pause_exit(0, "Нажмите любую клавишу для выхода....")
    elif balance == "IP_BANNED":
        print("Error: Ваш IP-адрес забанен за многократные попытки авторизации с неверным токеном.\nБан автоматически исчезнет через 5 минут.\n")
        pause_exit(0, "Нажмите любую клавишу для выхода....")
    else:
        print(f"Баланс RuCaptcha: {balance}р.\n")

    # Запускаем регистрацию аккаунтов
    print(f"Запущена регистрация {config['amount_accounts']} аккаунтов. Пожалуйста, подождите...")
    print(f"Тип генирации: {config['generate_type']}\n")

    while True:
        if amount_accounts <= config["amount_accounts"]:
            generate()
        else:
            pause_exit(0, "Нажмите любую клавишу для выхода....")