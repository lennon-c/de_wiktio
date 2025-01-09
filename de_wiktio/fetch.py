# %% Import modules
"""
This module provides methods to fetch and parse XML files from the Wiktionary domain.
""" 
import requests
import pickle
import lxml.etree as ET
from typing import List, Dict,Tuple
from pathlib import Path
from de_wiktio.settings import Settings


# %% WikiDump
class WikiDump:
    """This class provides methods to parse and process the XML dump file. It also creates and loads dictionaries of title-wikitext pairs.
    """
    settings : Settings = Settings()
    """The `Settings` object."""


    def __init__(self, xml_path: str = None):
        """
        WikiDump object constructor.

        Args:
            xml_path: Path to the XML dump file to be processed. If `None`, the path indicated in Settings will be used. 
        """
        if xml_path is None:
            xml_path = WikiDump.settings.get('XML_FILE')
            if xml_path is None:
                raise ValueError("Path not provided. Please provide a valid path to the XML file or set a valid XML_FILE in Settings")

        if not Path(xml_path).exists():
            raise FileNotFoundError(f"File not found: {xml_path}. Please provide a valid path or set a valid XML_FILE in Settings") 
        
        self.xml_path= Path(xml_path)

        # Instance attributes docstring 
        self.xml_path: Path
        "Path to the XML dump file to be processed."
   

    @property
    def tree(self) -> ET._ElementTree:
        """The lxml tree object from the XML file.
        
        Lazy evaluation. This is a time consuming operation, so it is only computed when needed."""
        if not hasattr(self, '_tree'):
            self._tree = ET.parse(self.xml_path)
        return self._tree

    @property
    def root(self) -> ET.Element:
        """The root element of the tree.

        Lazy evaluation. This is a time consuming operation, so it is only computed when needed."""
        if not hasattr(self, '_root'):
            self._root  = self.tree.getroot()
        return self._root

    @property
    def namespaces(self) -> Dict[str, str]:
        """Dictionary of XML namespaces of the root element."""
        if not hasattr(self, '_namespaces'):
            self._namespaces = self._root.nsmap
        return self._namespaces

    @property
    def pages(self) -> List[ET.Element]:
        """List of all page elements from the XML file.
        
        This includes all pages from all wiki namespaces.
        Lazy evaluation. This is a time consuming operation, so it is only computed when needed.
        """
        if not hasattr(self, '_pages'):
            self._pages = self.root.findall('page', namespaces=self.namespaces)
        return self._pages
    
    def pages_by_ns(self, ns: str) -> List[ET.Element]:
        """
        Retrieve pages matching the Wiki namespace `ns`. 

        Args:
            ns: The Wiki namespace identifier to filter pages (e.g., '0' for content pages, '108' for Flexion pages).

        Returns:
            A list of page elements.
        """
        elements = list()
        for p in self.pages:
            element = p.find('ns', namespaces=self.namespaces)
            if element.text == ns: 
                elements.append(p)
        return elements

    def create_dict_by_ns(self, ns: str, dict_path: str = None) -> Dict[str, str]:
        """
        Create a dictionary with titles as keys and the corresponding *wikitext* as values and saves it to a pickle file.

        Args:
            ns: The Wiki namespace identifier to filter pages (e.g., `'0'` for content pages, `'108'` for Flexion pages)
            dict_path: The path where the dictionary should be saved. If not provided, the dictionary will be saved as 'wikidict_{ns}.pkl' in the folder indicated in Settings.

        Returns:
            A dictionary with page titles as keys and their corresponding *wikitext* as values.
        """
        if dict_path is None:
            dict_path = WikiDump.settings.get('DICT_PATH')
            if dict_path is None:
                raise ValueError("Path not provided. Please provide a valid path to the dictionary or set a valid DICT_PATH in Settings")
            
        dict_path = Path(dict_path)

        if not dict_path.exists():
            raise FileNotFoundError(f"Folder not found: {dict_path}. Please provide a valid path or set a valid DICT_PATH in Settings")

        pages = self.pages_by_ns(ns)
        dic = dict()
        for p in pages:
            title = p.find('title', namespaces=self.namespaces)
            wikitext = p.find('revision/text', namespaces=self.namespaces)
            dic[title.text] = wikitext.text
     
        dict_file = dict_path / f'wikidict_{ns}.pkl'
        
        with open(dict_file, 'wb') as f:
            pickle.dump(dic, f)
        return dic

    
    @classmethod
    def load_wikidict_by_ns(cls, file: str = None, ns: str = '0') -> Dict[str, str]:
        """
        Load a dictionary with page titles as keys and their corresponding *wikitext* as values from a pickle file.

        Args:
            file: The path to the pickle file. If `None`, the file 'wikidict_{ns}.pkl' in the folder indicated in Settings will be used.	
            ns: The wikinamespace identifier to filter pages (e.g., `'0'` for content pages, `'108'` for Flexion pages). 

        Returns:
            A dictionary with page titles as keys and their corresponding *wikitext* as values.

        Raises:
            FileNotFoundError: If the file does not exist.
        """
        if file is None:
            dict_path = cls.settings.get('DICT_PATH')
            # print(type(dict_path))
            if dict_path is None:
                raise ValueError("Path not provided. Please provide a valid path to the dictionary or set a valid DICT_PATH in Settings")
            else:
                file = Path(dict_path) / f'wikidict_{ns}.pkl'
        else:
            file = Path(file)

        if not file.exists():
            raise FileNotFoundError(f"The file {file} does not exist. Please create it first using the 'create_dict_by_ns' method.")
        
        with open(file, 'rb') as f:
            dic = pickle.load(f)
        return dic
    
