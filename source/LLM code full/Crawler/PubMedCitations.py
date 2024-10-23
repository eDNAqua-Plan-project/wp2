import requests
from PubMedIdTranslator import PubMedIdTranslator
import xml.etree.ElementTree as ET
from ParsePubMed import ExceptionHandler

class PubMedCitations:
    
    URL = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi?dbfrom=pubmed&linkname=pubmed_pmc_refs&id='
    
    def __init__(self,verbose:bool=True):
        ExceptionHandler.checkType(verbose,'verbose',bool)
        self.__verbose = verbose
        self.__doi = None
        self.response = None
        self.__dois = None
        
    def __call__(self,DOI:str=None):
        self.setDOI(DOI)
        self.request()
        self.parse()
        return self.getDOIs
        
    def setDOI(self,DOI:str=None):
        ExceptionHandler.checkType(DOI,'DOI',str)
        self.__doi = DOI
        
    def request(self):
        if self.__verbose: print('Connecting... ',end='')
        self.response = requests.get(self.URI)
        ExceptionHandler.checkConnection(self.response)
        if self.__verbose: print(self.response.status_code)
        ExceptionHandler.checkContent(self.response)
        
    def parse(self):
        if self.__verbose: print('Decoding... ')
        root = ET.fromstring(self.response.content.decode())
        pmcids = ['PMC' + pmcid.text for pmcid in root.findall('./LinkSet/LinkSetDb/Link/Id')]
        if self.__verbose: print('Translating...')
        self.__dois = [PubMedIdTranslator.PubMedCentraltoDOI(pmcid) for pmcid in pmcids]
        
    @property
    def URI(self) -> str:
        ExceptionHandler.checkProperty(self.__doi,exception_text='Cannot find DOI number')
        return PubMedCitations.URL + self.__doi
    
    @property
    def getDOIs(self) -> list:
        ExceptionHandler.checkProperty(self.__dois,'Cannot find any translated DOIs. Try to request DOI first.')
        return self.__dois