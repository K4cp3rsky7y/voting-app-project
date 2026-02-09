# Instrukcja dodania projektu na GitHub

## Krok 1: Zainicjalizuj repozytorium Git (jeśli jeszcze nie zrobione)

Otwórz terminal (PowerShell lub Git Bash) w folderze projektu i wykonaj:

```bash
cd c:\Users\kacpe\Downloads\voting-app-project
git init
```

## Krok 2: Dodaj wszystkie pliki do Git

```bash
git add .
```

## Krok 3: Utwórz pierwszy commit

```bash
git commit -m "Initial commit - aplikacja do głosowania z Flask, Redis i RabbitMQ"
```

## Krok 4: Dodaj remote repository (GitHub)

Zastąp `TWOJA_NAZWA_UZYTKOWNIKA` i `NAZWA_REPOZYTORIUM` swoimi danymi:

```bash
git remote add origin https://github.com/TWOJA_NAZWA_UZYTKOWNIKA/NAZWA_REPOZYTORIUM.git
```

Przykład:
```bash
git remote add origin https://github.com/kacpe/voting-app-project.git
```

## Krok 5: Wyślij kod na GitHub

```bash
git branch -M main
git push -u origin main
```

## Jeśli masz problemy z autoryzacją:

GitHub wymaga teraz tokenu dostępu zamiast hasła:

1. Wygeneruj token: GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic) → Generate new token
2. Zaznacz uprawnienia: `repo`
3. Skopiuj token
4. Przy `git push` użyj tokenu jako hasła (username to Twój login GitHub)

Lub użyj GitHub Desktop (prostsze rozwiązanie):
- Pobierz: https://desktop.github.com/
- File → Add Local Repository → wybierz folder projektu
- Publish repository → wybierz nazwę i kliknij Publish

## Szybka weryfikacja:

Po pushu sprawdź czy wszystko się udało:
- Otwórz swoje repozytorium na GitHub.com
- Powinieneś zobaczyć wszystkie pliki projektu
