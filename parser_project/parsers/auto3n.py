from bs4 import BeautifulSoup
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time

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
    category_url = 'https://auto3n.ru/categories/motornye-masla-2444'

    try:
        for page in range(1, 6):  # До 5 страниц
            current_url = f"{category_url}?page={page}"
            print(f"Открываем страницу: {current_url}")
            driver.get(current_url)
            time.sleep(4)
            soup = BeautifulSoup(driver.page_source, 'lxml')

            product_cards = soup.find_all('li', attrs={'data-role': 'productDetail'})
            print(f"На странице {page} найдено товаров: {len(product_cards)}")

            if not product_cards:
                print("Нет товаров, прекращаем.")
                break

            for card in product_cards:
                link_tag = card.find('a', itemprop='url')
                if not link_tag:
                    continue
                product_url = link_tag['href']
                if not product_url.startswith('http'):
                    product_url = 'https://auto3n.ru' + product_url

                driver.get(product_url)
                time.sleep(3)
                product_soup = BeautifulSoup(driver.page_source, 'lxml')

                product = {}

                # Название
                name_elem = product_soup.find('h1', class_='bottom-margin')
                product['name'] = name_elem.text.strip() if name_elem else 'Нет названия'

                # Цена
                price_elem = product_soup.find('div', class_='price bold')
                if price_elem and price_elem.span:
                    product['price'] = price_elem.span.text.strip().replace('\xa0', '').replace(' ', '')
                else:
                    product['price'] = 'Нет цены'

                # Бренд
                brand = 'Не найден'
                for kv in product_soup.find_all('div', class_='key-value'):
                    spans = kv.find_all('span')
                    if len(spans) == 2 and spans[0].text.strip().lower() == 'бренд':
                        brand = spans[1].text.strip()
                        break
                product['brand'] = brand

                # Ссылка
                product['url'] = product_url

                products.append(product)
                print(f"Обработан товар: {product['name']}")

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

    df = pd.DataFrame({
        'Название': [p.get('name') for p in products],
        'Цена': [p.get('price') for p in products],
        'Бренд': [p.get('brand') for p in products],
        'Ссылка': [p.get('url') for p in products],
    })

    file_name = 'auto3n_oils.xlsx'
    df.to_excel(file_name, index=False)
    print(f"Данные сохранены в файл {file_name}")
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
