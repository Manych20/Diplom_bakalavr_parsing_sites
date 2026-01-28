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
    base_url = 'https://forwardauto.ru'
    category_url = base_url + '/catalog/masla_i_tekhnicheskie_zhidkosti/motornoe_maslo/'

    try:
        for page in range(1, 6):  # Обрабатываем первые 5 страниц
            current_url = f"{category_url}?PAGEN_1={page}"
            print(f"Открываем страницу: {current_url}")
            driver.get(current_url)
            time.sleep(4)
            soup = BeautifulSoup(driver.page_source, 'lxml')
            
            # Находим все карточки товаров
            product_cards = soup.find_all('div', class_='inner_wrap TYPE_1')
            print(f"На странице {page} найдено товаров: {len(product_cards)}")

            if not product_cards:
                print(f"На странице {page} нет товаров, прекращаем обработку")
                break

            for card in product_cards:
                product = {}
                # Находим ссылку на товар внутри карточки
                link = card.find('a', class_='dark_link')
                if not link:
                    continue
                    
                product_url = base_url + link['href']
                product['url'] = product_url

                # Переход на карточку товара
                driver.get(product_url)
                time.sleep(3)
                product_soup = BeautifulSoup(driver.page_source, 'lxml')

                # Извлекаем название
                name_elem = product_soup.find('h1', id='pagetitle')
                if name_elem:
                    product_name = name_elem.text.strip()
                    product['name'] = product_name
                else:
                    product['name'] = 'Нет названия'

                # Извлекаем цену
                price_elem = product_soup.find('span', class_='price_value')
                if price_elem:
                    price = price_elem.text.strip().replace(' ', '')
                    product['price'] = price
                else:
                    product['price'] = 'Нет цены'

                # Извлекаем бренд
                brand = 'Не найден'
                
                # Ищем все блоки характеристик
                option_blocks = product_soup.find_all('div', class_='properties__item')
                
                for block in option_blocks:
                    # Ищем заголовок "Бренд" в текущем блоке
                    title = block.find('div', class_='properties__title')
                    if title and 'Бренд' in title.get_text(strip=True):
                        # Если нашли заголовок "Бренд", берем значение
                        brand_elem = block.find('div', class_='properties__value')
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

    excel_file = 'forwardauto_maslo.xlsx'
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