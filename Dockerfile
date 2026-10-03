# Image Python légère
FROM python:3.12-slim

WORKDIR /app

# Les dépendances d'abord : Docker garde cette couche en cache tant que requirements.txt ne change pas
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Puis le code de l'application uniquement (pas les tests, ni les données d'exemple, ni .env)
COPY src/ ./src/

EXPOSE 8000

# La clé API n'est PAS dans l'image : elle est fournie au lancement avec --env-file .env
CMD ["uvicorn", "api:app", "--app-dir", "src", "--host", "0.0.0.0", "--port", "8000"]