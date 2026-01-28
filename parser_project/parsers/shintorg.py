from bs4 import BeautifulSoup
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import re

def extract_brand(name):
    words = name.replace("Масло моторное", "").strip().split()
    if words:
        if "-" in words[0] or (len(words) > 1 and words[1][0].isupper() and not re.search(r'\d', words[1])):
            return f"{words[0]}-{words[1]}" if "-" not in words[0] else words[0]
        return words[0]
    return "Не найден"

def get_product_data():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )

    products = []
    base_url = 'https://www.shintorg48.ru'
    category_url = base_url + '/catalog/masla/motornye/'

    try:
        for page in range(1, 6):  # Обрабатываем первые 5 страниц
            current_url = f"{category_url}?PAGEN_1={page}"
            print(f"Открываем страницу: {current_url}")
            driver.get(current_url)
            time.sleep(4)
            soup = BeautifulSoup(driver.page_source, 'lxml')

            product_cards = soup.find_all('h3', class_='item-name')
            print(f"На странице {page} найдено товаров: {len(product_cards)}")

            if not product_cards:
                print(f"На странице {page} нет товаров, прекращаем обработку")
                break

            for card in product_cards:
                link_tag = card.find('a')
                if not link_tag:
                    continue

                product_url = base_url + link_tag['href']
                driver.get(product_url)
                time.sleep(2)
                product_soup = BeautifulSoup(driver.page_source, 'lxml')

                product = {}

                name_elem = product_soup.find('h1', class_='product-name')
                product_name = name_elem.text.strip() if name_elem else "Нет названия"
                product['name'] = product_name

                price_elem = product_soup.find('span', class_='item-price')
                price = price_elem.text.strip().replace('\xa0', '').replace('c', '') if price_elem else "Нет цены"
                product['price'] = price

                product['url'] = product_url
                product['brand'] = extract_brand(product_name)

                products.append(product)
                print(f"Обработан товар: {product_name}")

        return products

    except Exception as e:
        print(f"Ошибка: {e}")
        return []
    finally:
        driver.quit()

def save_to_excel(products):
    if not products:
        print("Нет данных для сохранения")
        return None

    df = pd.DataFrame(products)
    df = df[['name', 'price', 'brand', 'url']]
    df.columns = ['Название', 'Цена', 'Бренд', 'Ссылка']

    excel_file = 'shintorg_masla.xlsx'
    df.to_excel(excel_file, index=False)
    print(f"Данные сохранены в файл {excel_file}")

    return df

if __name__ == "__main__":
    print("Начало работы парсера...")
    products = get_product_data()
    if products:
        print(f"\nУспешно собрано {len(products)} товаров")
        df = save_to_excel(products)
        print("\nПервые 5 записей:")
        print(df.head())
    else:
        print("Не удалось собрать данные")