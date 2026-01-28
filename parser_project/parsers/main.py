import importlib

# Меню выбора парсера
def show_menu():
    print("\n" + "="*40)
    print("Выберите сайт для парсинга:")
    print("1. Колеса даром")
    print("2. EMEX")
    print("3. Шинторг")
    print("4. Партерра")
    print("5. Чалик")
    print("6. Форвард авто")
    print("7. AVTOALL")
    print("0. Выход")
    print("="*40)

# Запуск парсера
def run_parser(choice):
    # Сопоставляем номер с названием файла
    parsers = {
        '1': 'kolesa_darom',
        '2': 'emex',
        '3': 'shintorg',
        '4': 'parterra',
        '5': 'chalik',
        '6': 'forwardauto',
        '7': 'avtoall'
    }
    
    if choice in parsers:
        try:
            # Импортируем нужный парсер
            module = importlib.import_module(parsers[choice])
            
            # Запускаем парсинг
            print(f"\nЗапускаю парсер для {parsers[choice]}...")
            products = module.get_product_data()
            
            # Сохраняем в Excel
            if products:
                module.save_to_excel(products)
                print(f"Готово! Сохранено {len(products)} товаров")
            else:
                print("Не удалось получить данные")
                
        except ImportError:
            print("Файл парсера не найден!")
        except Exception as e:
            print(f"Ошибка: {e}")
        
        input("\nНажмите Enter чтобы продолжить...")

# Основная программа
def main():
    while True:
        show_menu()
        choice = input("Ваш выбор (0-7): ")
        
        if choice == '0':
            print("Выход из программы")
            break
        elif choice in ['1', '2', '3', '4', '5', '6', '7']:
            run_parser(choice)
        else:
            print("Ошибка: введите число от 0 до 7")

if __name__ == "__main__":
    main()