"""
This module provides methods to parse *wikitext* and extract data from Wiktionary pages.
""" 
# %%
from __future__ import annotations
import mwparserfromhell
from mwparserfromhell.wikicode import Wikicode
from mwparserfromhell.nodes.heading import Heading
from mwparserfromhell.nodes.template import Template

from de_wiktio.fetch import  PageExport, WikiDump

from typing import List, Optional, Dict, Self
from pathlib import Path
import re
 
class _EntryBase:
    """Base class for parsing the *wikitex* of a Wiktionary page.

    The Wiktionary domain is divided into different namespaces (see the German wiki help page on  Namespaces [here](https://de.wiktionary.org/wiki/Hilfe:Namensr%C3%A4ume)). Pages from some namespaces are not relevant for our purposes and presumably other namespaces would require a different parser. 

    So the approach here is to use EntryBase as a base class to create subclasses for each namespace `NS`. The specific `NS` of the subclass is defined in the 'NS' class attribute.

    """
    WIKIDICT = None
    NS = '0'

    # doctring Class attributes
    NS: str
    """Class attribute: The wiki namespace identifier. 
    Each subclass should define its own `NS` value."""

    WIKIDICT: dict
    """Class attribute: Dictionary of title-wikitext pairs.
    
    To be accessed when using the `from_dump` class method. 
    This is a lazy attribute. It loads the dictionary when needed. After that, it is kept in memory as a class attribute so that the dictionary is not loaded multiple times when using the `from_dump` class method to create a new `Entry` object."""

    @classmethod
    def from_export(cls, title: str) -> Self:      
        """Create a class instance by fetching online the wiki page.

        Args:
            title: The title of the Wiktionary page.

        Returns:
            An EntryBase or a subclass instance
        """
        fetched = PageExport(title)
        wikitext = fetched.wikitext

        if fetched.wikitext == '':
            status = f'No content for {title} in exported page'
        elif fetched.ns != cls.NS:
            status = f'No proper wiki namespace found for {title}'
            wikitext = ''
        else:
            status = 'OK'
        return cls(title, wikitext, status,'from export')

    @classmethod
    def from_dump(cls, title: str, dict_path: Optional[str] = None) -> Self: 
        """
        Create a class instance by fetching the *wikitext* from local dictionary.

        During the session, only one dictionary is loaded. The dictionary is loaded from the pickle file `'wikidict_{*cls.NS*}.pkl'`, which is located in `dict_path`.  

        Args:
            title: The title of the Wiktionary page to fetch.
            dict_path: Path to the folder containing the dictionary. If `None`, the folder indicated in `Settings` will be used.

        Returns:
            An EntryBase or a subclass instance
        """
        wikidict = cls.get_wikidict(dict_path)
        wikitext = wikidict.get(title, '')
        status = 'OK' if wikitext != '' else f'No content for {title} in dump file'
        return cls(title, wikitext, status, 'from dump')

    
    @classmethod
    def get_wikidict(cls, dict_path: Optional[str] = None) -> Dict[str, str]:
        """
        Load the dictionary from the pickle file. 

        If the dictionary is already loaded, return the dictionary from memory. Per session, only one dictionary is loaded. The dictionary is loaded from the pickle file 'wikidict_{*cls.NS*}.pkl' in `dict_path` or in the folder indicated in `Settings` if `dict_path` is not provided.

        Args:
            dict_path: Path to the folder containing the dictionary. If `None`, the folder indicated in `Settings` will be used.

        Returns:
            A dictionary with page titles as keys and their corresponding *wikitext* as values.
        """
        # if the dictionary is already loaded, return it
        if cls.WIKIDICT is not None:
            return cls.WIKIDICT
        
        # otherwise, load the dictionary
        if dict_path is None:
            cls.WIKIDICT = WikiDump.load_wikidict_by_ns(ns=cls.NS)
        else:
            _file = Path(dict_path) / f'wikidict_{cls.NS}.pkl'
            cls.WIKIDICT = WikiDump.load_wikidict_by_ns(file=_file, ns=cls.NS)

        return cls.WIKIDICT

    def __init__(self, title: str, wikitext:str, status:str='OK', extracted_from:str =None) -> None:
        """The EntryBase constructor.

        Args:
            title: The wiki page title
            wikitext: The *wikitext* of the page
            status: The status.  
            extracted_from: The source of the extraction.

                - The possible values are: 'from dump', 'from export' or `None`.
        """

        self.title: str = title
        """The title of the Wiktionary page."""

        self.text: str = wikitext
        """The *wikitext* of the page."""

        self.status: str = status
        """The status of the parsing and extraction. 
        
        Some values are: 'OK', 'No content for {title} in exported page' or 'No proper wiki namespace found for {title}'
        """

        self.extracted_from: str = extracted_from
        """The source of the extraction. 
        
        The possible values are: 'from dump', 'from export' or `None`. A `None` value indicates that the instance was created directly from the constructor passing the *wikitext* and title of the page."""

        if self.status != 'OK':
            print(f'Wiki search for "{self.title}" failed: {self.status}')
            return

 
    @property
    def parsed(self) -> Wikicode:
        """The parsed *wikitext* of the page.
        
        The *wikitext* is parsed using the `mwparserfromhell` library.
        """
        if not hasattr(self, '_parsed'):
            self._parsed = mwparserfromhell.parse(self.text)
        return self._parsed

    
    def _get_section_de(self) -> Optional[Wikicode]:
        """
        Retrieve the German section of the wikitext.

        Returns:
            The German section if found, otherwise None.

        Raises:
            Exception: If more than one German section is found.
        """
        sections = self.parsed.get_sections(levels=[2], matches=r"\|Deutsch")

        if len(sections) == 1:
            return sections[0]
        
        if len(sections) > 1:
            self.status = f'More than one German section found for {self.title}'
            return None
        
        if len(sections) == 0:
            self.status = f'No German section found for {self.title}'
            return None
         

    def print_sections_tree(self, section: Optional[Wikicode] = None, level: int = 2) -> None:
        """
        Print the headings tree.

        Args:
            section: The `Wikicode`section to start printing from. If not provided, prints the headings tree of the entire wikitext.
            level: The initial heading level from where to start printing.
        """
        if section is None:
            section = self.parsed

        headings = section.filter_headings()
        for heading in headings:
            if level <= heading.level:
                print(' ' * 8 * (heading.level - level), heading.level, heading.title)


