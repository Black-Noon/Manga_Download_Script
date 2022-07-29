import requests
import lxml
from bs4 import BeautifulSoup
import os
import shutil
from tqdm import tqdm
import zipfile
import re


def check_url(link):
    pattern_1 = re.compile(r"http://mangabook\.org/manga/|https://mangabook\.org/manga/")
    pattern_2 = re.compile(r"mangabook\.org/manga/")
    if re.match(pattern_1, link):
        return link
    elif re.match(pattern_2, link):
        return "http://" + link
    else:
        print("-- Ссылка некорректна! Проверьте её соответствие странице манги. --")
        exit()


def rename(name):
    pattern_1 = re.compile(r"[*?<>]")
    pattern_2 = re.compile(r"\"")
    pattern_3 = re.compile(r"[\\|/:]")
    name = re.sub(pattern_1, "", name)
    name = re.sub(pattern_2, "'", name)
    name = re.sub(pattern_3, " -", name)
    name = name.replace("  ", " ")
    if len(name) < 210:
        return name.strip()
    else:
        return name[:210].strip()


def extension():
    choice_ext = input("Выберите расширение файлов - *.zip(Z) или *.cbz(C): ").upper()

    while choice_ext != "next":
        if choice_ext == "Z":
            choice_ext = "next"
            f_ext = "zip"
        elif choice_ext == "C":
            choice_ext = "next"
            f_ext = "cbz"
        else:
            choice_ext = input("Пожалуйста, введите 'Z' или 'C': ").upper()
    return f_ext


def download(soup, download_class, ext):
    link_chapters = []
    name_chapters = []

    if download_class == "all":
        for link in soup.find_all('a', class_='btn-filt2'):
            link_chapters.append(link.get('href'))
        for name in soup.find_all('h5'):
            name_chapters.append(rename(name.text))
    else:
        names_links = soup.find_all('li', class_=download_class)
        for elem in names_links:
            link_chapters.append(elem.a.get('href'))
            name_chapters.append(rename(elem.h5.text))

    link_chapters.reverse()
    name_chapters.reverse()

    for name, link in zip(name_chapters, link_chapters):
        res = requests.get(link, stream=True)
        size = int(res.headers['content-length'])
        with tqdm.wrapattr(open("{}.{}".format(name, ext), "wb"), "write",
                           miniters=1, desc=name.ljust(64, " "),
                           total=size, ncols=128) as file:
            for chunk in res.iter_content(chunk_size=4096):
                file.write(chunk)
    return name_chapters


def parser(response):
    soup = BeautifulSoup(response.text, 'lxml')
    name_book = soup.h1.text
    chapters_soup = soup.find('ul', class_='chapters')

    if chapters_soup:
        print("Название: {}".format(name_book.strip()))
        name_book = rename(name_book)

        if not os.path.isdir(name_book):
            os.mkdir(name_book)
        os.chdir(name_book)

        choice_download = input("Выберите способ загрузки файлов - по томам(V) или все(A): ").upper()

        while choice_download != "next":
            if choice_download == "V":
                choice_download = "next"
                f_ext = extension()

                repack = input("Перепаковать файлы по томам? Да(Y)/Нет(N): ").upper()

                while repack != "Y" or repack != "N":
                    if repack == "Y":
                        break
                    elif repack == "N":
                        break
                    else:
                        repack = input("Пожалуйста, введите 'Y' или 'N': ").upper()

                print("-- Начата загрузка файлов. Ожидайте... --")

                volumes_soup = chapters_soup.find_all('li', class_='volume btn btn-default btn-xs')

                name_volumes = []
                id_volumes = []

                for volume in volumes_soup:
                    name_volumes.append(volume.text.strip())
                    id_volumes.append(volume.get('data-volume'))

                name_volumes.reverse()
                id_volumes.reverse()

                for name_volume, id_volume in zip(name_volumes, id_volumes):
                    if not os.path.isdir(name_volume):
                        os.mkdir(name_volume)
                    os.chdir(name_volume)

                    list_chapters = download(chapters_soup, id_volume, f_ext)

                    print("- {} загружен! -".format(name_volume))

                    if repack == "Y":
                        repacking(name_volume, list_chapters, f_ext)

                        print("- Перепаковка '{}' завершена. -".format(name_volume))

                    else:
                        os.chdir(os.pardir)

            elif choice_download == "A":
                choice_download = "next"
                f_ext = extension()

                print("-- Начата загрузка файлов. Ожидайте... --")

                download(chapters_soup, "all", f_ext)

            else:
                choice_download = input("Пожалуйста, введите 'V' или 'A': ").upper()

        print("-- Файлы загружены! --")
        print("-- Спасибо, что воспользовались этим скриптом. Приятного чтения! --")

    else:
        print("-- Загрузка невозможна. --")
        print("-- Файл '{}' удален по требованию правообладателя. --".format(name_book.strip()))
        print("-- Попробуйте другой адрес. --")
        main()


def repacking(volume, chapter_list, ext_archive):
    index_chapters = []
    name_list = []
    amount = 0

    for chapter in chapter_list:
        data_zip = zipfile.ZipFile(chapter + '.' + ext_archive, 'r')
        data_zip.extractall(str(chapter_list.index(chapter)))
        data_zip.close()
        os.remove(chapter + '.' + ext_archive)

    for index_chapter in os.listdir():
        index_chapters.append(index_chapter)
        os.chdir(index_chapter)

        for element in os.listdir():
            if os.path.isfile(os.path.join(element)):
                amount += 1
        os.chdir(os.pardir)

    for number in range(1, amount + 1):
        name_list.append(str(number).zfill(4))
    name_list.reverse()

    for index_chapter in index_chapters:
        os.chdir(index_chapter)
        for picture in os.listdir():
            ext_file = os.path.splitext(picture)[1]
            os.rename(picture, name_list.pop() + ext_file)
        os.chdir(os.pardir)

    for index_chapter in index_chapters:
        os.chdir(index_chapter)
        for picture in os.listdir():
            shutil.move(picture, os.pardir)
        os.chdir(os.pardir)
        shutil.rmtree(index_chapter, ignore_errors=True)

    list_files = os.listdir()
    with zipfile.ZipFile(volume + '.' + ext_archive, 'w') as zip_a:
        for file in list_files:
            zip_a.write(file)

    shutil.move(volume + '.' + ext_archive, os.pardir)
    os.chdir(os.pardir)
    shutil.rmtree(volume, ignore_errors=True)


def main():
    url = check_url(input("Введите адрес страницы: "))
    response = requests.get(url)
    if response.status_code == requests.codes.ok:
        parser(response)
    else:
        print("-- Что-то пошло не так! Страница недоступна.--")
        print("-- Проверьте корректность ссылки и её работоспособность в браузере. --")

        
if __name__ == "__main__":
    print(r"-- Скрипт предназначен для загрузки манги с сайта http://mangabook.org/ --")
    main()

# проверка работы гитхаб