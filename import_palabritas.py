"""Импортирует карточки из CSV через API проекта cards."""

import csv
import getpass
from pathlib import Path

import httpx


CSV_PATH = Path(__file__).with_name("palabritas_import.csv")
DEFAULT_API_URL = "http://127.0.0.1:8000/cards/"


def main() -> None:
    """Запрашивает параметры и отправляет карточки в API."""
    if not CSV_PATH.exists():
        raise FileNotFoundError(
            f"Не найден CSV-файл: {CSV_PATH}\n"
            "Положите palabritas_import.csv рядом с этим скриптом."
        )

    api_url = input(
        f"URL API карточек [{DEFAULT_API_URL}]: "
    ).strip() or DEFAULT_API_URL
    access_token = getpass.getpass("Access token (Bearer): ").strip()
    deck_id = int(input("ID колоды: ").strip())
    language_a_id = int(input("ID испанского языка (language_a_id): ").strip())
    language_b_id = int(input("ID русского языка (language_b_id): ").strip())

    headers = {"Authorization": f"Bearer {access_token}"}
    created = 0
    skipped = 0
    failed = 0

    with CSV_PATH.open(encoding="utf-8-sig", newline="") as csv_file:
        rows = list(csv.DictReader(csv_file))

    if not rows or not {"spanish", "russian"}.issubset(rows[0]):
        raise ValueError(
            "CSV должен содержать столбцы 'spanish' и 'russian'."
        )

    with httpx.Client(timeout=20.0) as client:
        for row_number, row in enumerate(rows, start=2):
            word = row["spanish"].strip()
            translation = row["russian"].strip()

            if not word or not translation:
                print(f"Строка {row_number}: пропущена — пустое поле.")
                skipped += 1
                continue

            payload = {
                "word": word,
                "translation": translation,
                "deck_id": deck_id,
                "language_a_id": language_a_id,
                "language_b_id": language_b_id,
            }

            try:
                response = client.post(
                    api_url,
                    headers=headers,
                    json=payload,
                )
            except httpx.HTTPError as error:
                print(f"Строка {row_number}: ошибка соединения: {error}")
                failed += 1
                continue

            if response.status_code in (200, 201):
                created += 1
                print(f"Добавлено: {word}")
            elif response.status_code == 409:
                skipped += 1
                print(f"Уже существует, пропущено: {word}")
            else:
                failed += 1
                print(
                    f"Ошибка для '{word}': HTTP {response.status_code} — "
                    f"{response.text}"
                )

    print("\nИмпорт завершён.")
    print(f"Добавлено: {created}")
    print(f"Пропущено (пустые поля/дубликаты): {skipped}")
    print(f"Ошибок: {failed}")


if __name__ == "__main__":
    main()