class Entry(_EntryBase):
    """Entry class for parsing *wikitext* from main content pages (ns = `0`) of the German Wiktionary.   
     
    This class deals with the German section of the page, i.e. the German-to-German dictionary. Therefore, it does not parse multilingual entries, such as English-to-German, French-to-German, etc...
    """

    NS: str = '0'
    """Class attribute: The namespace of the entry, set to `'0'`."""

    def __init__(self, title: str, wikitext:str, status:str='OK', extracted_from:str =None) -> None:
        """
        The Entry class constructor.

        Args:
            title: The title of the Wiktionary page.
            wikitext: The raw *wikitext* of the page.
            status: The status of the entry.
            extracted_from: The source of the extraction.
        """
        super().__init__(title, wikitext, status, extracted_from)
        self.german: Wikicode = self._get_section_de()
        """The German section of the page."""


    @property
    def wordforms(self) -> List[WordForm]:
        """List of German word forms."""
        if not hasattr(self, '_wordforms'):
            if self.status != 'OK':
                return []
            
            self._wordforms = self.german.get_sections(levels=[3],
                                              matches="Wortart",
                                              flat=True)
            
            if len(self._wordforms) == 0:
                self.status = f'No German word forms for {self.title}'

            self._wordforms = [WordForm(form, entry=self) for form in self._wordforms]
        
        return self._wordforms

 
