#!/usr/bin/env python3
"""
Скрипт для проверки состояния базы данных и миграций.
Помогает диагностировать проблемы с БД.
"""

import sys
import os
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'knowledge_base.settings')
django.setup()

from django.db import connection
from django.core.management import call_command
from django.apps import apps

def check_migrations():
    """Проверка наличия файлов миграций"""
    print("="*60)
    print("ПРОВЕРКА ФАЙЛОВ МИГРАЦИЙ")
    print("="*60)
    
    api_app = apps.get_app_config('api')
    migrations_path = os.path.join(api_app.path, 'migrations')
    
    if not os.path.exists(migrations_path):
        print(f"❌ Папка migrations не существует: {migrations_path}")
        print("   Нужно создать миграции: python manage.py makemigrations")
        return False
    else:
        print(f"✓ Папка migrations существует: {migrations_path}")
        migration_files = [f for f in os.listdir(migrations_path) if f.endswith('.py') and f != '__init__.py']
        if not migration_files:
            print("❌ Нет файлов миграций!")
            print("   Нужно создать миграции: python manage.py makemigrations")
            return False
        else:
            print(f"✓ Найдено файлов миграций: {len(migration_files)}")
            for f in migration_files:
                print(f"  - {f}")
            return True

def check_database_connection():
    """Проверка подключения к базе данных"""
    print("\n" + "="*60)
    print("ПРОВЕРКА ПОДКЛЮЧЕНИЯ К БД")
    print("="*60)
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            print(f"✓ Подключение к БД успешно")
            print(f"  Версия PostgreSQL: {version.split(',')[0]}")
            
            # Получаем имя БД
            db_name = connection.settings_dict['NAME']
            db_user = connection.settings_dict['USER']
            db_host = connection.settings_dict['HOST']
            print(f"  База данных: {db_name}")
            print(f"  Пользователь: {db_user}")
            print(f"  Хост: {db_host}")
            return True
    except Exception as e:
        print(f"❌ Ошибка подключения к БД: {e}")
        return False

def check_tables():
    """Проверка наличия таблиц в БД"""
    print("\n" + "="*60)
    print("ПРОВЕРКА ТАБЛИЦ В БД")
    print("="*60)
    
    try:
        with connection.cursor() as cursor:
            # Получаем список всех таблиц
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """)
            tables = [row[0] for row in cursor.fetchall()]
            
            if not tables:
                print("❌ В базе данных нет таблиц!")
                return False
            
            print(f"✓ Найдено таблиц: {len(tables)}")
            
            # Проверяем наличие нужных таблиц
            required_tables = ['api_knowledge', 'api_knowledgeimage', 'django_migrations']
            missing_tables = []
            
            for table in required_tables:
                if table in tables:
                    print(f"  ✓ {table}")
                else:
                    print(f"  ❌ {table} - ОТСУТСТВУЕТ")
                    missing_tables.append(table)
            
            if missing_tables:
                print(f"\n❌ Отсутствуют таблицы: {', '.join(missing_tables)}")
                return False
            else:
                print("\n✓ Все необходимые таблицы присутствуют")
                return True
                
    except Exception as e:
        print(f"❌ Ошибка при проверке таблиц: {e}")
        return False

def check_migration_status():
    """Проверка статуса миграций"""
    print("\n" + "="*60)
    print("СТАТУС МИГРАЦИЙ")
    print("="*60)
    
    try:
        from django.db.migrations.recorder import MigrationRecorder
        recorder = MigrationRecorder(connection)
        
        # Проверяем, существует ли таблица django_migrations
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'django_migrations'
                );
            """)
            exists = cursor.fetchone()[0]
            
            if not exists:
                print("❌ Таблица django_migrations не существует")
                print("   Это означает, что миграции никогда не применялись")
                return False
            
            # Получаем список примененных миграций для приложения api
            applied = recorder.applied_migrations()
            api_migrations = [m for m in applied if m[0] == 'api']
            
            if api_migrations:
                print(f"✓ Применено миграций для 'api': {len(api_migrations)}")
                for app, migration in api_migrations:
                    print(f"  - {migration}")
            else:
                print("❌ Нет примененных миграций для приложения 'api'")
                return False
                
            return True
    except Exception as e:
        print(f"❌ Ошибка при проверке статуса миграций: {e}")
        return False

def main():
    """Главная функция"""
    print("\n" + "="*60)
    print("ДИАГНОСТИКА БАЗЫ ДАННЫХ")
    print("="*60 + "\n")
    
    results = {
        'migrations_exist': check_migrations(),
        'db_connection': check_database_connection(),
        'tables_exist': check_tables(),
        'migrations_applied': check_migration_status(),
    }
    
    print("\n" + "="*60)
    print("ИТОГИ ДИАГНОСТИКИ")
    print("="*60)
    
    all_ok = all(results.values())
    
    if all_ok:
        print("\n✓ Все проверки пройдены успешно!")
        print("  База данных настроена корректно.")
    else:
        print("\n❌ Обнаружены проблемы:")
        
        if not results['migrations_exist']:
            print("\n1. ФАЙЛЫ МИГРАЦИЙ НЕ СОЗДАНЫ")
            print("   Решение: python manage.py makemigrations")
        
        if not results['db_connection']:
            print("\n2. ОШИБКА ПОДКЛЮЧЕНИЯ К БД")
            print("   Проверьте настройки в .env файле:")
            print("   - DB_NAME")
            print("   - DB_USER")
            print("   - DB_PASSWORD")
            print("   - DB_HOST")
            print("   - DB_PORT")
        
        if not results['tables_exist']:
            print("\n3. ТАБЛИЦЫ ОТСУТСТВУЮТ В БД")
            if results['migrations_exist']:
                print("   Решение: python manage.py migrate")
            else:
                print("   Решение:")
                print("   1. python manage.py makemigrations")
                print("   2. python manage.py migrate")
        
        if not results['migrations_applied']:
            print("\n4. МИГРАЦИИ НЕ ПРИМЕНЕНЫ")
            if results['migrations_exist']:
                print("   Решение: python manage.py migrate")
            else:
                print("   Решение:")
                print("   1. python manage.py makemigrations")
                print("   2. python manage.py migrate")
    
    print("\n" + "="*60 + "\n")
    
    return 0 if all_ok else 1

if __name__ == '__main__':
    sys.exit(main())


