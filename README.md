# Учет оборудования на производстве

Проект представляет собой информационную систему для учета оборудования на производстве, включая его ремонты и списание.

## Состав проекта

### Основные модули

1. **Equipment.py** - Основной модуль для учета оборудования:
   - Просмотр списка всего оборудования
   - Добавление/редактирование/удаление оборудования
   - Отображение текущего статуса (Исправен/На ремонте/Списано)
   - Цветовая индикация статусов оборудования

2. **RepairApp.py** - Модуль учета ремонтов оборудования:
   - Ведение истории ремонтов
   - Учет стоимости ремонтов
   - Управление статусами ремонта (Завершен/В процессе/Отменен)
   - Интеграция с модулем оборудования

3. **WriteOffApp.py** - Модуль списания оборудования:
   - Оформление актов списания
   - Указание причины списания
   - Автоматическое обновление статуса оборудования
   - История списанного оборудования

### Вспомогательные файлы

4. **database.sql** - SQL-скрипты для создания структуры БД:
   - Таблицы оборудования, ремонтов и списаний
   - Связи между таблицами
   - Примеры начальных данных

5. **requirements.txt** - Список зависимостей:
   - Python 3.10+
   - PyQt6
   - psycopg2
   - Другие необходимые библиотеки

## Особенности системы

- Полноценный графический интерфейс на PyQt6
- Интеграция с PostgreSQL
- Промышленный дизайн интерфейса
- Автоматическое обновление статусов оборудования
- Поддержка каскадных операций
- Валидация вводимых данных
