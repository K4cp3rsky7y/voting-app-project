# Real vs Barca - Aplikacja Głosowania

Aplikacja do głosowania zbudowana z wykorzystaniem Flask, Redis i RabbitMQ. Projekt zaliczeniowy z przedmiotu "Projektowanie aplikacji internetowych".

## 📋 Opis projektu

Aplikacja umożliwia głosowanie na lepszy klub piłkarski: Real Madrid czy FC Barcelona. Aplikacja wykorzystuje architekturę mikroserwisów z kontenerami Docker, zapewniając skalowalność i niezawodność.

## 🚀 Funkcjonalności

- ✅ Głosowanie w czasie rzeczywistym
- ✅ Wyświetlanie wyników z wizualizacją procentową
- ✅ Asynchroniczne przetwarzanie głosów przez RabbitMQ
- ✅ Przechowywanie danych w Redis
- ✅ RESTful API do pobierania statystyk
- ✅ Health check endpoint
- ✅ Responsywny interfejs użytkownika
- ✅ Auto-odświeżanie wyników

## 🛠️ Technologie

- **Backend**: Python 3.11, Flask 3.0
- **Baza danych**: Redis 7
- **Kolejka wiadomości**: RabbitMQ 3
- **Konteneryzacja**: Docker, Docker Compose
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)

## 📁 Struktura projektu

```
voting-app-project/
├── app/
│   ├── __init__.py
│   ├── main.py              # Główna aplikacja Flask
│   ├── worker.py            # Worker do przetwarzania wiadomości z RabbitMQ
│   ├── templates/
│   │   └── index.html       # Szablon strony głównej
│   └── static/
│       └── style.css        # Style CSS
├── Dockerfile                # Konfiguracja obrazu Docker
├── docker-compose.yaml      # Konfiguracja orkiestracji kontenerów
├── requirements.txt         # Zależności Pythona
├── .env.example            # Przykładowy plik zmiennych środowiskowych
├── .gitignore              # Pliki ignorowane przez Git
└── README.md               # Dokumentacja projektu
```

## 🔧 Instalacja i uruchomienie

### Wymagania wstępne

- Docker Desktop (lub Docker + Docker Compose)
- Git (opcjonalnie)

### Szybki start

1. **Sklonuj repozytorium** (lub pobierz pliki projektu):
   ```bash
   git clone <url-repozytorium>
   cd voting-app-project
   ```

2. **Uruchom aplikację za pomocą Docker Compose**:
   ```bash
   docker-compose up --build
   ```

3. **Otwórz przeglądarkę** i przejdź do:
   ```
   http://localhost:5000
   ```

### Uruchomienie bez Docker (lokalne)

1. **Zainstaluj zależności**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Uruchom Redis i RabbitMQ** (lokalnie lub w Docker):
   ```bash
   docker run -d -p 6379:6379 redis:7-alpine
   docker run -d -p 5672:5672 -p 15672:15672 -e RABBITMQ_DEFAULT_USER=admin -e RABBITMQ_DEFAULT_PASS=admin123 rabbitmq:3-management-alpine
   ```

3. **Ustaw zmienne środowiskowe**:
   ```bash
   export REDIS_HOST=localhost
   export RABBITMQ_HOST=localhost
   export RABBITMQ_USER=admin
   export RABBITMQ_PASSWORD=admin123
   ```

4. **Uruchom aplikację**:
   ```bash
   python app/main.py
   ```

## 📡 API Endpoints

### `GET /`
Strona główna z interfejsem głosowania.

### `POST /vote`
Wysyła głos na wybraną opcję.
- **Body**: `vote=<option_name>`
- **Response**: JSON z aktualnymi wynikami

### `POST /reset`
Resetuje wszystkie głosy.
- **Response**: JSON z potwierdzeniem

### `GET /api/stats`
Zwraca statystyki głosowania w formacie JSON.
- **Response**:
  ```json
  {
    "option1": "Real",
    "option2": "Barca",
    "vote1": 10,
    "vote2": 5,
    "total": 15,
    "percentage1": 66.67,
    "percentage2": 33.33
  }
  ```

