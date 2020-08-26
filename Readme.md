# Unofficial Bundesrat Scraper - Website

## Initialize

If you start the webpage for the very first time, it can take up to 30-60 seconds before you see the page. In this time, the text JSONs from the [Bundesrat Scraper](https://github.com/okfde/bundesrat-scraper) get downloaded. After this, it should be much faster.

## Running the Test Suite

```
pip install coverage
coverage run --source='.' manage.py test scraper 
coverage report #To see test coverage of files
```
