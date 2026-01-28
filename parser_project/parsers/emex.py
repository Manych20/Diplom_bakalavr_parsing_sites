from bs4 import BeautifulSoup
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
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
    base_url = 'https://emex.ru'
    category_url = base_url + '/catalogs2/212'  # Категория моторных масел

    try:
        print(f"Открываем страницу: {category_url}")
        driver.get(category_url)
        time.sleep(5)
        
        # Обработка кнопки "Показать еще"
        while True:
            # Прокрутка вниз перед поиском кнопки
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            try:
                # Ожидаем появления кнопки и кликаем
                load_more_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button.sc-7a8fd0f9-26")))
                load_more_button.click()
                print("Кнопка нажата")
                time.sleep(3)  # Даем время для загрузки новых товаров
            except Exception:
                print("Кнопка Показать еще' не найдена")
                break
            
            # Проверяем, не зациклились ли мы (на всякий случай)
            if len(products) > 100:  # Максимум 100 товаров для примера
                print("Достигнут лимит товаров")
                break
        
        # После загрузки всех товаров собираем данные
        soup = BeautifulSoup(driver.page_source, 'lxml')
        product_cards = soup.find_all('a', class_='sc-f7cb4d56-6')
        print(f"Всего найдено товаров: {len(product_cards)}")

        for card in product_cards:
            product = {}
            try:
                # Извлекаем данные из карточки на странице категории
                product_name = card.find('div', class_='sc-f7cb4d56-5').text.strip()
                product_brand = card.find('div', class_='sc-f7cb4d56-8').text.strip()
                product_url = base_url + card['href']
                
                # Переход на карточку товара
                driver.get(product_url)
                time.sleep(2)
                product_soup = BeautifulSoup(driver.page_source, 'lxml')

                # Уточняем название из карточки товара
                name_elem = product_soup.find('h1', class_='sc-6cb21ce1-1')
                product['name'] = name_elem.text.strip() if name_elem else product_name

                # Извлекаем цену
                price_elem = product_soup.find('div', class_='sc-6cb21ce1-13')
                if price_elem:
                    price = price_elem.text.strip().replace(' ', '').replace('\xa0', '').replace('руб.', '')
                    product['price'] = price
                else:
                    product['price'] = 'Нет цены'

                # Уточняем бренд из карточки товара
                brand_elem = product_soup.find('div', class_='sc-93ed5ded-8')
                product['brand'] = brand_elem.text.strip() if brand_elem else product_brand

                product['url'] = product_url
                products.append(product)
                print(f"Обработан товар: {product.get('name')}")

                # Возвращаемся назад
                driver.back()
                time.sleep(1)
                
            except Exception as e:
                print(f"Ошибка при обработке товара: {e}")
                continue

    except Exception as e:
        print(f"Ошибка: {e}")
        return []
    finally:
        driver.quit()
    
    return products

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

    excel_file = 'emex_maslo.xlsx'
    df.to_excel(excel_file, index=False)
    print(f"Данные сохранены в файл {excel_file}")

    return df

if __name__ == "__main__":
    print("Начало работы парсера emex.ru...")
    products = get_product_data()
    if products:
        print(f"\nУспешно собрано {len(products)} товаров")
        df = save_to_excel(products)
        print("\nПервые 5 записей:")
        print(df.head())
    else:
        print("Не удалось собрать данные")