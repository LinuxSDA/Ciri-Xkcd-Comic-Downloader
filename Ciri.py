#! /usr/bin/env python
from __future__ import print_function
import requests
from bs4 import BeautifulSoup
import os
import time
from multiprocessing import Pool
import shelve
import argparse
import zipfile
import wget
"""
========================================================================================================================
                        Ciri, short for Cirilla Fiona Elen Riannon, is an xkcd comic downloader.
========================================================================================================================
"""


def setup(path):
    if not os.path.isdir(path):
        os.makedirs(path)

    os.chdir(path)


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

    lastpage = requests.get('https://xkcd.com/')
    soup = BeautifulSoup(lastpage.content, 'html.parser')

    "fetch second last comic number. Easier to get."
    end = soup.find('a', attrs={'accesskey': 'p'})['href']      # 'end' variable has format '/comic_number/'
    end = int(end[1:-1]) + 2                                    # 'end' used in range function, +2 instead of +1.

    return status, start, end


def downloader(num):

    try:
        page = requests.get('https://xkcd.com/' + str(num))
        soup = BeautifulSoup(page.content, 'html.parser')

        title = soup.find(id='ctitle').text                     # Get comic title.
        title = title.replace('/', '.')                         # '/' in comic title coflicts with linux path format.

        imglink = soup.find(id='comic').img['src']              # Get image link.

        if imglink.startswith('//'):
            image = requests.get('https:' + imglink)            # Downloads image.
        else:
            raise TypeError('This raise exception exists only because of comic #1525')

        save = open(str(num) + '- ' + title + imglink[-4:], 'wb')  # Conflict happens here, title used as filename.
        save.write(image.content)                                   # Writes image data to file.
        save.close()

    except requests.exceptions.ConnectionError:
        print("Request denied by XKCD. Resuming in 2 secs..")
        time.sleep(2)
        downloader(num)

    except TypeError:                                           # Comic 1350, 1416, 1525, 1608, 1663 are not images.
        print("Comic #", num, ": Unable to download - Comic type not image.")

    except AttributeError:
        if num == 404:                                          # No comic at xkcd.com/404
            pass
        else:
            print("Comic #", num, ": Connection problem. Retrying in 1 sec..")   # Happens sometime.
            time.sleep(1)
            downloader(num)

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

    pack = 100                                                      # will download in pack of 100 comics at a time.
    loop = True

    print("Starting from: ", start, "\n")

    while loop:
        pseudo_end = start + pack

        if pseudo_end < end:
            pass
        else:
            pseudo_end = end
            loop = False

        "I/O bound process can have more processes than cores. Don't worry!"
        pool = Pool(processes=32)       # spawns 32 processes for parallel download.
        pool.map(downloader, range(start, pseudo_end))
        pool.close()

        updatelog(pseudo_end)

        start = pseudo_end

    print("\n\nCompleted in ", int((time.time() - t) / 60), " mins and ", int((time.time() - t) % 60), " secs.")


def archive(url):

    wget.download(url)
    comic = zipfile.ZipFile('XKCD_Comics.zip')
    comic.extractall()
    comic.close()

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
        pool = Pool(processes=3)       # spawns only 3 processes for parallel download.
        pool.map(downloader, [x for x in result.select if x > 0])
        pool.close()
        print("Done.")

    elif result.bounds:
        if result.bounds[1] > result.bounds[0] > 0:
            print("Starting download...\n")
            pool = Pool(processes=8)       # spawns only 8 processes for parallel download.
            pool.map(downloader, range(result.bounds[0], result.bounds[1]+1))
            pool.close()
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
