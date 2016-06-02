# -*- coding: utf-8 -*-
import os
from fb2parse import BookFile
from binascii import Error as base64PaddingError
from shutil import move as shumove
from datetime import datetime
import django
os.environ["DJANGO_SETTINGS_MODULE"] = "fb2lib.settings"
django.setup()
from fb2lib.private_settings import SRC_BOOK_PATH, COVERS, LIBRARY_PATH
from book.models import Book, Sequence, SequenceBook, Genre, Translator, \
    Author, Language, Publisher


# Модуль в одном потоке бежит по файловой системе,
# читает файлы, перекладывает их в другое место
# сразу же добавляет в базу, упаковывает их


# todo: 4 проверка дубликатов
# todo: 5 добавение в базу
# todo: 6 упаковка


SOURCE = SRC_BOOK_PATH
LIBRARY = LIBRARY_PATH


def get_path_elements(path):
    """ Разбираем путь на части """
    _path, _file = os.path.split(path)
    elements = []
    while 1:
        _path, folder = os.path.split(_path)
        if folder != '':
            elements.append(folder)
            if _path == "":
                break
        else:
            if _path != "":
                elements.append(_path)
            break
    elements.reverse()
    return elements


def build_path(book_file):
    """ Строим дерево каталогов """
    name, path = book_file.get_new_name_path()
    start_path = LIBRARY
    elements = get_path_elements(path)
    for el in elements:
        start_path = os.path.join(start_path, el)
        if not os.path.exists(start_path):
            try:
                os.mkdir(start_path)
            except Exception, e:
                return False
    return True


def move_book(book_file):
    # строим путь в ФС для книги
    res = build_path(book_file)
    if res:
        _path = os.path.join(LIBRARY, book_file.new_path)
        try:
            shumove(book_file.file, _path)
        except Exception:
            return False
        return True
    return False


def main():
    for (_dir, sub_dir, files_here) in os.walk(SOURCE):
        for _file in files_here:
            start = datetime.now()
            # собираем file-object книгу
            _file_path = os.path.join(_dir, _file)
            book_file = BookFile(_file_path)
            # собираем class-object книгу
            res = book_file.make_book()
            if not res:
                # если не получилось - пропускаем
                continue
            # перемещаем книгу
            res = move_book(book_file)
            if not res:
                continue
            res = save_cover(book_file)
            if not res:
                continue
            save_book(book_file)
            print datetime.now() - start


def save_cover(book_file):
    if book_file.book.cover is not None:
        covername = book_file.hash
        coverpath = os.path.join(COVERS, covername[:4])
        if not os.path.exists(coverpath):
            os.mkdir(coverpath)
        _path = os.path.join(
            coverpath,
            covername + '.' + book_file.book.cover.extension
        )
        with open(_path, 'wb') as coverfile:
            try:
                coverfile.write(book_file.book.cover.data.decode('base64'))
                return True
            except base64PaddingError:
                # todo: fix padding
                return False
    return False


def save_book(book_file):
    """
    book_file instance ob BookFile
    """
    book = book_file.book
    # Добавляем книгу
    if not Book.objects.filter(md5=book_file.hash).exists():
        obj = Book.objects.create(
            title=book_file.book.title,
            annotation=book_file.book.annotation,
            date=book_file.book.date,
            book_file=book_file.new_path,
            md5=book_file.hash
        )
    else:
        obj = Book.objects.get(md5=book_file.hash)

    if book_file.book.cover is not None:
        obj.image = os.path.join(book_file.hash[:4],
                                 book_file.hash + '.' +
                                 book_file.book.cover.extension
                                 )
        obj.save()

    _lang = book.lang if book.lang is not None else "UNKNOWN"
    book_lang, cr = Language.objects.get_or_create(code=_lang)
    _src_lang = book.src_lang if book.src_lang is not None else "UNKNOWN"
    book_src_lang, cr = Language.objects.get_or_create(code=_src_lang)

    if obj:
        obj.lang = book_lang
        obj.src_lang = book_src_lang
        obj.save()

    # Создаем жанры прочитанные в книге
    for b_genre in book.genres:
        if b_genre.code is not None:
            genre, cr = Genre.objects.get_or_create(code=b_genre.code,
                                                    name=b_genre.name)
        else:
            genre, cr = Genre.objects.get_or_create(code='UNKNOWN')

        if obj:
            obj.genre.add(genre)

    # Создаем авторов
    for _author in book.authors:
        author, cr = Author.objects.get_or_create(
            first_name=_author.first_name,
            middle_name=_author.middle_name,
            last_name=_author.last_name
        )
        if obj:
            obj.authors.add(author)

    # добавляем переводчиков
    for _translator in book.translators:
        translator, cr = Translator.objects.get_or_create(
            first_name=_translator.first_name,
            middle_name=_translator.middle_name,
            last_name=_translator.last_name
        )
        if obj:
            obj.translator.add(translator)
    # Создаем серии

    for b_sequence in book.sequences:
        if b_sequence.name:
            sequence, cr = Sequence.objects.get_or_create(name=b_sequence.name)
            SequenceBook.objects.get_or_create(
                book=obj,
                sequence=sequence,
                number=b_sequence.number
            )

if __name__ == "__main__":
    main()
