## Extracting German Wiktionary Data

There are two ways to fetch, parse, and extract *wikitext* content:

- By fetching content online:

```python exec="1" source="above"  session="showcase"
from de_wiktio.entry import Entry

entry = Entry.from_export('stark')
```

- Or from your machine. This requires preprocessing the dump files from the German wiktionary and storing the information locally in a dictionary. See below for instructions. 

```python   
entry = Entry.from_dump('stark')
```

Both methods above return an `Entry` object. From which,

- you can access the raw *wikitext* from the page.

```python exec="1" source="tabbed-left" result="pycon" session="showcase"
print('type = ',type(entry),'\n') 
print(entry.text[:500])
```

- explore the headings tree.
=== "Source"
    ```python
    # For the whole page:
    entry.print_sections_tree()
    ```
=== "Result"
    ```pycon
    2  stark ({{Sprache|Deutsch}})
        3  {{Wortart|Adjektiv|Deutsch}}
            4  {{Übersetzungen}}
    2  stark ({{Sprache|Englisch}})
        3  {{Wortart|Adjektiv|Englisch}}
            4  {{Übersetzungen}}
        3  {{Wortart|Adverb|Englisch}}
            4  {{Übersetzungen}}
    2  stark ({{Sprache|Schwedisch}})
        3  {{Wortart|Adjektiv|Schwedisch}}
            4  {{Übersetzungen}}
    2  stark ({{Sprache|Deutsch}})
        3  {{Wortart|Adjektiv|Deutsch}}
            4  {{Übersetzungen}}
    ```

===! "Source"
    ```python 
    # For the German section:
    entry.print_sections_tree(section=entry.german) 
    ``` 
=== "Result"
    ```pycon
    2  stark ({{Sprache|Deutsch}})
        3  {{Wortart|Adjektiv|Deutsch}}
            4  {{Übersetzungen}}
    ```

`Entry` objects extract additional information from the *German section*: 

- The list of German word forms, using `entry.wordforms`
: Which returns a list of `WordForm` objects.

```python exec="1" source="tabbed-left" result="pycon"  session="showcase"
print(len(entry.wordforms))
```
From a `WordForm` object, you can extract:

- The Part of the Speech

```python exec="1" source="tabbed-left" result="pycon" session="showcase"
wordform =  entry.wordforms[0]
print(f'{wordform.pos = }')
```

-  Word inflections for nouns, verbs, adjectives, and adverbs.

```python exec="1" source="tabbed-left" result="pycon" session="showcase"
wordform =  entry.wordforms[0]
inflections = wordform.inflections()
for flexion in inflections:
    for k,v in flexion.items():
        print(f'{k} = {v}')
    print()
```

- And other content, such as:
: `'Bedeutungen'` (meaning),`'Beispiele'` (examples), `'Synonyme'` (synonyms), `'Sprichwörter'` (proverbs), among others.

```python exec="1" source="tabbed-left" result="pycon" session="showcase"
for content_type in ['Bedeutungen', 'Beispiele', 'Synonyme', 'Sprichwörter']:
    print(content_type.center(20, '-'))
    content = wordform.other_content_extract(content_type)
    print(content[:150], '\n')
```

## Working with dump files

To work with a dump file, you need to create a dictionary of page *titles* and *wikitexts* pairs. For this you will need to:

1. Download and decompress the Wiktionary dump file.  
    - You can download the latest version [here](https://dumps.wikimedia.org/dewiktionary/latest/dewiktionary-latest-pages-articles-multistream.xml.bz2) or refer to instructions for downloading specific versions in this [Hands-on Guide](https://lennon-c.github.io/python-wikitext-parser-guide/Fetching%20XML%20data/Dump%20files/#german-wiktionary-dump-files).
2. Specify the path to the decompressed file in `XML_FILE`.
3. Specify the folder where the dictionary should be saved in `DICT_PATH`.


```python  
# Specify your own paths
XML_FILE = r'path\to\xml\dewiktionary-20241020-pages-articles-multistream.xml'
DICT_PATH = r'path\to\dict'
```
The easiest way to get started is to set the path to the dictionary folder in `Settings`.

- This allows you to use the dump file data without repeatedly specifying the folder path.

```python
from de_wiktio.settings import Settings

Settings.set(key='DICT_PATH', value=DICT_PATH)
```

The next code will load and parse the XML dump file and create and save dictionaries to pickle files in the specified folder.

To use the `Entry.from_dump` method, you need to create two dictionaries:

- one for the main content namespace (ns = `'0'`)
- another for the Flexion namespace (ns = `'108'`)

Grab a cup of coffee and wait—it might take a few minutes (between 4 and 5 minutes on my computer).

```python
from de_wiktio.fetch import WikiDump

dump = WikiDump(XML_FILE)
_ = dump.create_dict_by_ns(ns='0')
_ = dump.create_dict_by_ns(ns='108')
```
You are now ready to work with `Entry` objects using the `from_dump` class method.

- The first `Entry` created during the session loads the dictionary, so it takes longer (around 9 to 11 seconds on my computer).
- From the second `Entry` onwards, `Entry.from_dump` accesses the dictionary from memory, making it faster than the first entry creation but also faster than fetching the content online using `from_export`.

```python exec="1" source="tabbed-left" result="pycon" session="showcase"
from de_wiktio.entry import Entry
# First entry  
entry = Entry.from_dump('stark')
print(type(entry))

# Second entry
entry = Entry.from_dump('hoch')
print(type(entry))
```
