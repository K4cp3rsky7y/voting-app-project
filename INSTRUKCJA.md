# Instrukcja uruchomienia aplikacji

## Szybki start - krok po kroku

### 1. Wymagania wstępne
- **Docker Desktop** musi być zainstalowany i uruchomiony
- Sprawdź czy Docker działa: `docker ps` (powinien zwrócić listę kontenerów lub pustą listę)

### 2. Uruchomienie aplikacji

Otwórz terminal w folderze projektu i wykonaj:

```bash
cd voting-app-project
docker-compose up --build
```

Lub w trybie tła (detached):

```bash
docker-compose up --build -d
```

### 3. Sprawdzenie statusu

```bash
docker-compose ps
```

Powinieneś zobaczyć 3 kontenery:
- `voting-app` (aplikacja Flask)
- `voting-redis` (baza danych)
- `voting-rabbitmq` (kolejka wiadomości)

### 4. Dostęp do aplikacji

- **Aplikacja głosowania**: http://localhost:5000
- **RabbitMQ Management UI**: http://localhost:15672
  - Login: `admin`
  - Hasło: `admin123`

### 5. Zatrzymanie aplikacji

```bash
docker-compose down
```

Aby usunąć również dane (wolumeny):

```bash
docker-compose down -v
```

## Rozwiązywanie problemów

### Problem: Docker nie działa
```
error during connect: open //./pipe/dockerDesktopLinuxEngine
```
**Rozwiązanie**: Uruchom Docker Desktop i poczekaj aż się w pełni załaduje.

### Problem: Port już zajęty
```
Error: bind: address already in use
```
**Rozwiązanie**: 
- Zmień porty w `docker-compose.yaml` (np. 5001:5000 zamiast 5000:5000)
- Lub zatrzymaj aplikację używającą tych portów

### Problem: Kontenery nie startują
```bash
# Sprawdź logi
docker-compose logs

# Sprawdź logi konkretnego serwisu
docker-compose logs web
docker-compose logs redis
docker-compose logs rabbitmq
```

### Problem: Aplikacja nie łączy się z Redis/RabbitMQ
- Sprawdź czy wszystkie kontenery są uruchomione: `docker-compose ps`
- Sprawdź czy są w stanie "healthy": `docker-compose ps`
- Sprawdź logi: `docker-compose logs web`

## Pełna reinstalacja

Jeśli chcesz zacząć od nowa:

```bash
# Zatrzymaj i usuń wszystko
docker-compose down -v

# Usuń obrazy (opcjonalnie)
docker rmi voting-app-project-web

# Uruchom ponownie
docker-compose up --build
```

## Testowanie aplikacji

### Przez przeglądarkę
1. Otwórz http://localhost:5000
2. Kliknij przycisk "Real" lub "Barca"
3. Zobacz aktualizację wyników

### Przez API (curl)

```bash
# Sprawdź statystyki
curl http://localhost:5000/api/stats

# Głosuj na Real
curl -X POST http://localhost:5000/vote -d "vote=Real"

# Głosuj na Barca
curl -X POST http://localhost:5000/vote -d "vote=Barca"

# Reset głosów
curl -X POST http://localhost:5000/reset

# Health check
curl http://localhost:5000/health
```

## Uruchomienie bez Docker (lokalne)

Jeśli nie chcesz używać Docker:

1. **Zainstaluj zależności**:
```bash
pip install -r requirements.txt
```

2. **Uruchom Redis i RabbitMQ w Docker**:
```bash
docker run -d -p 6379:6379 redis:7-alpine
docker run -d -p 5672:5672 -p 15672:15672 -e RABBITMQ_DEFAULT_USER=admin -e RABBITMQ_DEFAULT_PASS=admin123 rabbitmq:3-management-alpine
```

3. **Ustaw zmienne środowiskowe**:
```bash
# Windows PowerShell
$env:REDIS_HOST="localhost"
$env:RABBITMQ_HOST="localhost"
$env:RABBITMQ_USER="admin"
$env:RABBITMQ_PASSWORD="admin123"
$env:VOTE_OPTION_1="Real"
$env:VOTE_OPTION_2="Barca"
$env:APP_TITLE="Real vs Barca - Głosowanie"

# Linux/Mac
export REDIS_HOST=localhost
export RABBITMQ_HOST=localhost
export RABBITMQ_USER=admin
export RABBITMQ_PASSWORD=admin123
export VOTE_OPTION_1=Real
export VOTE_OPTION_2=Barca
export APP_TITLE="Real vs Barca - Głosowanie"
```

4. **Uruchom aplikację**:
```bash
python app/main.py
```

Aplikacja będzie dostępna pod: http://localhost:5000
