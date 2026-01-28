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
    chrome_options.add_argument("--disable-dev-shm-usage")
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
    base_url = 'https://chalik.ru'
    category_url = base_url + '/catalog/masla/masla_motornye_/filter/cml2_manufacturer-is-b72a3cdc-832b-11eb-a79f-002590e06769-or-9370aa00-8336-11eb-a79f-002590e06769-or-c573e77a-6864-11eb-7f9d-002590e06769-or-11f9eba8-8327-11eb-a79f-002590e06769-or-5b069a06-7dc9-11ec-97d8-ac1f6b3a135d-or-ae8fdd0e-b4ca-11eb-9896-002590e06769/apply/'

    try:
        for page in range(1, 6):  # Обрабатываем первые 5 страниц
            current_url = f"{category_url}?PAGEN_1={page}"
            print(f"Открываем страницу: {current_url}")
            driver.get(current_url)
            time.sleep(4)
            soup = BeautifulSoup(driver.page_source, 'lxml')
            
            # Находим все карточки товаров
            product_cards = soup.find_all('div', class_='site_view_result__item__col')
            print(f"На странице {page} найдено товаров: {len(product_cards)}")

            if not product_cards:
                print(f"На странице {page} нет товаров, прекращаем обработку")
                break

            for card in product_cards:
                product = {}
                # Находим ссылку на товар внутри карточки
                link = card.find('a', class_='tile_item_wrap_link')
                if not link:
                    continue
                    
                product_url = base_url + link['href']
                product['url'] = product_url

                # Переход на карточку товара
                driver.get(product_url)
                time.sleep(10)
                product_soup = BeautifulSoup(driver.page_source, 'lxml')

                # Извлекаем название
                name_elem = product_soup.find('h1', class_='title_h3 title_card')
                if name_elem:
                    product_name = name_elem.text.strip()
                    product['name'] = product_name
                else:
                    product['name'] = 'Нет названия'

                # Извлекаем цену
                price_elem = product_soup.find('span', class_='card_offers__price__text')
                if price_elem:
                    price = price_elem.text.strip().replace('р.', '').strip()
                    product['price'] = price
                else:
                    product['price'] = 'Нет цены'

                # Извлекаем бренд
                brand = 'Не найден'
                option_blocks = product_soup.find_all('div', class_='tabs_option_block__item')
                for block in option_blocks:
                    title = block.find('div', class_='option_item_title')
                    if title and 'Бренд' in title.get_text(strip=True):
                        brand_elem = block.find('div', class_='option_item_descr')
                        if brand_elem:
                            brand = brand_elem.get_text(strip=True)
                            break
                
                product['brand'] = brand

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

    # Формируем списки для столбцов
    names = []
    prices = []
    brands = []
    urls = []

    for product in products:
        names.append(product.get('name', 'Нет названия'))
        prices.append(product.get('price', 'Нет цены'))
        brands.append(product.get('brand', 'Нет бренда'))
        urls.append(product.get('url', 'Нет ссылки'))

    # Создание DataFrame с правильным порядком
    df = pd.DataFrame({
        'Название': names,
        'Цена': prices,
        'Бренд': brands,
        'Ссылка': urls
    })

    excel_file = 'chalik_maslo.xlsx'
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