class EntryFlexion(_EntryBase):
    """Entry class for parsing *wikitext* from Flexion pages (ns = `108`).

    Flexion pages hold the complete inflection tables for verbs and adjectives. These tables are referred to as *Flexionseiten* in the German Wiktionary. They are an extension of the inflection tables of the main content pages. 
     
    This class deals with the German section of the page, i.e. the German-to-German dictionary. Therefore, it does not parse multilingual entries, such as English-to-German, French-to-German, etc...
    """
     
    NS = '108'
    """Class attribute: The namespace of the entry, set to `'108'`."""

    def __init__(self, title: str, wikitext: str, status: str = 'OK', extracted_from: Optional[str] = None) -> None:
        """
        The EntryFlexion class constructor.

        Args:
            title: The title of the Wiktionary page.
            wikitext: The raw *wikitext* of the page.
            status: The status of the entry.
            extracted_from: The source of the extraction.

        """
        super().__init__(title, wikitext, status, extracted_from)
        self.german: Wikicode = self._get_section_de()
        """The German section of the page."""

    @property
    def pos(self) -> List[str]:
        """List of German *Part Of Speech* (POS).

        The POS are extracted from the name of the flexion templates in the body.
        The possible values are "Adjektiv", "Verb", "Adverb", "Gerundivum", or "Numerale".
        """
        if not hasattr(self, '_pos'):
            if self.status != 'OK':
                return []
            
            pattern = r"(Adjektiv|Verb|Adverb|Gerundivum|Numerale)"
            compiled = re.compile(pattern)
            self._pos = []

            for template in self.flexion_tpls:
                match = compiled.search(str(template.name))
                if match:
                    self._pos.append(match.group(1))

            if not self._pos:
                self.status = f'No POS found for {self.title}'
            
            if len(self._pos) > 1:
                self.status = f'Multiple POS found for {self.title}'

        return self._pos

    def inflections(self) -> List[Dict[str, str]]:
        """Retrieve a list of dictionaries from the inflection templates.

        Returns:
            A list of dictionaries where each dictionary represents an inflection template.
        """
        return [Tools.template_to_dict(template) for template in self.flexion_tpls]

    @property
    def flexion_tpls(self) -> List[Template]:
        """List of German flexion templates.

        Templates are extracted from the body of the page.
        """
        if not hasattr(self, '_flexion_tpls'):
            if self.status != 'OK':
                    return []
            body = self.german.get_sections(include_headings=False)
            self._flexion_tpls = []
            for node in body:
                self._flexion_tpls += node.filter_templates()
            
            if self._flexion_tpls == []:
                self.status = 'No German flexion templates'
            elif len(self._flexion_tpls) > 1:
                self.status = 'Multiple German flexion templates'
        
        return self._flexion_tpls


