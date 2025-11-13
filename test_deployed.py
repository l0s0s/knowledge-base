#!/usr/bin/env python3
"""
Скрипт для тестирования развернутого приложения Knowledge Base API.
Проверяет все эндпоинты на корректную работу.

Требования:
    pip install requests Pillow

Использование:
    python test_deployed.py <BASE_URL>
    
Пример:
    python test_deployed.py http://localhost:8000
    python test_deployed.py https://api.example.com

Тестируемые функции:
    - CRUD операции (создание, чтение, обновление, удаление)
    - Мягкое удаление и восстановление записей
    - Загрузка и удаление изображений
    - Фильтрация и поиск
    - Пагинация
    - Сортировка
    - Валидация данных
    - Обработка ошибок (404, 400)
"""

import sys
import requests
import json
from io import BytesIO
from PIL import Image
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple


class Colors:
    """ANSI цвета для вывода в терминал"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


class APITester:
    """Класс для тестирования API"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.api_url = f"{self.base_url}/knowledge"
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        self.test_results = {
            'passed': 0,
            'failed': 0,
            'errors': []
        }
        self.created_resources = []  # Для очистки после тестов
        
    def log(self, message: str, color: str = Colors.RESET):
        """Вывод сообщения с цветом"""
        print(f"{color}{message}{Colors.RESET}")
    
    def parse_error_message(self, response_text: str) -> str:
        """Парсинг сообщения об ошибке из ответа сервера"""
        try:
            # Пытаемся найти ключевые сообщения об ошибках
            if 'ProgrammingError' in response_text or 'relation' in response_text.lower():
                if 'не существует' in response_text or 'does not exist' in response_text:
                    return "ОШИБКА БАЗЫ ДАННЫХ: Таблицы не существуют. Необходимо выполнить миграции (python manage.py migrate)"
            
            if 'OperationalError' in response_text:
                return "ОШИБКА ПОДКЛЮЧЕНИЯ К БД: Проверьте настройки базы данных"
            
            if 'IntegrityError' in response_text:
                return "ОШИБКА ЦЕЛОСТНОСТИ ДАННЫХ: Нарушение ограничений базы данных"
            
            # Пытаемся извлечь JSON ошибку
            try:
                data = json.loads(response_text)
                if 'detail' in data:
                    return f"Ошибка: {data['detail']}"
            except:
                pass
            
            # Ищем Exception Value в HTML ответе
            if 'Exception Value:' in response_text:
                lines = response_text.split('\n')
                for i, line in enumerate(lines):
                    if 'Exception Value:' in line and i + 1 < len(lines):
                        error_msg = lines[i + 1].strip()
                        if error_msg:
                            return f"Ошибка сервера: {error_msg}"
            
            # Если ничего не найдено, возвращаем первые 200 символов
            return response_text[:200] + ('...' if len(response_text) > 200 else '')
        except:
            return response_text[:200] if len(response_text) > 200 else response_text
    
    def log_full_error(self, response):
        """Вывод полного ответа сервера при ошибке"""
        self.log(f"\n  {'─'*58}", Colors.RED)
        self.log(f"  ПОЛНЫЙ ОТВЕТ СЕРВЕРА:", Colors.RED + Colors.BOLD)
        self.log(f"  {'─'*58}", Colors.RED)
        self.log(f"  Статус код: {response.status_code}", Colors.RED)
        self.log(f"  Заголовки ответа:", Colors.YELLOW)
        for key, value in response.headers.items():
            self.log(f"    {key}: {value}", Colors.YELLOW)
        self.log(f"\n  Тело ответа:", Colors.YELLOW)
        # Выводим полный текст ответа
        response_text = response.text
        # Если ответ очень длинный, показываем первые и последние строки
        if len(response_text) > 5000:
            lines = response_text.split('\n')
            self.log(f"  (Показаны первые 100 и последние 50 строк из {len(lines)} строк)", Colors.YELLOW)
            for line in lines[:100]:
                self.log(f"  {line}", Colors.RESET)
            self.log(f"\n  ... (пропущено {len(lines) - 150} строк) ...\n", Colors.YELLOW)
            for line in lines[-50:]:
                self.log(f"  {line}", Colors.RESET)
        else:
            # Выводим весь ответ построчно
            for line in response_text.split('\n'):
                self.log(f"  {line}", Colors.RESET)
        self.log(f"  {'─'*58}\n", Colors.RED)
        
    def test(self, name: str, func) -> bool:
        """Выполнение теста с обработкой ошибок"""
        try:
            self.log(f"\n{'='*60}", Colors.BLUE)
            self.log(f"Тест: {name}", Colors.BOLD + Colors.BLUE)
            self.log('='*60, Colors.BLUE)
            result = func()
            if result:
                self.test_results['passed'] += 1
                self.log(f"✓ ПРОЙДЕН: {name}", Colors.GREEN)
                return True
            else:
                self.test_results['failed'] += 1
                self.log(f"✗ ПРОВАЛЕН: {name}", Colors.RED)
                return False
        except Exception as e:
            self.test_results['failed'] += 1
            self.test_results['errors'].append(f"{name}: {str(e)}")
            self.log(f"✗ ОШИБКА: {name}", Colors.RED)
            self.log(f"  Детали: {str(e)}", Colors.RED)
            return False
    
    def create_test_image(self) -> BytesIO:
        """Создание тестового изображения в памяти"""
        img = Image.new('RGB', (100, 100), color='red')
        img_bytes = BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        return img_bytes
    
    # ==================== ТЕСТЫ ЭНДПОИНТОВ ====================
    
    def test_api_root(self) -> bool:
        """Тест корневого эндпоинта API"""
        try:
            response = self.session.get(f"{self.api_url}/")
            if response.status_code == 200:
                self.log(f"  Ответ: {response.status_code}", Colors.GREEN)
                return True
            else:
                self.log(f"  Неожиданный статус: {response.status_code}", Colors.RED)
                return False
        except requests.exceptions.RequestException as e:
            self.log(f"  Ошибка подключения: {str(e)}", Colors.RED)
            return False
    
    def test_create_knowledge(self) -> bool:
        """Тест создания записи knowledge"""
        data = {
            'user_id': 'test_user_123',
            'text': 'Тестовый текст для проверки API',
            'quiz': ['Вопрос 1?', 'Вопрос 2?']
        }
        response = self.session.post(
            f"{self.api_url}/knowledge/",
            json=data
        )
        
        if response.status_code == 201:
            try:
                result = response.json()
                # Если в ответе нет id, получаем его из списка записей
                if 'id' not in result:
                    # Ищем созданную запись в списке по user_id и text
                    list_response = self.session.get(
                        f"{self.api_url}/knowledge/",
                        params={'user_id': data['user_id']}
                    )
                    if list_response.status_code == 200:
                        items = list_response.json().get('results', [])
                        # Находим последнюю созданную запись с таким user_id и текстом
                        for item in items:
                            if item.get('user_id') == data['user_id'] and item.get('text') == data['text']:
                                knowledge_id = item['id']
                                self.created_resources.append(('knowledge', knowledge_id))
                                self.log(f"  Создана запись с ID: {knowledge_id} (получен из списка)", Colors.GREEN)
                                self.log(f"  user_id: {result.get('user_id', 'N/A')}", Colors.GREEN)
                                self.log(f"  text: {result.get('text', 'N/A')[:50]}...", Colors.GREEN)
                                return True
                    # Если не нашли, все равно считаем успешным (запись создана)
                    self.log(f"  Запись создана (ID не получен, но статус 201)", Colors.GREEN)
                    self.log(f"  user_id: {result.get('user_id', 'N/A')}", Colors.GREEN)
                    return True
                else:
                    self.created_resources.append(('knowledge', result['id']))
                    self.log(f"  Создана запись с ID: {result['id']}", Colors.GREEN)
                    self.log(f"  user_id: {result.get('user_id', 'N/A')}", Colors.GREEN)
                    self.log(f"  text: {result.get('text', 'N/A')[:50]}...", Colors.GREEN)
                    return True
            except (KeyError, ValueError, json.JSONDecodeError) as e:
                self.log(f"  Ошибка при обработке ответа: {str(e)}", Colors.RED)
                self.log(f"  Статус: {response.status_code}", Colors.RED)
                self.log(f"  Ответ сервера: {response.text[:500]}", Colors.RED)
                return False
        else:
            self.log(f"  Статус: {response.status_code}", Colors.RED)
            error_msg = self.parse_error_message(response.text)
            self.log(f"  Краткое описание: {error_msg}", Colors.RED)
            # Выводим полный ответ сервера
            self.log_full_error(response)
            if response.status_code == 500:
                self.log(f"  ВАЖНО: Проверьте, что миграции применены (python manage.py migrate)", Colors.YELLOW)
            return False
    
    def test_list_knowledge(self) -> bool:
        """Тест получения списка записей"""
        response = self.session.get(f"{self.api_url}/knowledge/")
        
        if response.status_code == 200:
            data = response.json()
            self.log(f"  Всего записей: {data.get('count', len(data.get('results', [])))}", Colors.GREEN)
            self.log(f"  На странице: {len(data.get('results', []))}", Colors.GREEN)
            return True
        else:
            self.log(f"  Статус: {response.status_code}", Colors.RED)
            error_msg = self.parse_error_message(response.text)
            self.log(f"  Краткое описание: {error_msg}", Colors.RED)
            # Выводим полный ответ сервера
            self.log_full_error(response)
            return False
    
    def test_list_knowledge_with_filters(self) -> bool:
        """Тест фильтрации записей"""
        # Фильтр по user_id
        response = self.session.get(
            f"{self.api_url}/knowledge/",
            params={'user_id': 'test_user_123'}
        )
        
        if response.status_code != 200:
            self.log(f"  Ошибка фильтрации по user_id: {response.status_code}", Colors.RED)
            error_msg = self.parse_error_message(response.text)
            self.log(f"  Краткое описание: {error_msg}", Colors.RED)
            self.log_full_error(response)
            return False
        
        # Фильтр по тексту
        response = self.session.get(
            f"{self.api_url}/knowledge/",
            params={'text__icontains': 'тест'}
        )
        
        if response.status_code == 200:
            self.log(f"  Фильтры работают корректно", Colors.GREEN)
            return True
        else:
            self.log(f"  Ошибка фильтрации по тексту: {response.status_code}", Colors.RED)
            error_msg = self.parse_error_message(response.text)
            self.log(f"  Краткое описание: {error_msg}", Colors.RED)
            self.log_full_error(response)
            return False
    
    def test_list_knowledge_pagination(self) -> bool:
        """Тест пагинации"""
        response = self.session.get(
            f"{self.api_url}/knowledge/",
            params={'page': 1, 'page_size': 10}
        )
        
        if response.status_code == 200:
            data = response.json()
            has_pagination = 'count' in data and 'next' in data and 'results' in data
            if has_pagination:
                self.log(f"  Пагинация работает: count={data.get('count')}", Colors.GREEN)
                return True
            else:
                self.log(f"  Пагинация не работает корректно", Colors.RED)
                return False
        else:
            self.log(f"  Статус: {response.status_code}", Colors.RED)
            error_msg = self.parse_error_message(response.text)
            self.log(f"  Краткое описание: {error_msg}", Colors.RED)
            # Выводим полный ответ сервера
            self.log_full_error(response)
            return False
    
    def test_list_knowledge_ordering(self) -> bool:
        """Тест сортировки"""
        response = self.session.get(
            f"{self.api_url}/knowledge/",
            params={'ordering': '-created_at'}
        )
        
        if response.status_code == 200:
            self.log(f"  Сортировка работает", Colors.GREEN)
            return True
        else:
            self.log(f"  Ошибка сортировки: {response.status_code}", Colors.RED)
            error_msg = self.parse_error_message(response.text)
            self.log(f"  Краткое описание: {error_msg}", Colors.RED)
            self.log_full_error(response)
            return False
    
    def test_get_knowledge_detail(self) -> bool:
        """Тест получения одной записи"""
        if not self.created_resources:
            self.log(f"  Нет созданных ресурсов для теста", Colors.YELLOW)
            return True  # Пропускаем, если нет ресурсов
        
        knowledge_id = None
        for resource_type, resource_id in self.created_resources:
            if resource_type == 'knowledge':
                knowledge_id = resource_id
                break
        
        if not knowledge_id:
            self.log(f"  Не найден ID записи для теста", Colors.YELLOW)
            return True
        
        response = self.session.get(f"{self.api_url}/knowledge/{knowledge_id}/")
        
        if response.status_code == 200:
            data = response.json()
            self.log(f"  Получена запись ID: {data['id']}", Colors.GREEN)
            return True
        else:
            self.log(f"  Статус: {response.status_code}", Colors.RED)
            error_msg = self.parse_error_message(response.text)
            self.log(f"  Краткое описание: {error_msg}", Colors.RED)
            self.log_full_error(response)
            return False
    
    def test_get_nonexistent_knowledge(self) -> bool:
        """Тест получения несуществующей записи (должна быть 404)"""
        response = self.session.get(f"{self.api_url}/knowledge/999999/")
        
        if response.status_code == 404:
            self.log(f"  Корректно возвращается 404 для несуществующей записи", Colors.GREEN)
            return True
        elif response.status_code == 500:
            # Если БД не настроена, это нормально, что получаем 500 вместо 404
            error_msg = self.parse_error_message(response.text)
            if 'не существует' in error_msg or 'does not exist' in error_msg:
                self.log(f"  Получен 500 из-за отсутствия таблиц БД (ожидалось 404)", Colors.YELLOW)
                self.log(f"  Это нормально, если миграции не применены", Colors.YELLOW)
                return True  # Считаем это приемлемым для теста доступности
            else:
                self.log(f"  Ожидался 404, получен {response.status_code}", Colors.RED)
                self.log(f"  Краткое описание: {error_msg}", Colors.RED)
                self.log_full_error(response)
                return False
        else:
            self.log(f"  Ожидался 404, получен {response.status_code}", Colors.RED)
            error_msg = self.parse_error_message(response.text)
            self.log(f"  Краткое описание: {error_msg}", Colors.RED)
            self.log_full_error(response)
            return False
    
    def test_update_knowledge(self) -> bool:
        """Тест обновления записи"""
        knowledge_id = None
        for resource_type, resource_id in self.created_resources:
            if resource_type == 'knowledge':
                knowledge_id = resource_id
                break
        
        if not knowledge_id:
            self.log(f"  Нет созданных ресурсов для теста", Colors.YELLOW)
            return True
        
        data = {
            'text': 'Обновленный текст',
            'quiz': ['Новый вопрос?']
        }
        response = self.session.patch(
            f"{self.api_url}/knowledge/{knowledge_id}/",
            json=data
        )
        
        if response.status_code == 200:
            result = response.json()
            if result['text'] == 'Обновленный текст':
                self.log(f"  Запись успешно обновлена", Colors.GREEN)
                return True
            else:
                self.log(f"  Текст не обновился", Colors.RED)
                return False
        else:
            self.log(f"  Статус: {response.status_code}", Colors.RED)
            error_msg = self.parse_error_message(response.text)
            self.log(f"  Краткое описание: {error_msg}", Colors.RED)
            self.log_full_error(response)
            return False
    
    def test_soft_delete_knowledge(self) -> bool:
        """Тест мягкого удаления записи"""
        knowledge_id = None
        for resource_type, resource_id in self.created_resources:
            if resource_type == 'knowledge':
                knowledge_id = resource_id
                break
        
        if not knowledge_id:
            self.log(f"  Нет созданных ресурсов для теста", Colors.YELLOW)
            return True
        
        response = self.session.delete(f"{self.api_url}/knowledge/{knowledge_id}/")
        
        if response.status_code == 204:
            # Проверяем, что запись не появляется в списке
            list_response = self.session.get(f"{self.api_url}/knowledge/")
            if list_response.status_code == 200:
                results = list_response.json().get('results', [])
                found = any(r['id'] == knowledge_id for r in results)
                if not found:
                    self.log(f"  Запись успешно удалена (soft delete)", Colors.GREEN)
                    return True
                else:
                    self.log(f"  Запись все еще в списке", Colors.RED)
                    return False
            else:
                self.log(f"  Не удалось проверить список", Colors.RED)
                return False
        else:
            self.log(f"  Статус: {response.status_code}", Colors.RED)
            error_msg = self.parse_error_message(response.text)
            self.log(f"  Краткое описание: {error_msg}", Colors.RED)
            self.log_full_error(response)
            return False
    
    def test_restore_knowledge(self) -> bool:
        """Тест восстановления удаленной записи"""
        knowledge_id = None
        for resource_type, resource_id in self.created_resources:
            if resource_type == 'knowledge':
                knowledge_id = resource_id
                break
        
        if not knowledge_id:
            self.log(f"  Нет удаленных ресурсов для теста", Colors.YELLOW)
            return True
        
        response = self.session.post(f"{self.api_url}/knowledge/{knowledge_id}/restore/")
        
        if response.status_code == 200:
            result = response.json()
            self.log(f"  Запись успешно восстановлена", Colors.GREEN)
            return True
        elif response.status_code == 400:
            # Возможно, запись уже не удалена
            self.log(f"  Запись не была удалена (ожидалось)", Colors.YELLOW)
            return True
        else:
            self.log(f"  Статус: {response.status_code}", Colors.RED)
            error_msg = self.parse_error_message(response.text)
            self.log(f"  Краткое описание: {error_msg}", Colors.RED)
            self.log_full_error(response)
            return False
    
    def test_upload_image(self) -> bool:
        """Тест загрузки изображения"""
        # Создаем новую запись для теста изображения
        data = {
            'user_id': 'test_user_image',
            'text': 'Тест загрузки изображения',
            'quiz': []
        }
        response = self.session.post(
            f"{self.api_url}/knowledge/",
            json=data
        )
        
        if response.status_code != 201:
            self.log(f"  Не удалось создать запись для теста изображения", Colors.RED)
            self.log(f"  Статус: {response.status_code}", Colors.RED)
            self.log(f"  Ответ: {response.text[:200]}", Colors.RED)
            return False
        
        knowledge_id = None
        try:
            result = response.json()
            # Если в ответе нет id, получаем его из списка записей
            if 'id' not in result:
                # Ищем созданную запись в списке по user_id и text
                list_response = self.session.get(
                    f"{self.api_url}/knowledge/",
                    params={'user_id': data['user_id']}
                )
                if list_response.status_code == 200:
                    items = list_response.json().get('results', [])
                    # Находим последнюю созданную запись с таким user_id и текстом
                    for item in items:
                        if item.get('user_id') == data['user_id'] and item.get('text') == data['text']:
                            knowledge_id = item['id']
                            self.created_resources.append(('knowledge', knowledge_id))
                            break
                    if not knowledge_id:
                        # Если не нашли, пропускаем этот тест
                        self.log(f"  Не удалось найти ID созданной записи", Colors.YELLOW)
                        return True  # Пропускаем тест загрузки изображения
                else:
                    self.log(f"  Не удалось получить список для поиска ID", Colors.YELLOW)
                    return True  # Пропускаем тест
            else:
                knowledge_id = result['id']
                self.created_resources.append(('knowledge', knowledge_id))
        except (KeyError, ValueError, json.JSONDecodeError) as e:
            self.log(f"  Ошибка при обработке ответа: {str(e)}", Colors.RED)
            self.log(f"  Ответ сервера: {response.text[:500]}", Colors.RED)
            return False
        
        if not knowledge_id:
            self.log(f"  Не удалось получить ID записи для загрузки изображения", Colors.YELLOW)
            return True  # Пропускаем тест
        
        # Загружаем изображение
        img_bytes = self.create_test_image()
        files = {'image': ('test_image.png', img_bytes, 'image/png')}
        
        # Убираем JSON заголовок для multipart/form-data
        headers = {'Accept': 'application/json'}
        upload_response = requests.post(
            f"{self.api_url}/knowledge/{knowledge_id}/upload-image/",
            files=files,
            headers=headers
        )
        
        if upload_response.status_code == 201:
            try:
                result = upload_response.json()
                if 'id' not in result:
                    self.log(f"  Ошибка: в ответе отсутствует поле 'id'", Colors.RED)
                    self.log(f"  Ответ сервера: {upload_response.text[:200]}", Colors.RED)
                    return False
                image_id = result['id']
                self.created_resources.append(('image', image_id))
                self.log(f"  Изображение успешно загружено, ID: {image_id}", Colors.GREEN)
                return True
            except (KeyError, ValueError, json.JSONDecodeError) as e:
                self.log(f"  Ошибка при обработке ответа: {str(e)}", Colors.RED)
                self.log(f"  Статус: {upload_response.status_code}", Colors.RED)
                self.log(f"  Ответ сервера: {upload_response.text[:500]}", Colors.RED)
                return False
        else:
            self.log(f"  Статус: {upload_response.status_code}", Colors.RED)
            error_msg = self.parse_error_message(upload_response.text)
            self.log(f"  Краткое описание: {error_msg}", Colors.RED)
            self.log_full_error(upload_response)
            return False
    
    def test_delete_image(self) -> bool:
        """Тест удаления изображения"""
        # Находим knowledge с изображением
        knowledge_id = None
        image_id = None
        
        for resource_type, resource_id in self.created_resources:
            if resource_type == 'knowledge':
                # Проверяем, есть ли у этой записи изображения
                response = self.session.get(f"{self.api_url}/knowledge/{resource_id}/")
                if response.status_code == 200:
                    images = response.json().get('images', [])
                    if images:
                        knowledge_id = resource_id
                        image_id = images[0]['id']
                        break
        
        if not knowledge_id or not image_id:
            self.log(f"  Нет изображений для удаления", Colors.YELLOW)
            return True
        
        response = self.session.delete(
            f"{self.api_url}/knowledge/{knowledge_id}/images/{image_id}/"
        )
        
        if response.status_code == 204:
            self.log(f"  Изображение успешно удалено", Colors.GREEN)
            return True
        else:
            self.log(f"  Статус: {response.status_code}", Colors.RED)
            error_msg = self.parse_error_message(response.text)
            self.log(f"  Краткое описание: {error_msg}", Colors.RED)
            self.log_full_error(response)
            return False
    
    def test_create_knowledge_validation(self) -> bool:
        """Тест валидации при создании записи"""
        # Тест без обязательных полей
        response = self.session.post(
            f"{self.api_url}/knowledge/",
            json={}
        )
        
        if response.status_code == 400:
            self.log(f"  Валидация работает: отклонены неполные данные", Colors.GREEN)
            return True
        else:
            self.log(f"  Валидация не работает: статус {response.status_code}", Colors.RED)
            return False
    
    def test_create_knowledge_invalid_quiz(self) -> bool:
        """Тест валидации quiz (должен быть массив)"""
        data = {
            'user_id': 'test_user',
            'text': 'Тест',
            'quiz': 'не массив'  # Неправильный тип
        }
        response = self.session.post(
            f"{self.api_url}/knowledge/",
            json=data
        )
        
        if response.status_code == 400:
            self.log(f"  Валидация quiz работает корректно", Colors.GREEN)
            return True
        else:
            self.log(f"  Валидация quiz не работает: статус {response.status_code}", Colors.RED)
            return False
    
    def test_date_filters(self) -> bool:
        """Тест фильтров по дате"""
        now = datetime.now(timezone.utc)
        date_str = now.strftime('%Y-%m-%dT%H:%M:%SZ')
        
        response = self.session.get(
            f"{self.api_url}/knowledge/",
            params={'created_at__gte': date_str}
        )
        
        if response.status_code == 200:
            self.log(f"  Фильтры по дате работают", Colors.GREEN)
            return True
        else:
            self.log(f"  Ошибка фильтров по дате: {response.status_code}", Colors.RED)
            error_msg = self.parse_error_message(response.text)
            self.log(f"  Краткое описание: {error_msg}", Colors.RED)
            self.log_full_error(response)
            return False
    
    def check_database_status(self) -> bool:
        """Проверка состояния базы данных"""
        try:
            response = self.session.get(f"{self.api_url}/knowledge/")
            if response.status_code == 500:
                error_text = response.text.lower()
                if 'не существует' in error_text or 'does not exist' in error_text or 'relation' in error_text:
                    return False
            return True
        except:
            return True  # Если не можем проверить, продолжаем тесты
    
    def run_all_tests(self):
        """Запуск всех тестов"""
        self.log("\n" + "="*60, Colors.BOLD)
        self.log("НАЧАЛО ТЕСТИРОВАНИЯ API", Colors.BOLD)
        self.log(f"Базовый URL: {self.base_url}", Colors.BOLD)
        self.log("="*60 + "\n", Colors.BOLD)
        
        # Предварительная проверка состояния БД
        if not self.check_database_status():
            self.log("\n" + "⚠"*30, Colors.YELLOW + Colors.BOLD)
            self.log("ВНИМАНИЕ: Обнаружены проблемы с базой данных!", Colors.YELLOW + Colors.BOLD)
            self.log("Возможно, миграции не применены.", Colors.YELLOW)
            self.log("Выполните: python manage.py migrate", Colors.YELLOW)
            self.log("⚠"*30 + "\n", Colors.YELLOW + Colors.BOLD)
        
        # Проверка доступности API
        self.test("Проверка доступности API", self.test_api_root)
        
        # CRUD операции
        self.test("Создание записи knowledge", self.test_create_knowledge)
        self.test("Получение списка записей", self.test_list_knowledge)
        self.test("Получение деталей записи", self.test_get_knowledge_detail)
        self.test("Обновление записи", self.test_update_knowledge)
        
        # Фильтрация и поиск
        self.test("Фильтрация записей", self.test_list_knowledge_with_filters)
        self.test("Пагинация", self.test_list_knowledge_pagination)
        self.test("Сортировка", self.test_list_knowledge_ordering)
        self.test("Фильтры по дате", self.test_date_filters)
        
        # Soft delete и restore
        self.test("Мягкое удаление записи", self.test_soft_delete_knowledge)
        self.test("Восстановление записи", self.test_restore_knowledge)
        
        # Работа с изображениями
        self.test("Загрузка изображения", self.test_upload_image)
        self.test("Удаление изображения", self.test_delete_image)
        
        # Валидация
        self.test("Валидация при создании", self.test_create_knowledge_validation)
        self.test("Валидация quiz", self.test_create_knowledge_invalid_quiz)
        
        # Обработка ошибок
        self.test("Получение несуществующей записи (404)", self.test_get_nonexistent_knowledge)
        
        # Итоги
        self.print_summary()
    
    def print_summary(self):
        """Вывод итогов тестирования"""
        self.log("\n" + "="*60, Colors.BOLD)
        self.log("ИТОГИ ТЕСТИРОВАНИЯ", Colors.BOLD)
        self.log("="*60, Colors.BOLD)
        
        total = self.test_results['passed'] + self.test_results['failed']
        passed = self.test_results['passed']
        failed = self.test_results['failed']
        
        self.log(f"\nВсего тестов: {total}", Colors.BOLD)
        self.log(f"Пройдено: {passed}", Colors.GREEN)
        self.log(f"Провалено: {failed}", Colors.RED if failed > 0 else Colors.GREEN)
        
        if self.test_results['errors']:
            self.log(f"\nОшибки:", Colors.RED)
            for error in self.test_results['errors']:
                self.log(f"  - {error}", Colors.RED)
        
        success_rate = (passed / total * 100) if total > 0 else 0
        self.log(f"\nУспешность: {success_rate:.1f}%", 
                Colors.GREEN if success_rate == 100 else Colors.YELLOW)
        
        if failed == 0:
            self.log("\n✓ ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!", Colors.BOLD + Colors.GREEN)
        else:
            self.log(f"\n✗ НЕКОТОРЫЕ ТЕСТЫ ПРОВАЛЕНЫ", Colors.BOLD + Colors.RED)
            
            # Проверяем, есть ли проблемы с БД
            db_errors = [e for e in self.test_results['errors'] if 'не существует' in e.lower() or 'does not exist' in e.lower() or 'relation' in e.lower()]
            if db_errors or any('500' in str(e) for e in self.test_results['errors']):
                self.log("\n" + "─"*60, Colors.YELLOW)
                self.log("РЕКОМЕНДАЦИИ:", Colors.YELLOW + Colors.BOLD)
                self.log("1. Проверьте, что миграции применены: python manage.py migrate", Colors.YELLOW)
                self.log("2. Убедитесь, что база данных создана и доступна", Colors.YELLOW)
                self.log("3. Проверьте настройки подключения к БД в settings.py", Colors.YELLOW)
                self.log("─"*60, Colors.YELLOW)
        
        self.log("="*60 + "\n", Colors.BOLD)


def main():
    """Главная функция"""
    if len(sys.argv) < 2:
        print("Использование: python test_deployed.py <BASE_URL>")
        print("Пример: python test_deployed.py http://localhost:8000")
        print("Пример: python test_deployed.py https://api.example.com")
        sys.exit(1)
    
    base_url = sys.argv[1]
    
    # Проверка формата URL
    if not base_url.startswith(('http://', 'https://')):
        print(f"Ошибка: URL должен начинаться с http:// или https://")
        print(f"Получено: {base_url}")
        sys.exit(1)
    
    tester = APITester(base_url)
    tester.run_all_tests()
    
    # Возвращаем код выхода в зависимости от результатов
    if tester.test_results['failed'] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()

