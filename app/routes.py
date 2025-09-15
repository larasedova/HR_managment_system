from flask import Blueprint, render_template, request, redirect, url_for, flash
from sqlalchemy import or_
from app.models import db, Employee, Position
import os

# Сначала определяем blueprint
main_bp = Blueprint('main_bp', __name__)


# Затем определяем маршруты
@main_bp.route('/')
def index():
    """Главная страница со списком сотрудников"""
    try:
        # Получение параметров сортировки
        sort_by = request.args.get('sort_by', 'id')
        order = request.args.get('order', 'asc')

        # Валидация параметров сортировки
        valid_sort_columns = ['id', 'first_name', 'last_name', 'hire_date', 'salary']
        if sort_by not in valid_sort_columns:
            sort_by = 'id'

        # Построение запроса с сортировкой
        query = Employee.query

        # Поиск по ФИО
        search_query = request.args.get('search', '')
        if search_query:
            search_pattern = f'%{search_query}%'
            query = query.filter(
                or_(
                    Employee.first_name.ilike(search_pattern),
                    Employee.last_name.ilike(search_pattern),
                    Employee.middle_name.ilike(search_pattern)
                )
            )

        # Применение сортировки
        if order == 'desc':
            query = query.order_by(getattr(Employee, sort_by).desc())
        else:
            query = query.order_by(getattr(Employee, sort_by).asc())

        # Пагинация
        page = request.args.get('page', 1, type=int)
        per_page = 50

        employees = query.paginate(page=page, per_page=per_page, error_out=False)

        return render_template('employees.html',
                               employees=employees,
                               sort_by=sort_by,
                               order=order,
                               search_query=search_query)

    except Exception as e:
        flash(f'Ошибка при загрузке данных: {str(e)}', 'error')
        return render_template('employees.html',
                               employees=None,
                               sort_by='id',
                               order='asc',
                               search_query='')


@main_bp.route('/update_manager/<int:employee_id>', methods=['GET', 'POST'])
def update_manager(employee_id):
    """Обновление начальника сотрудника"""
    print(f"DEBUG: Update manager called for employee_id: {employee_id}")
    print(f"DEBUG: Request method: {request.method}")

    try:
        employee = Employee.query.get_or_404(employee_id)
        print(f"DEBUG: Employee found: {employee.full_name}")
        print(f"DEBUG: Current manager: {employee.manager_id}")

        if request.method == 'POST':
            print(f"DEBUG: POST data: {dict(request.form)}")

            # Получаем ID нового начальника из формы
            new_manager_id = request.form.get('manager_id')
            print(f"DEBUG: New manager ID from form: '{new_manager_id}' (type: {type(new_manager_id)})")

            # Проверяем, не пустое ли значение
            if new_manager_id == '' or new_manager_id is None:
                new_manager_id = None
                print("DEBUG: Setting manager to None")
            else:
                try:
                    new_manager_id = int(new_manager_id)
                    print(f"DEBUG: Converted to int: {new_manager_id}")

                    # Проверка: нельзя назначить себя своим начальником
                    if new_manager_id == employee.id:
                        flash('Сотрудник не может быть своим начальником', 'error')
                        return redirect(url_for('main_bp.update_manager', employee_id=employee_id))

                    # Проверка на циклические ссылки
                    current_manager = Employee.query.get(new_manager_id)
                    if current_manager:
                        print(f"DEBUG: New manager found: {current_manager.full_name}")
                        # Проверяем всю цепочку начальников на цикличность
                        checked_managers = set()
                        temp_manager = current_manager
                        while temp_manager and temp_manager.manager_id:
                            if temp_manager.manager_id == employee.id:
                                flash('Обнаружена циклическая ссылка в иерархии', 'error')
                                return redirect(url_for('main_bp.update_manager', employee_id=employee_id))
                            if temp_manager.id in checked_managers:
                                break  # Предотвращаем бесконечный цикл
                            checked_managers.add(temp_manager.id)
                            temp_manager = Employee.query.get(temp_manager.manager_id)
                    else:
                        print(f"DEBUG: Manager with ID {new_manager_id} not found!")
                        flash('Указанный начальник не найден', 'error')
                        return redirect(url_for('main_bp.update_manager', employee_id=employee_id))

                except ValueError:
                    print("DEBUG: ValueError when converting manager_id to int")
                    flash('Некорректный ID начальника', 'error')
                    return redirect(url_for('main_bp.update_manager', employee_id=employee_id))

            # Обновляем начальника
            print(f"DEBUG: Setting manager_id from {employee.manager_id} to {new_manager_id}")
            employee.manager_id = new_manager_id

            try:
                db.session.commit()
                print("DEBUG: Database commit successful")
                flash('Начальник успешно обновлен', 'success')
                return redirect(url_for('main_bp.index'))
            except Exception as db_error:
                db.session.rollback()
                print(f"DEBUG: Database error: {str(db_error)}")
                flash(f'Ошибка базы данных: {str(db_error)}', 'error')
                return redirect(url_for('main_bp.update_manager', employee_id=employee_id))

        # GET запрос - показать форму
        all_employees = Employee.query.filter(Employee.id != employee_id).all()
        print(f"DEBUG: Found {len(all_employees)} possible managers")

        return render_template('edit_manager.html',
                               employee=employee,
                               all_employees=all_employees)

    except Exception as e:
        db.session.rollback()
        print(f"DEBUG: General error: {str(e)}")
        flash(f'Ошибка при обновлении начальника: {str(e)}', 'error')
        return redirect(url_for('main_bp.index'))


@main_bp.errorhandler(404)
def not_found_error(error):
    flash('Страница не найдена', 'error')
    return redirect(url_for('main_bp.index'))


@main_bp.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    flash('Внутренняя ошибка сервера', 'error')
    return redirect(url_for('main_bp.index'))

