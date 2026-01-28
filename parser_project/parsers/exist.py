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
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def get_product_data():
    # Настройка опций Chrome
    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--headless")  # Фоновый режим

    # Инициализация драйвера
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    products = []
    base_url = 'https://www.exist.ru'
    catalog_url = base_url + '/Catalog/Goods/7/3'
    
    try:
        logger.info(f"Открываем URL: {catalog_url}")
        driver.get(catalog_url)
        time.sleep(5)  # Ожидание загрузки динамического контента
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Находим все карточки товаров
        product_cards = soup.find_all('div', class_='cell2')
        
        logger.info(f"Найдено карточек товаров: {len(product_cards)}")
        
        for card in product_cards:
            product = {}
            
            # Получаем название товара
            name_elem = card.find('div', class_='descr').find('span')
            full_name_elem = card.find('div', class_='wrap').find('p')
            
            # Используем полное наименование, если есть
            if full_name_elem:
                product['name'] = full_name_elem.text.strip()
            elif name_elem:
                product['name'] = name_elem.text.strip()
            else:
                product['name'] = ''
            
            # Получаем цену товара
            price_elem = card.find('span', class_='ucatprc')
            if price_elem:
                price = price_elem.text.strip()
                # Очищаем цену от лишних символов
                price = price.replace('₽', '').replace('&nbsp;', '').replace(' ', '').replace('от', '')
                product['price'] = price
            
            # Получаем характеристики
            characteristics = []
            
            # Состав, вязкость и объем из краткого описания
            params_elem = card.find('div', class_='desc params')
            if params_elem:
                params = params_elem.text.strip().split('\n')
                for param in params:
                    if 'л' in param:
                        characteristics.append(f"Объем: {param.strip()}")
                    elif 'W-' in param:
                        characteristics.append(f"Вязкость: {param.strip()}")
                    else:
                        characteristics.append(f"Состав: {param.strip()}")
            
            # Бренд
            brand_elem = card.find('div', class_='wrap').find('p')
            if brand_elem:
                brand = brand_elem.text.strip().split()[0]  # Первое слово в названии - обычно бренд
                characteristics.append(f"Бренд: {brand}")
            
            product['characteristics'] = characteristics
            
            # Получаем URL товара
            link_elem = card.find('a', class_='catheader')
            if link_elem and 'href' in link_elem.attrs:
                product['url'] = base_url + link_elem['href']
            
            products.append(product)
            
        return products
        
    except Exception as e:
        logger.error(f"Ошибка при получении данных: {str(e)}")
        return []
    finally:
        driver.quit()

def save_to_excel(products):
    if not products:
        logger.warning("Нет данных для сохранения")
        return None
    
    # Создаем DataFrame с нужными полями
    data = []
    
    for product in products:
        # Формируем строку с характеристиками
        chars = {}
        for char in product.get('characteristics', []):
            if ':' in char:
                key, value = char.split(':', 1)
                chars[key.strip()] = value.strip()
        
        data.append({
            'Название': product.get('name', ''),
            'Цена': product.get('price', 'Нет цены'),
            'Состав': chars.get('Состав', ''),
            'Объем': chars.get('Объем', ''),
            'Вязкость': chars.get('Вязкость', ''),
            'Бренд': chars.get('Бренд', ''),
            'Ссылка': product.get('url', 'Нет ссылки')
        })
    
    df = pd.DataFrame(data)
    
    # Сохраняем в Excel
    excel_file = 'exist_oils.xlsx'
    df.to_excel(excel_file, index=False)
    logger.info(f"Данные сохранены в файл: {excel_file}")
    
    return df

if __name__ == "__main__":
    try:
        logger.info("Запуск парсера Exist.ru...")
        products = get_product_data()
        
        if products:
            logger.info(f"Успешно собрано товаров: {len(products)}")
            df = save_to_excel(products)
            logger.info("\nПервые записи в данных:")
            logger.info(df.head())
        else:
            logger.warning("Не удалось собрать данные о товарах")
        
    except Exception as e:
        logger.error(f"Критическая ошибка в работе парсера: {str(e)}")