### `GET /health`
Health check endpoint.
- **Response**:
  ```json
  {
    "status": "ok",
    "redis": "ok",
    "timestamp": "2026-02-09T18:00:00"
  }
  ```

## 🐳 Serwisy Docker

Aplikacja składa się z trzech kontenerów:

1. **web** - Aplikacja Flask (port 5000)
2. **redis** - Baza danych Redis (port 6379)
3. **rabbitmq** - Kolejka RabbitMQ (porty 5672, 15672)

### RabbitMQ Management UI

Dostęp do interfejsu zarządzania RabbitMQ:
```
http://localhost:15672
```
- **Login**: admin
- **Hasło**: admin123

## 🔄 Architektura

```
┌─────────────┐
│   Browser   │
└──────┬──────┘
       │ HTTP
       ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ Flask App   │────▶│   Redis     │     │  RabbitMQ   │
│  (Port 5000)│     │ (Port 6379) │     │ (Port 5672) │
└─────────────┘     └─────────────┘     └─────────────┘
       │                    │                    │
       └────────────────────┴────────────────────┘
                    Docker Network
```

### Przepływ danych:

1. Użytkownik głosuje przez interfejs webowy
2. Flask przyjmuje żądanie POST na `/vote`
3. Głos jest wysyłany do kolejki RabbitMQ (asynchronicznie)
4. Głos jest również zapisywany bezpośrednio w Redis (synchronicznie)
5. Wyniki są zwracane użytkownikowi
6. Interfejs automatycznie odświeża się co 5 sekund

## 🧪 Testowanie

### Testowanie API za pomocą curl:

```bash
# Sprawdzenie health check
curl http://localhost:5000/health

# Pobranie statystyk
curl http://localhost:5000/api/stats

# Głosowanie
curl -X POST http://localhost:5000/vote -d "vote=Real"

# Reset głosów
curl -X POST http://localhost:5000/reset
```

## 📝 Konfiguracja

Zmienne środowiskowe można zmienić w pliku `docker-compose.yaml`:

- `VOTE_OPTION_1` - Nazwa pierwszej opcji głosowania (domyślnie: Real)
- `VOTE_OPTION_2` - Nazwa drugiej opcji głosowania (domyślnie: Barca)
- `APP_TITLE` - Tytuł aplikacji
- `RABBITMQ_USER` / `RABBITMQ_PASSWORD` - Dane logowania do RabbitMQ

## 🛑 Zatrzymanie aplikacji

```bash
docker-compose down
```

Aby usunąć również wolumeny z danymi:
```bash
docker-compose down -v
```

## 📚 Dokumentacja dodatkowa

### Redis
- Dane są przechowywane w Redis jako klucz-wartość
- Klucze: nazwy opcji głosowania
- Wartości: liczba głosów (integer)

### RabbitMQ
- Kolejka: `votes`
- Wiadomości w formacie JSON zawierają:
  - `option`: wybrana opcja
  - `timestamp`: czas głosowania
  - `ip`: adres IP użytkownika

### Worker (Opcjonalny)
Aplikacja zawiera opcjonalny worker (`app/worker.py`) do asynchronicznego przetwarzania wiadomości z RabbitMQ. Worker można uruchomić osobno:

```bash
python app/worker.py
```

Worker automatycznie przetwarza wiadomości z kolejki i aktualizuje dane w Redis. W podstawowej konfiguracji aplikacja Flask przetwarza głosy synchronicznie, ale worker może być użyty do bardziej zaawansowanych scenariuszy (np. logowanie, analityka, powiadomienia).

## 👥 Autorzy
Kacper Chłopek
Szymon Piechocki
## 📄 Licencja

Ten projekt został stworzony na potrzeby zaliczenia przedmiotu "Projektowanie aplikacji internetowych".

## 🎯 Prezentacja

Prezentacja projektu obejmuje:
- Demonstrację działania aplikacji
- Omówienie architektury
- Prezentację wykorzystanych technologii
- Pokaz interfejsu RabbitMQ Management UI

---

**Uwaga**: Projekt jest gotowy do prezentacji i zawiera wszystkie wymagane elementy zgodnie z wytycznymi zaliczenia.
