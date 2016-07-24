# Ciri-Xkcd-Comic-Downloader

![Relevent XKCD](https://imgs.xkcd.com/comics/code_quality.png)



### Things to know:
  - Works on both python 2 and 3
  - Depends on ~~BeautifulSoup~~  Official API, wget and Requests. 
  - Tested on linux. ~~Should work on windows.~~ Works on Windows
  - Path is current directory. 


### Usage: (cd to downloaded path and execute script)

``` python Ciri.py --archive```

- Downloads the xkcd comic archive directly from third party server. Last updated on july 22, 2016. No need to unnecessarily crowd the XKCD servers for all comics.


```python Ciri.py --update	                             	# After downloading archive```

- Updates the xkcd comics folder anytime in near future.


```python Ciri.py --update	                            	# If archive not downloaded```

- Downloads all comics from xkcd. Program uses multiple processes for faster downloading.


```python Ciri.py --select [comic_number] [comic_number] ...```

- Download selective comics seperated by spaces.


```python Ciri.py --bounds [Lower_bound] [Upper_bound]```

- Download specified range of comics.

![Relevent XKCD](https://imgs.xkcd.com/comics/code_quality_2.png)


###If you don't wish to run script then you can download pre-fetched archive from [here](http://www.insomniacprogrammer.hol.es/xkcd/XKCD_Comics.zip). Updated on july 22, 2016.
