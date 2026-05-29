import os
import json
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

if not url or not key:
    print("Ошибка: SUPABASE_URL или SUPABASE_KEY не найдены в .env файле.")
    exit(1)

supabase: Client = create_client(url, key)

def migrate_deleted_items():
    if os.path.exists("deleted_items.json"):
        try:
            with open("deleted_items.json", "r", encoding="utf-8") as f:
                deleted_ids = json.load(f)
                for item_id in deleted_ids:
                    try:
                        supabase.table("deleted_items").upsert({"item_id": item_id}).execute()
                    except Exception as e:
                        print(f"Ошибка миграции удаленного элемента {item_id}: {e}")
        except json.JSONDecodeError:
            print("Файл deleted_items.json пуст или поврежден.")
    else:
        print("Файл deleted_items.json не найден.")

def migrate_items():
    if os.path.exists("items.json"):
        try:
            with open("items.json", "r", encoding="utf-8") as f:
                items = json.load(f)
                for item in items:
                    item.pop("_source", None)
                    try:
                        supabase.table("items").upsert(item).execute()
                    except Exception as e:
                        print(f"Ошибка миграции элемента {item.get('id')}: {e}")
        except json.JSONDecodeError:
            print("Файл items.json пуст или поврежден.")
    else:
        print("Файл items.json не найден.")

if __name__ == "__main__":
    print("Начинаем миграцию данных в Supabase...")
    migrate_deleted_items()
    migrate_items()
    print("Миграция завершена успешно!")
