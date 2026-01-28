from bs4 import BeautifulSoup
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time

def get_product_data():
    chrome_options = Options()
    # chrome_options.add_argument("--headless=new")  # Раскомментируйте для headless-режима
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    
    # Добавляем User-Agent (современный Chrome)
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )

    products = []
    base_url = 'https://avto-fes.ru'
    category_url = base_url + '/oils_catalog'

    try:
        for page in range(1, 6):  # Обрабатываем первые 5 страниц
            current_url = f"{category_url}?page={page}"
            print(f"Открываем страницу: {current_url}")
            driver.get(current_url)
            time.sleep(4)
            soup = BeautifulSoup(driver.page_source, 'lxml')

            product_links = soup.select('a[href^="/parts/"][target="_blank"]')
            print(f"На странице {page} найдено товаров: {len(product_links)}")

            if not product_links:
                print(f"На странице {page} нет товаров, прекращаем обработку")
                break

            for link in product_links:
                product_url = base_url + link['href']
                driver.get(product_url)
                time.sleep(2)
                product_soup = BeautifulSoup(driver.page_source, 'lxml')

                product = {}

                # Название
                name_elem = product_soup.find('div', class_='goodsInfoDescr')
                product['name'] = name_elem.text.strip() if name_elem else 'Нет названия'

                # Цена
                price_elem = product_soup.find('div', class_='distrInfoPrice')
                if price_elem:
                    price_text = price_elem.get_text(strip=True)
                    price = price_text.replace('Цена', '').replace('₽', '').strip()
                    product['price'] = price
                else:
                    product['price'] = 'Нет цены'

                # Бренд
                brand_elem = product_soup.find('span', class_='article-brand brandInfoEm')
                product['brand'] = brand_elem.text.strip() if brand_elem else 'Не найден'

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

    names = []
    prices = []
    brands = []
    urls = []

    for product in products:
        names.append(product.get('name', 'Нет названия'))
        prices.append(product.get('price', 'Нет цены'))
        brands.append(product.get('brand', 'Нет бренда'))
        urls.append(product.get('url', 'Нет ссылки'))

    df = pd.DataFrame({
        'Название': names,
        'Цена': prices,
        'Бренд': brands,
        'Ссылка': urls
    })

    excel_file = 'avto_fes_oils.xlsx'
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