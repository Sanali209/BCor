import win32clipboard
import os
# todo integrate this
from SLM.appGlue.iotools.pathtools import get_files


def copy_files_to_clipboard(file_paths):
    # Формируем список файлов с нулевым разделителем (\0) между путями
    files_str = "\0".join(file_paths) + "\0"
    # Открываем буфер обмена
    win32clipboard.OpenClipboard()
    # Очищаем буфер
    win32clipboard.EmptyClipboard()
    # Устанавливаем данные как список файлов
    win32clipboard.SetClipboardData(win32clipboard.CF_HDROP, files_str)
    # Закрываем буфер
    win32clipboard.CloseClipboard()


# Пример использования
file_list = get_files(r'G:\Мой диск\Sanali209', ['*.py'])
copy_files_to_clipboard(file_list)
print("Файлы скопированы в буфер обмена.")
