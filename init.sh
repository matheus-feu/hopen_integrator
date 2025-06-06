#!/bin/bash

echo "Verificando e criando o banco de dados..."
PGPASSWORD=$POSTGRES_PASSWORD psql -h $POSTGRES_HOST -U $POSTGRES_USER -p $POSTGRES_PORT -c "SELECT 1 FROM pg_database WHERE datname = '$POSTGRES_NAME';" | grep -q 1 || \
PGPASSWORD=$POSTGRES_PASSWORD psql -h $POSTGRES_HOST -U $POSTGRES_USER -p $POSTGRES_PORT -c "CREATE DATABASE $POSTGRES_NAME;"

# Cria as migrações
echo "Criando as migrações..."
python manage.py makemigrations

# Roda as migrações
echo "Rodando as migrações..."
python manage.py migrate

# Cria o superusuário automaticamente
echo "Criando superusuário..."
python manage.py shell <<EOF
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin')
EOF

# Inicia o servidor
echo "Iniciando o servidor..."
exec python manage.py runserver 0.0.0.0:8000