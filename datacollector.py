import pathlib
import sys
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import tqdm

logging.basicConfig(
    filename='log.txt',
    level=logging.WARNING,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)


def collect_text_from_folders(folders, extension, use_multithreading=False):
    """Собирает текст из всех файлов с заданным расширением (рекурсивно)."""
    all_files = []
    
    for folder in folders:
        if not folder.exists() or not folder.is_dir():
            error_msg = f"Папка '{folder}' не существует или не является директорией."
            print(error_msg, file=sys.stderr)
            logging.warning(error_msg)
            continue
        
        for file_path in folder.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() == extension.lower():
                all_files.append(file_path)
    
    if not all_files:
        return

    def read_file(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
                return f"--- Содержимое файла: {file_path.name} ---\n{text}\n\n"
        except UnicodeDecodeError:
            warning_msg = f"Файл '{file_path}' не является текстовым или имеет неподдерживаемую кодировку. Пропускаю."
            print(warning_msg, file=sys.stderr)
            logging.warning(warning_msg)
            return ""
        except Exception as e:
            error_msg = f"Ошибка при чтении файла '{file_path}': {e}"
            print(error_msg, file=sys.stderr)
            logging.error(error_msg)
            return ""

    if use_multithreading:
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {executor.submit(read_file, file): file for file in all_files}
            for future in tqdm.tqdm(as_completed(futures), total=len(futures), desc="Обрабатываю файлы"):
                yield future.result()
    else:
        for file_path in tqdm.tqdm(all_files, desc="Обрабатываю файлы"):
            yield read_file(file_path)


def main():
    print("Привет! Это MVP агрегатор текста из файлов в папках.")
    print("Программа соберёт весь текст из файлов с указанным расширением и сохранит в файл.")

    while True:
        try:
            num_folders = int(input("Сколько папок вы хотите обработать? (Введите число, например, 1 или 2): "))
            if num_folders > 0:
                break
            print("Число должно быть положительным. Попробуйте снова.")
        except ValueError:
            print("Введите корректное число. Попробуйте снова.")

    folders = []
    for i in range(num_folders):
        while True:
            path_str = input(f"Введите путь к папке {i+1} (например, /home/user/docs или C:\\Users\\user\\docs): ").strip()
            if path_str:
                folders.append(pathlib.Path(path_str))
                break
            print("Путь не может быть пустым. Попробуйте снова.")

    while True:
        extension = input("Введите расширение файлов (например, .txt или .md): ").strip()
        if extension.startswith('.'):
            break
        print("Расширение должно начинаться с точки, например '.txt'. Попробуйте снова.")

    print("Обрабатываю файлы... Пожалуйста, подождите.")
    text_generator = collect_text_from_folders(folders, extension, use_multithreading=False)

    has_content = False
    temp_file = pathlib.Path("temp_output.txt")
    
    with open(temp_file, 'w', encoding='utf-8') as f:
        for chunk in text_generator:
            if chunk:
                f.write(chunk)
                has_content = True

    if not has_content:
        print("Нет файлов с указанным расширением в заданных папках.", file=sys.stderr)
        temp_file.unlink()
        return

    output_file = pathlib.Path("output.txt")
    if output_file.exists():
        while True:
            choice = input(f"Файл '{output_file}' уже существует. Перезаписать? (да/нет) или введите новое имя файла: ").strip().lower()
            if choice == 'да':
                break
            elif choice == 'нет':
                new_name = input("Введите новое имя файла (без расширения, добавлю .txt): ").strip()
                if new_name:
                    output_file = pathlib.Path(f"{new_name}.txt")
                    break
                print("Имя не может быть пустым.")
            else:
                output_file = pathlib.Path(choice)
                break

    try:
        output_file.write_text(temp_file.read_text(), encoding='utf-8')
        temp_file.unlink()
        print(f"Текст успешно собран в файл '{output_file}'.")
        print("Готово! Проверьте файл и log.txt для ошибок.")
    except Exception as e:
        error_msg = f"Ошибка при записи файла: {e}"
        print(error_msg, file=sys.stderr)
        logging.error(error_msg)
        temp_file.unlink()


if __name__ == "__main__":
    main()