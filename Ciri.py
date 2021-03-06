#! /usr/bin/env python
from __future__ import print_function
import requests
import os
import time
from multiprocessing import Pool
import shelve
import argparse
import zipfile
import wget
import threading
"""
========================================================================================================================
                        Ciri, short for Cirilla Fiona Elen Riannon, is an xkcd comic downloader.
========================================================================================================================
"""


def setup(path):
    if not os.path.isdir(path):
        os.makedirs(path)

    os.chdir(path)


def comic_url(num=''):
    url = 'https://xkcd.com/'
    if num:
        url += '{}/'.format(num)
    url += 'info.0.json'
    return url


def comic_info(num=''):
    """
    Returns None if comic doesn't exist.
    The returned dict has these attributes:
    title: title of comic
    safe_title: title without html tags, if title has any
    :parameter num: number of comic(int)
    img: direct url of image
    month: month the comic was released
    day: day the comic was released
    year: year the comic was released
    alt: alt/hover text of the image
    transcript: transcript of the comic
    link: image's hyperlink
    news: ? url of associated news article ?
    """
    req = requests.get(comic_url(num))
    if req.status_code == 200:
        return req.json()
    return None


def fetch():
    if not os.path.isfile('.UpdateLog'):
        log = shelve.open('.UpdateLog')                         # Default values to new log file.
        log['Complete'] = None                                  # None, True , False. True = No errors during download.
        log['Record'] = 1                                       # Starts from comic #1
        log.close()

    log = shelve.open('.UpdateLog')
    status = log['Complete']                                    # Retrieve values from log file.
    start = log['Record']
    log.close()

    end = comic_info()['num'] + 1

    return status, start, end


def downloader(num):
    try:
        info = comic_info(num)
        if info is None:
            raise AttributeError

        title = info['safe_title'].encode('ascii', 'ignore')
        title = title.replace('/', '.').replace('\\', '').replace('?', '')  # '/' in title coflicts with path format.

        image_ext = info['img'][-4:]
        img_link = info['img']

        if img_link == "http://imgs.xkcd.com/comics/":
            raise TypeError

        image = requests.get(img_link)

        image_file = '{}- {}{}'.format(info['num'], title, image_ext)

        with open(image_file, 'wb') as save:
            save.write(image.content)                                     # Writes image data to file.

    except requests.exceptions.ConnectionError:
        print("Request denied by XKCD. Resuming in 2 secs..")
        time.sleep(2)
        downloader(num)

    except AttributeError:
        if num == 404:                                          # No comic at xkcd.com/404
            pass
        else:
            end = comic_info()['num']
            
            if num <= end:
                print("Comic #", num, ": Connection problem. Retrying in 1 sec..")   # Happens sometime.
                time.sleep(1)
                downloader(num)

    except TypeError:
        print("Comic #", num, " is not downloadable.")

    except Exception as e:
        print("Unexpected Error: ", e, "\n Occurred at Comic #", num, ". Report bug!")


def updatelog(pseudo_end):
    log = shelve.open('.UpdateLog')
    log['Complete'] = True
    log['Record'] = pseudo_end
    log.close()
    print("\nLogs updated at Comic #", pseudo_end - 1, "\n")


def update():
    t = time.time()                                                 # Update start time.

    status, start, end = fetch()

    if status is False:                                             # Give warning if there was error last time.
        print("Program ended unexpectedly during last attempt. Some of the downloaded data will be overwritten.")

    log = shelve.open('.UpdateLog')
    log['Complete'] = False                                        # Remains false if program exits unexpectedly.
    log.close()

    pack = 50                                                       # 50 Threads.
    loop = True
    check = False
    print("Starting from: ", start, "\n")

    while loop:
        pseudo_end = start + pack

        if pseudo_end < end:
            pass
        else:
            pseudo_end = end
            loop = False

        threads = []

        for x in range(start, pseudo_end):
            thread = threading.Thread(target=downloader, args=(x,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        if check:
            updatelog(pseudo_end)                           # will update logs after every 100 comics.
        else:
            check = not check

        start = pseudo_end

    print("\n\nCompleted in ", int((time.time() - t) / 60), " mins and ", int((time.time() - t) % 60), " secs.")


def archive(url):
    wget.download(url)
    with zipfile.ZipFile('XKCD_Comics.zip') as arc:
        arc.extractall()

    os.unlink('XKCD_Comics.zip')


def main():
    parser = argparse.ArgumentParser(description="Ciri: XKCD Comic Downloader.")

    group = parser.add_mutually_exclusive_group()

    group.add_argument('--archive', action="store_true", help="Download and extract the zip archive.")
    group.add_argument('--update', action="store_true", help="Update the comic archive.")
    group.add_argument('--select', action="store", nargs='+', type=int,
                       help="Download selective comics: --select 2 3 66 900")
    group.add_argument('--bounds', action="store", nargs=2, type=int,
                       help="Download given range of comics: --bounds 2 99")

    result = parser.parse_args()

    url = "http://insomniacprogrammer.hol.es/xkcd/XKCD_Comics.zip"

    path = os.path.join('.', 'XKCD_Comics')

    setup(path)

    if result.archive:
        print("Downloading archive(~100MB)...\nThis may take some time.")
        try:
            archive(url)
            print("Done")

        except Exception as e:
            print('Error: ', e)

    elif result.update:
        print("Updating archive...\n")
        update()

    elif result.select:
        print("Starting download...\n")
        threads = []                       # a list of all the Thread objects

        for x in result.select:
            if x > 0:
                thread = threading.Thread(target=downloader, args=(x,))
                threads.append(thread)
                thread.start()

        for thread in threads:
            thread.join()
        print("Done.")

    elif result.bounds:
        if result.bounds[1] > result.bounds[0] > 0:
            print("Starting download...\n")
            threads = []                       # a list of all the Thread objects

            start = result.bounds[0]
            end = result.bounds[1] + 1
            loop = True

            while loop:
                pseudo_end = start + 10

                if pseudo_end > end:                 # 10 threads at a time.
                    pseudo_end = end
                    loop = False

                for x in range(start, pseudo_end):
                    thread = threading.Thread(target=downloader, args=(x,))
                    threads.append(thread)
                    thread.start()

                for thread in threads:
                    thread.join()

                start = pseudo_end

            print("Done.")

        else:
            print(":Range not defined Correctly.\n")

    else:
        print("see --help for help")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("Process interrupted.")
exit()
