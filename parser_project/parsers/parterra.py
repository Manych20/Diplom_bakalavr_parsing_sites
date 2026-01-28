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
    chrome_options.add_argument('--disable-software-rasterizer')  # Отключение софтверного рендерера
    chrome_options.add_argument('--no-use-gl')  # Явное отключение OpenGL

    # Скрытие автоматизации
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )

    products = []
    base_url = 'https://parterra.ru'
    category_url = base_url + '/catalog-parts/maslo-motornoe/'

    try:
        for page in range(1, 6):  # Обрабатываем первые 5 страниц
            current_url = f"{category_url}?PAGEN_1={page}"
            print(f"Открываем страницу: {current_url}")
            driver.get(current_url)
            time.sleep(4)
            soup = BeautifulSoup(driver.page_source, 'lxml')
            
            # Находим все карточки товаров по goods-item
            product_cards = soup.find_all('div', class_='goods-item', attrs={'data-role': 'catalog.goods.item'})
            print(f"На странице {page} найдено товаров: {len(product_cards)}")

            if not product_cards:
                print(f"На странице {page} нет товаров, прекращаем обработку")
                break

            for card in product_cards:
                product = {}
                # Находим ссылку на товар внутри карточки
                link = card.find('a', class_='name')
                if not link:
                    continue
                    
                product_url = base_url + link['href']
                product['url'] = product_url

                # Переход на карточку товара
                driver.get(product_url)
                time.sleep(3)
                product_soup = BeautifulSoup(driver.page_source, 'lxml')

                # Извлекаем название
                name_elem = product_soup.find('span', class_='screen-mode').parent
                if name_elem:
                    product_name = name_elem.get_text(separator=' ', strip=True)
                    product['name'] = product_name
                else:
                    product['name'] = 'Нет названия'

                # Извлекаем цену
                price_elem = product_soup.find('span', class_='payment-block__total-price')
                if price_elem:
                    price = price_elem.get_text(strip=True).replace('₽', '').strip()
                    product['price'] = price
                else:
                    product['price'] = 'Нет цены'

                # Извлекаем бренд
                brand_elem = product_soup.find('a', class_='product-characteristics__item-description', itemprop='brand')
                product['brand'] = brand_elem.text.strip() if brand_elem else 'Не найден'

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

    excel_file = 'parterra_maslo.xlsx'
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