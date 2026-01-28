from bs4 import BeautifulSoup
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time

def get_product_data():
    chrome_options = Options()
    # Режим и размеры
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--window-size=1920,1080")

    # Производительность
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-gpu")

    # Скрытие автоматизации
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )

    products = []
    base_url = 'https://krasnodar.kolesa-darom.ru'
    category_url = base_url + '/catalog/avto/avtomasla-i-zhidkosti/motornye-masla/'

    try:
        for page in range(1, 6):  # Обрабатываем первые 5 страниц
            current_url = f"{category_url}?PAGEN_1={page}"
            print(f"Открываем страницу: {current_url}")
            driver.get(current_url)
            time.sleep(4)
            soup = BeautifulSoup(driver.page_source, 'lxml')
            
            # Находим все карточки товаров по product-card__inner
            product_cards = soup.find_all('div', class_='product-card__inner')
            print(f"На странице {page} найдено товаров: {len(product_cards)}")

            if not product_cards:
                print(f"На странице {page} нет товаров, прекращаем обработку")
                break

            for card in product_cards:
                product = {}
                # Находим ссылку на товар внутри карточки
                link = card.find('a', class_='product-card-properties__main')
                if not link:
                    continue
                    
                product_url = base_url + link['href']
                product['url'] = product_url

                # Переход на карточку товара
                driver.get(product_url)
                time.sleep(3)
                product_soup = BeautifulSoup(driver.page_source, 'lxml')

                # Извлекаем название
                name_elem = product_soup.find('h1', {'itemprop': 'name', 'class': 'product-information__title'})
                if name_elem:
                    product_name = name_elem.text.strip().replace('в Краснодаре', '').strip()
                    product['name'] = product_name
                else:
                    product['name'] = 'Нет названия'

                # Извлекаем цену
                price_elem = product_soup.find('span', {'data-product-main-price': '', 'class': 'product-price-summ'})
                if price_elem:
                    price = price_elem.text.strip().replace(' ', '').replace('\xa0', '')
                    product['price'] = price
                else:
                    product['price'] = 'Нет цены'

                # Извлекаем бренд
                brand_elem = product_soup.select_one('span.dots-leaders-item__right a[href*="/catalog/"]')
                if brand_elem:
                    product['brand'] = brand_elem.text.strip() 
                else:  
                    product['brand'] = 'Нет бренда'

                products.append(product)
                print(f"Обработан товар: {product.get('name')}")

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

    excel_file = 'kolesa_darom_maslo.xlsx'
    df.to_excel(excel_file, index=False)
    print(f"Данные сохранены в файл {excel_file}")

    return df

# if __name__ == "__main__":
#     print("Начало работы парсера...")
#     products = get_product_data()
#     if products:
#         print(f"\nУспешно собрано {len(products)} товаров")
#         df = save_to_excel(products)
#         print("\nПервые 5 записей:")
#         print(df.head())
#     else:
#         print("Не удалось собрать данные")