class WordForm:
    """A class representing a word form.

    Future work:
        - Add translations  
    """
 
    def __init__(self, wordform: Wikicode, entry: Entry = None) -> None:
        """The WordForm constructor.
        
        Args:
            wordform: A Wikicode object containing the word form.
        """
        self.wordform: Wikicode = wordform
        """A Wikicode object containing the word form."""
        self.status: str = 'OK'
        """The status of the word form."""
        self.entry: Entry = entry
        """The `Entry` object to which the word form belongs."""

    @property
    def heading(self) -> Heading:
        """The heading of the word form."""
        return self.wordform.filter_headings()[0]


    @property
    def pos(self) -> List[str]:
        """List of Part Of Speech (POS) or empty list if no POS are found.

        The POS are extracted from the *Wortart* templates of the word form.
        """
        if not hasattr(self, '_pos'):
            self._pos = [str(tpl.get('1')) 
                         for tpl in self.wortart_tpls 
                         if tpl.get('1', default=None)]
            if not self._pos:
                self.status = f'No POS found for {self.heading.title}'
                
        return self._pos

    
    @property
    def _flexionseite(self) -> None | EntryFlexion: 
        """The EntryFlexion object associated to the word form.

        Returns: 
            EntryFlexion object or None if the Flexion page is not found or if the word form is not a verb nor an adjective.
        """

        if not hasattr(self, '__flexionseite'):
            if self.status != 'OK':
                self.__flexionseite = None
                return self.__flexionseite

            if not any(word in self.pos for word in ['Verb', 'Adjektiv']):
                self.__flexionseite = None
                return self.__flexionseite

            title = f'Flexion:{self.entry.title}'
            if self.entry.extracted_from == 'from export':
                self.__flexionseite = EntryFlexion.from_export(title) 
            else:
                self.__flexionseite = EntryFlexion.from_dump(title)
            
        return self.__flexionseite


    def inflections(self, all: bool=False) -> List[Dict[str, str]]:
        """
        Retrieve a list of inflections of the word form from the main content page (ns = 0).

        The inflections are extracted from the *Übersicht* templates from the main content page.

        Args:
            all: If `True`, all keys of the inflections templates are returned, otherwise keys relating to the image ('Bild') are removed.

        Returns:
            A list of dictionaries, where each dictionary represents an inflection table. The keys of the dictionaries are the parameter names of the *Übersicht* template, and the values are the corresponding parameter values.  
        """
        flexions = [Tools.template_to_dict(template) for template in self.übersichten_tpls]
        if all:
            return flexions
        else:
            return [{k:v for k,v in flexion.items() 
                if 'Bild' not in k  
                and not k.isnumeric()} for flexion in flexions]
        
    def inflections_extended(self) -> List[Dict[str, str]]:
        """List of dictionaries with the inflections templates from the Flexion pages (ns = 108).

        In general, this are small dictionaries, providing additional infomation for the contruction of extended inflection tables.

        Returns: 
            A list of dictionaries, or an empty list if no inflection templates are found or the word form is not a verb or adjective.
        """
        if self._flexionseite:
            return self._flexionseite.inflections()
        else:
            return []


    def other_content_extract(self, name: str, strip_code: bool = True, strip_kw: Optional[Dict[str, str]] = None) -> str:
        """Extract other content such as `Bedeutungen`, `Beispiele`, `Synonyme`, or `Sprichwörter`.

        Extracts other types of content which are located within the word form section of the page in separate paragraphs. The first line of the paragraph includes only a template without parameters, whose name is the type of content to extract. The content is extracted from the second line until the end of the paragraph.

        Args:
            name: The name of the template to extract content from. i.e. "Bedeutungen", "Beispiele", "Synonyme", or "Sprichwörter", or any other template name that follows the same pattern.
            strip_code: Whether to strip *wikitext* code from the extracted content and return plain text.
            strip_kw: A dictionary of keyword arguments to pass to `strip_code` method of [`mwparserfromhell.nodes.Wikicode`][mwparserfromhell.wikicode.Wikicode.strip_code] objects.

        Returns:
            The extracted content, either as plain text or raw *wikitext*.
        """
        text = str(self.wordform)
        pattern = r'\n\n\{\{' + name + r'\}\}\n(.+?)\n\n'
        search = re.search(pattern, text, re.DOTALL)
        
        if search is None:
            return  
        
        content = search.group(1)
        
        if strip_code:
            if strip_kw is not None:
                content = mwparserfromhell.parse(content).strip_code(**strip_kw)
            else:
                content = mwparserfromhell.parse(content).strip_code()
            
        return content


    @property
    def wortart_tpls(self) -> List[Template]:
        """List of *Wortart* template objects. Returns an empty list if no *Wortart* template is found.
        
        Note: In principle, one would expect only one *Wortart* template per word form, but in practice, there can be more than one.        
        """
        if not hasattr(self, '_wortart_tpls'):
            self._wortart_tpls = self.wordform.filter_templates(matches='Wortart')
            if len(self._wortart_tpls) == 0:
                self.status = f'No Wortart template found for {self.heading.title}'
                self._wortart_tpls = []
        
        return self._wortart_tpls



    @property
    def übersichten_tpls(self) -> List[Template]:
        """List of templates generating inflection tables (*Flexionstabellen*) in the main content page.

        These tables provide a brief overview (*Übersicht*) of the word form's inflections.
        Full inflection tables can be found in the corresponding *Flexionsseiten* (Flexion wiki namespace).
    
        Note: Most word forms have either none or only one Übersicht template, but there are cases where they have more than one, such as for 'Mars' and 'Partikel'.
        """
        if not hasattr(self, '_übersichten_tpls'):
            self._übersichten_tpls = self.wordform.filter_templates(matches='Übersicht')
        return self._übersichten_tpls
 
    
class Tools:
    """Collection of utility functions."""

    @staticmethod
    def template_to_dict(template: Template) -> Dict[str, str]:
       """Get dictionary of paramenters from template object.
       
       Although templates objects have many functionalities similar to dictionaries, they do not return values as strings, but as objects. This function converts these objects to a dictionary of strings.
       
       Args:
           template: A `Template` object.
       
       Returns:
           A dictionary of the template object.
       """
       params = {str(p.name).strip():str(p.value).strip() 
                 for p in template.params}
       return params

