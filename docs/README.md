`de_wiktio` is a Python package designed to parse and extract data from the *German Wiktionary*. It enables users to access *wikitext* content either by fetching it directly online or by preprocessing and loading dump files locally for faster access. It can extract linguistic data such as parts of speech, inflections, examples, definitions, among others.


This package can be thought of as a companion to the [Hands-on Guide](https://lennon-c.github.io/python-wikitext-parser-guide); all the steps and code covered in the guide are implemented here as a package. 

## Installation
The package was created using Python 11, so make sure that you have Python 11 or later. You can install the package from the my GitHub repo. The following code will install the package and its dependencies (i.e. `requests`, `lxml`, and `mwparserfromhell`):

```bash 
pip install git+https://github.com/lennon-c/de_wiktio.git
```


## Documentation
In the documentation site, you can find:

- [Usage examples](https://lennon-c.github.io/de_wiktio/usage/) and 
- [The API documentation](https://lennon-c.github.io/de_wiktio/API/).  

## The Story Behind This Package
I created this package as a personal project to extract inflection tables, which I use in my flashcard system for learning German.



