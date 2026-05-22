from pathlib import Path


def audit_dist():
    """Перевірка цілісності папки Дистрибутив."""
    root_dir = Path(__file__).resolve().parent
    dist_dir = root_dir / "Дистрибутив"

    print("=== АУДИТ ПАПКИ ДИСТРИБУТИВ ===")
    print(f"Шлях: {dist_dir}")

    if not dist_dir.exists():
        print("❌ Папка Дистрибутив не знайдена!")
        return

    # 1. Перевірка profiles.yaml
    profiles_path = dist_dir / "_internal" / "resources" / "profiles.yaml"
    print("\n1. Перевірка конфігурації:")
    if profiles_path.exists():
        print(f" ✅ profiles.yaml знайдено ({profiles_path.stat().st_size} байт)")
    else:
        print(f" ❌ profiles.yaml НЕ ЗНАЙДЕНО в {profiles_path}")

    # 2. Перевірка баз даних у папці data
    data_dir = dist_dir / "data"
    print("\n2. Перевірка папки data:")
    if data_dir.exists():
        for client in ["АФІНА", "ДЖОНСОН", "PROCTER"]:
            client_db = data_dir / client / "certify.db"
            print(f" -> Клієнт {client}:")
            if client_db.exists():
                print(f"    ✅ certify.db знайдено ({client_db.stat().st_size} байт)")
            else:
                print("    ❌ certify.db НЕ ЗНАЙДЕНО")

            templates_dir = data_dir / client / "templates"
            if templates_dir.exists():
                files = list(templates_dir.glob("*.doc*"))
                print(f"    ✅ templates знайдено ({len(files)} файлів)")
            else:
                print("    ❌ templates НЕ ЗНАЙДЕНО")
    else:
        print(" ❌ Папка data НЕ ЗНАЙДЕНА!")

    # 3. Перевірка внутрішніх ресурсів лаунчера
    schema_path = dist_dir / "_internal" / "CERTIFYPRO" / "core" / "database" / "db_schema.sql"
    print("\n3. Перевірка внутрішніх ресурсів:")
    if schema_path.exists():
        print(" ✅ db_schema.sql знайдено")
    else:
        print(f" ❌ db_schema.sql НЕ ЗНАЙДЕНО в {schema_path}")

    input("\nНатисніть Enter...")


if __name__ == "__main__":
    audit_dist()
