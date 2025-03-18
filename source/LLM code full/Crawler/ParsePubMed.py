import pandas as pd
import requests
import xml.etree.ElementTree as ET

class ExceptionHandler:
    def checkProperty(prop, raise_exception: bool=True, exception_text:str=None):
        if exception_text is None:
            exception_text = 'Cannot find content of this publication.'
        if prop is None and raise_exception:
            raise ValueError(exception_text)
        elif prop is None:
            return True
        return False
    
    def checkType(prop, property_name, expected_types):
        if expected_types.__class__ is set().__class__:
            if prop.__class__ not in expected_types:
                raise AttributeError(f'{property_name} must be class {" or ".join([str(et) for et in expected_types])}, given parameter is class {prop.__class__}.')
        else:
            if prop.__class__ != expected_types:
                raise AttributeError(f'{property_name} must be class {expected_types.__class__}, given parameter is class {prop.__class__}.')
    
    def checkConnection(response):
        if response.status_code != 200:
            raise requests.ConnectionError(f'Cannot connect with this URI: {response.url}')
    
    def checkContent(response):
        content = response.content.decode()
        if content.startswith('No record can be found for the input'):
            raise ValueError(content)

class ParsePubMed:
    
    ABSTRACT = 'ABSTRACT'
    INTRO = 'INTRO'
    RESULTS = 'RESULTS'
    DISCUSS = 'DISCUSS'
    METHODS = 'METHODS'
    REFERENCE = 'REF'
    TYPES = [ABSTRACT, INTRO, RESULTS, DISCUSS, METHODS]
    
    
    
    def __init__(self,pub_id:int,verbose:bool = False):
        ExceptionHandler.checkType(pub_id,'pub_id',int)
        self.__pub_id = pub_id
        ExceptionHandler.checkType(verbose,'verbose',{bool,int})
        self.__verbose = bool(verbose)
        
        self.__content = None
        self.__abstract = None
        self.__intro = None
        self.__results = None
        self.__discuss = None
        self.__methods = None
        self.__title = None
        self.__doi = None
        self.__references = None
        
        self.request()
        self.parse()
        
    def request(self):
        if self.__verbose: print('Connecting... ',end='')
        self.response = requests.get(f'https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pmcoa.cgi/BioC_xml/{self.__pub_id}/unicode')
        ExceptionHandler.checkConnection(self.response)
        if self.__verbose: print(self.response.status_code)
        ExceptionHandler.checkContent(self.response)
        
    
    def parse(self):
        if self.__verbose: print('Decoding... ',end='')
        tree = ET.fromstring(self.response.content.decode())
        passages = tree.findall('./document/passage')
        
        if self.__verbose: print('OK\nParsing... ',end='')
        content = list()
        abstract = list()
        intro = list()
        results = list()
        discuss = list()
        methods = list()
        pub_ids = list()
        for passage in passages:
            #DOI
            if any([True for i in passage.findall('infon') if i.attrib['key'] == 'article-id_doi']):
                self.__doi = [i for i in passage.findall('infon') if i.attrib['key'] == 'article-id_doi'][0].text
            #title
            if any([i.text == 'TITLE' for i in passage.findall('infon') if i.attrib['key'] == 'section_type']):
                self.__title = passage.find('text').text
            #content
            if any([i.text in ParsePubMed.TYPES for i in passage.findall('infon') if i.attrib['key']=='section_type']):
                content.append(passage.find('text').text)
            #abstract
            if any([i.text == ParsePubMed.ABSTRACT for i in passage.findall('infon') if i.attrib['key']=='section_type']):
                abstract.append(passage.find('text').text)
            #intro
            if any([i.text == ParsePubMed.INTRO for i in passage.findall('infon') if i.attrib['key']=='section_type']):
                intro.append(passage.find('text').text)
            #results
            if any([i.text == ParsePubMed.RESULTS for i in passage.findall('infon') if i.attrib['key']=='section_type']):
                results.append(passage.find('text').text)
            #discuss
            if any([i.text == ParsePubMed.DISCUSS for i in passage.findall('infon') if i.attrib['key']=='section_type']):
                discuss.append(passage.find('text').text)
            #methods
            if any([i.text == ParsePubMed.METHODS for i in passage.findall('infon') if i.attrib['key']=='section_type']):
                methods.append(passage.find('text').text)
            #references
            if any([i.text == ParsePubMed.REFERENCE for i in passage.findall('infon') if i.attrib['key']=='section_type']) and len([i.text for i in passage.findall('infon') if i.attrib['key']=='pub-id_pmid']) > 0:
                pub_ids.append([i.text for i in passage.findall('infon') if i.attrib['key']=='pub-id_pmid'][0])
        
        if self.__verbose: print('OK\nMerging text... ',end='')
        self.__content = '\n'.join(content)
        self.__abstract = '\n'.join(abstract)
        self.__intro = '\n'.join(intro)
        self.__results = '\n'.join(results)
        self.__discuss = '\n'.join(discuss)
        self.__methods = '\n'.join(methods)
        
        if self.__verbose: print('OK\nExporting reference IDs... ',end='')
        self.__references = set([int(i) for i in pub_ids])
        if self.__verbose: print('OK')
    
    @property
    def PMID(self):
        return self.__pub_id
    
    def __str__(self):
        return str(self.__pub_id)
    
    def __repr__(self):
        if ExceptionHandler.checkProperty(self.__title, raise_exception=False):
            return f'Publication from PubMed on {self.__pub_id}.'
        return f'"{self.__title}" in PubMed with PMID {self.__pub_id}.'
    
    @property
    def DOI(self) -> str:
        ExceptionHandler.checkProperty(self.__doi)
        return self.__doi
    
    @property
    def Content(self) -> str:
        ExceptionHandler.checkProperty(self.__content)
        return self.__content
    
    @property
    def Abstract(self) -> str:
        ExceptionHandler.checkProperty(self.__abstract)
        return self.__abstract
    
    @property
    def Intro(self) -> str:
        ExceptionHandler.checkProperty(self.__intro)
        return self.__intro
    
    @property
    def Results(self) -> str:
        ExceptionHandler.checkProperty(self.__results)
        return self.__results
    
    @property
    def Discussion(self) -> str:
        ExceptionHandler.checkProperty(self.__discuss)
        return self.__discuss
    
    @property
    def Methods(self) -> str:
        ExceptionHandler.checkProperty(self.__methods)
        return self.__methods
    
    @property
    def Title(self) -> str:
        ExceptionHandler.checkProperty(self.__title)
        return self.__title
    
    @property
    def References(self) -> set:
        ExceptionHandler.checkProperty(self.__references, exception_text='No reference to return.')
        return set([int(ref) for ref in self.__references])
    
