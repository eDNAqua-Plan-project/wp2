import requests
from pypdf import PdfReader
from LLMapi import LLMapi
from ParsePubMed import ExceptionHandler

import tempfile
import os

class ParseSciHub:
    
    URL: str = 'https://sci-hub.se/'
    ABSTRACT = 'ABSTRACT'
    INTRO = 'INTRO'
    RESULTS = 'RESULTS'
    DISCUSS = 'DISCUSS'
    METHODS = 'METHODS'
    REFERENCE = 'REF'
    TYPES = [ABSTRACT, INTRO, RESULTS, DISCUSS, METHODS]
    
    def __init__(self,DOI:str,llm_api:LLMapi=None,verbose:bool = True):
        ExceptionHandler.checkType(DOI,'DOI',str)
        self.__doi = DOI
        ExceptionHandler.checkType(llm_api,'llm_api',LLMapi)
        self.__lapi = llm_api
        ExceptionHandler.checkType(verbose,'verbose',{bool,int})
        self.__verbose = bool(verbose)
        
        self.full_text = None
        
        self.__content = None
        self.__title = None
        self.__references = None
        
        if self.__verbose: print('Creating temporary PDF file')
        self.__pdf_tempfile = tempfile.NamedTemporaryFile()
        
        if self.__verbose: print('Requesting for article...')
        self.request()
        if self.__verbose: print('Parsing article...')
        self.parse()
        
    def __del__(self):
        try:
            if self.__verbose: print('Deleting temporary PDF file')
            self.__pdf_tempfile.close()
        except Exception as e:
            if self.__verbose: print('Temporary PDF was not removed:',e)
        
    def request(self):
        if self.__verbose: print('Connecting... ')
        response = requests.get(self.URI)
        ExceptionHandler.checkConnection(response)
        if self.__verbose: print(response.status_code)
        ExceptionHandler.checkContent(response)
        
        if self.__verbose: print('Extracting PDF URI')
        html = response.content.decode()
        start = html.find('embed type="application/pdf"') + 34
        stop = html.find(' id',start) - 1
        embed = html[start:stop]
        if embed.startswith('//'):
            embed = 'https:' + embed
        else:
            embed = ParseSciHub.URL + embed
            
        if self.__verbose: print('Requesting for PDF')
        response = requests.get(embed)
        full_text = None
        if self.__verbose: print('Extracting text from PDF')
        try:
            text = response.content.decode()
            if self.__verbose: print('Cannot find PDF for given DOI')
            if '404 Not Found' not in text:
                raise ValueError('Something went wrong.')
        except:
            self.__pdf_tempfile.write(response.content)
            reader = PdfReader(self.__pdf_tempfile.name)
            self.full_text = ''.join([page.extract_text() for page in reader.pages])
            
    def parse(self):
        ExceptionHandler.checkProperty(self.full_text,exception_text='No text to parse. First run .request() method.')
        if self.__verbose: print('Asking title...')
        self.__title = self.__lapi.ask(f'From given text extract title of an article. No comments, only cited text.',self.full_text)['Answer']
        if self.__verbose: print('Asking references...')
        self.__references = self.__lapi.ask(f'From given text extract DOI numbers of references to other articles. If there is no DOI just skip the position. Return result as comma separated list. No comments, only cited text.',self.full_text)['Answer']
        if self.__verbose: print('Converting references...')
        self.__references = set([ref.strip() for ref in self.__references.replace('\n',',').split(',')])  
        if self.__verbose: print('Done')
        
    @property
    def URI(self) -> str:
        return ParseSciHub.URL + self.__doi
    
    def __str__(self):
        return self.DOI
    
    def __repr__(self):
        if ExceptionHandler.checkProperty(self.__title, raise_exception=False):
            return f'Publication from SciHub on {self.DOI}.'
        return f'"{self.__title}" in SciHub with DOI {self.DOI}.'
    
    @property
    def DOI(self) -> str:
        ExceptionHandler.checkProperty(self.__doi)
        return self.__doi
    
    @property
    def Content(self) -> str:
        ExceptionHandler.checkProperty(self.__content)
        return self.__content
    
    @property
    def Title(self) -> str:
        ExceptionHandler.checkProperty(self.__title)
        return self.__title
    
    @property
    def References(self) -> set:
        ExceptionHandler.checkProperty(self.__references, exception_text='No reference to return.')
        return self.__references
    