class PageExport:
    """This class provides methods to fetch and parse the XML content of a Wiktionary page and to extract the *wikitext* using the export tool (Spezial:Exportieren).  
    """
    def __init__(self, title: str) -> None:
        """"
        Initialize the PageExport class.

        Args:
            title: The title of the Wiktionary page to fetch.

        Raises:
            requests.exceptions.RequestException: If the request fails.
        """
        self.title: str = title
        self.xml = self.fetch()
        self.root = ET.fromstring(self.xml)
        self.namespaces = self.root.nsmap 

        # Instance attributes docstring 
        self.title: str
        "The title of the Wiktionary page to fetch."
        self.xml: bytes
        "The XML content of the requested Wiktionary page."
        self.root: ET.Element
        "The root element of the tree."
        self.namespaces: Dict[str, str]
        "Dictionary of XML namespaces of the root element."
 

    def fetch(self) -> bytes:
        """
        Fetch and return the XML content of a Wiktionary page using the export tool.

        The XML data is retrieved using the following URL:
        `https://de.wiktionary.org/wiki/Spezial:Exportieren/{self.title}`

 
        Returns:
            the response.content - The XML content of the requested Wiktionary page.

        Raises:
            requests.exceptions.RequestException: If the request fails.
        """
        url = f'https://de.wiktionary.org/wiki/Spezial:Exportieren/{self.title}'
        resp = requests.get(url)
        resp.raise_for_status()
        return resp.content 
    
    @property
    def page(self) -> ET.Element:
        """The page element."""
        return self.root.find('page', namespaces=self.namespaces)
    
    @property
    def wikitext(self) -> str:
        """The *wikitext* of the page as a string.
        
        If not found, an empty string is returned.
        """
        if self.page is None:
            return ''
        
        wikitext_element = self.page.find('revision/text', namespaces=self.namespaces)

        if wikitext_element is None:
            return ''
        
        return wikitext_element.text
    
    @property
    def ns(self) -> str:
        """The Wiki namespace of the page as a string.

        If not found, an empty string is returned.
        """
        if self.page is None:
            return ''

        ns_element = self.page.find('ns', namespaces=self.namespaces)
        if ns_element is None:
            return ''
        
        return ns_element.text


def fetch_page_Action_API(title:str)-> bytes:
    """Fetch online and return the XML content of a Wiktionary page for the given title using the Action API.

    The XML data is retrieved from base URL:
    `https://de.wiktionary.org/w/api.php`

    Args:
        title: The title of the Wiktionary page to fetch.

    Returns:
        bytes: The XML content of the requested Wiktionary page.
    """
    url = "https://de.wiktionary.org/w/api.php"

    params = {
        "titles": title,
        "action": "query",
        "export": 1,
        "exportnowrap": 1
    }

    resp = requests.get(url=url, params=params)
    return resp.content

 
def print_tags_tree(
                    elem: ET.Element,
                    only_tagnames: bool = False,
                    print_attributes: bool = False,
                    print_text: bool = False,
                    max_children: int = 5,
                    max_level: int = 5,
                    _level: int = 0
                    ) -> None:
    """Print the tree structure of an XML element, with options for customization.

    Args:
        elem: The XML `Element` object whose tree structure is to be printed.
        only_tagnames: If True, print only the tag name without the namespace.
        print_attributes: If True, print the attributes of each element.
        print_text: If True, print the text content of each element.
        max_children: The maximum number of children to print for the root element.
        max_level: The maximum depth of the tree to print.
        _level: The current recursion level. This is used internally and should not be set by the user.
    """
    tagname = ET.QName(elem).localname if only_tagnames else elem.tag
    print(" " * 5 * _level, _level, tagname)

    if print_attributes:
        for attr in elem.attrib:
            print(" " * 5 * (_level + 1), attr, "=", elem.attrib[attr])

    if print_text:
        if elem.text is not None and elem.text.strip():
            print(" " * 5 * (_level + 1), elem.text)
        
    # Restrict depth
    if _level + 1 <= max_level:
        for child_index, child in enumerate(elem):
            print_tags_tree(child,
                print_attributes=print_attributes,
                print_text=print_text,
                only_tagnames=only_tagnames,
                max_children=max_children,
                max_level=max_level,
                _level=_level + 1)
            # Limit number of children of the root element
            if _level == 0 and child_index == max_children - 1:
                break