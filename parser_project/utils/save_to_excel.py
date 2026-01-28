import pandas as pd
import os

def save_to_excel(data: list, filename: str, sheet_name: str):
    df = pd.DataFrame(data)
    filepath = os.path.join('data', filename)
    with pd.ExcelWriter(filepath, engine='openpyxl', mode='a' if os.path.exists(filepath) else 'w') as writer:
        df.to_excel(writer, sheet_name=sheet_name, index=False)
    print(f"✅ Данные сохранены в файл {filepath}, вкладка {sheet_name}")