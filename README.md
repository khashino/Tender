# Django Multi-Application Project

This project contains two separate Django applications with login and registration functionality.

## Setup Instructions

1. Create a virtual environment:
```bash
python -m venv venv
```

2. Activate the virtual environment:
- Windows:
```bash
.\venv\Scripts\activate
```
- Linux/Mac:
```bash
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run migrations:
```bash
python manage.py migrate
```

5. Create a superuser:
```bash
python manage.py createsuperuser
```

6. Run the development server:
```bash
python manage.py runserver
```

The applications will be available at:
- App1: http://localhost:8000/app1/
- App2: http://localhost:8000/app2/ 




python manage.py test_oracle --query "SELECT * FROM your_table WHERE rownum <= 10"