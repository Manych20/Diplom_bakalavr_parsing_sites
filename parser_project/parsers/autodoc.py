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
    base_url = 'https://www.autodoc.ru'
    category_url = base_url + '/catalogs/universal/maslo-motornoe-780?page=goods'

    try:
        for page in range(1, 6):  # Обрабатываем первые 5 страниц
            current_url = f"{category_url}&page={page}"
            print(f"Открываем страницу: {current_url}")
            driver.get(current_url)
            time.sleep(4)  # Увеличиваем время ожидания
            
            # Прокрутка страницы для загрузки всех товаров
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            soup = BeautifulSoup(driver.page_source, 'lxml')
            
            # Находим все карточки товаров
            product_cards = soup.find_all('a', attrs={'target': '_blank', 'href': True})
            print(f"На странице {page} найдено товаров: {len(product_cards)}")

            if not product_cards:
                print(f"На странице {page} нет товаров, прекращаем обработку")
                break

            for card in product_cards:
                product = {}
                product_url = base_url + card['href']
                product['url'] = product_url

                # Переход на карточку товара
                driver.get(product_url)
                time.sleep(3)
                product_soup = BeautifulSoup(driver.page_source, 'lxml')

                # Извлекаем название
                name_elem = product_soup.find('span', class_='item right')
                if name_elem:
                    product['name'] = name_elem.text.strip()
                else:
                    product['name'] = 'Нет названия'

                # Извлекаем цену
                price_elem = product_soup.find('span', class_='price-number')
                if price_elem:
                    price = price_elem.text.strip().replace(' ', '').replace('\xa0', '').replace('от', '').replace('.00', '')
                    product['price'] = price
                else:
                    product['price'] = 'Нет цены'

                # Извлекаем бренд
                brand_elem = product_soup.find('a', href=lambda x: x and '/man/' in x)
                if brand_elem:
                    product['brand'] = brand_elem.text.strip()
                else:
                    product['brand'] = 'Не найден'

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

    # Создание DataFrame
    df = pd.DataFrame({
        'Название': names,
        'Цена': prices,
        'Бренд': brands,
        'Ссылка': urls
    })

    excel_file = 'autodoc_maslo.xlsx'
    df.to_excel(excel_file, index=False)
    print(f"Данные сохранены в файл {excel_file}")

    return df

if __name__ == "__main__":
    print("Начало работы парсера autodoc.ru...")
    products = get_product_data()
    if products:
        print(f"\nУспешно собрано {len(products)} товаров")
        df = save_to_excel(products)
        print("\nПервые 5 записей:")
        print(df.head())
    else:
        print("Не удалось собрать данные")