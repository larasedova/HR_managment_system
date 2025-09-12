import os
from app import create_app

app = create_app()

if __name__ == '__main__':
    # Проверим пути
    print("Current working directory:", os.getcwd())
    print("Templates path:", os.path.join(os.getcwd(), 'templates'))
    print("Employees.html exists:", os.path.exists(os.path.join(os.getcwd(), 'templates', 'employees.html')))

    app.run(debug=True, host='0.0.0.0', port=5000)