import shutil
import logging


def copy_file(path_to_file, target_path_for_GML):
    try:
        shutil.copy(path_to_file, target_path_for_GML)
        print(f"Plik został skopiowany do {target_path_for_GML}.")
        return True
    except Exception as e:
        logging.exception(e)
        print(f"Wystąpił błąd podczas kopiowania pliku: {str(e)}")
        return False


if __name__ == '__main__':
    pass