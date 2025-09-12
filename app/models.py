from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Position(db.Model):
    """Модель должностей"""
    __tablename__ = 'positions'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    level = db.Column(db.String(50), nullable=False)

    # Связь с сотрудниками - исправлено
    employees = db.relationship('Employee', backref='position_rel', lazy=True)

    def __repr__(self):
        return f'<Position {self.title}>'


class Employee(db.Model):
    """Модель сотрудников с самоссылающейся связью для начальников"""
    __tablename__ = 'employees'

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    middle_name = db.Column(db.String(50), nullable=True)

    # Внешний ключ для должности
    position_id = db.Column(db.Integer, db.ForeignKey('positions.id'), nullable=False)

    hire_date = db.Column(db.Date, nullable=False)
    salary = db.Column(db.Numeric(10, 2), nullable=False)

    # Внешний ключ для начальника (самоссылающаяся связь)
    manager_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=True)

    # Связи - исправлено для избежания конфликтов
    position = db.relationship('Position', backref='employee_positions', foreign_keys=[position_id])

    # Связь для подчиненных
    subordinates = db.relationship(
        'Employee',
        backref=db.backref('manager', remote_side=[id]),
        foreign_keys=[manager_id],
        lazy=True
    )

    @property
    def full_name(self):
        """Полное ФИО сотрудника"""
        names = [self.last_name, self.first_name]
        if self.middle_name:
            names.append(self.middle_name)
        return ' '.join(names)

    @property
    def manager_name(self):
        """Имя начальника"""
        if self.manager:
            return self.manager.full_name
        return 'Нет начальника'

    def __repr__(self):
        return f'<Employee {self.full_name}>'