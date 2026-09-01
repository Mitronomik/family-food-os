# User Install Guide

Status: **RETIRED — NOT A FAMILYFOODOS INSTALL PROCEDURE**.

ADR 0031 retires the inherited macOS consumer package and D5 install path.
FamilyFoodOS has no current end-user install procedure until the separately
gated hosted Web/PWA delivery exists.

The following source-product draft is retained only as historical evidence and
must not be followed for FamilyFoodOS:

1. Скачать архив приложения.
2. Распаковать архив.
3. Открыть приложение.
4. Разрешить запуск в macOS, если нужно.
5. Пройти первый запуск.
6. Создать первый backup.

Планируемая папка данных пользователя:

```text
~/Documents/Мастерская косметолога/
  data/
    cosmetic_workshop.sqlite
  backups/
  exports/
  attachments/
  logs/
```

Историческое примечание: D3/D4 давали source-product `.app` внутри ZIP, но этот
draft не прошёл D5 clean-profile rehearsal. ADR 0031 отменяет его как текущий
путь FamilyFoodOS.
