from ParsePubMed import ParsePubMed,ExceptionHandler
from Questions import Questions
from DBConnector import DBConnector
from LLMapi import LLMapi
from ParsePubMedCentral import ParsePubMedCentral
from PubMedIdTranslator import PubMedIdTranslator
from PubMedCitations import PubMedCitations
from datetime import datetime

class Crawler:
    DEBUG:bool = True
    LLM_API:LLMapi = LLMapi(URL='http://10.4.24.103',verbose=DEBUG)
    DB_connector:DBConnector = DBConnector(database_name='eDNAqua',collection_name='Articles',verbose=DEBUG)
    PMCitations:PubMedCitations = PubMedCitations(DEBUG)

    def __init__(self,DOI:str=None,ancestors:list=None, steps_allowed:int=100, verbose:bool=True,log=None):
        ExceptionHandler.checkType(verbose,'verbose',bool)
        self.__verbose = verbose
        
        ExceptionHandler.checkProperty(log,exception_text='log must be the file handler, not None')
        self.__log = log
        
        ExceptionHandler.checkType(DOI,'DOI',str)
        self.__DOI = DOI
        
        ExceptionHandler.checkType(ancestors,'ancestors',{list,None.__class__})
        if ancestors is None or len(ancestors) == 0:
            self.__ancestors = list()
            self.__ancestor = self.__DOI
        else:
            for element in ancestors:
                ExceptionHandler.checkType(element,'element',str)
            self.__ancestors = ancestors
            self.__ancestor = ancestors[-1]
        self.__ancestors.append(self.__DOI)
        
        ExceptionHandler.checkType(steps_allowed,'steps_allowed',int)
        self.__steps_allowed = steps_allowed
        
        self.__step = len(ancestors)
        if self.__step > steps_allowed:
            self.__log.write(f'{datetime.now()} [Message] {self.__DOI}: Allowed steps limit has been reached\n')
            if self.__verbose: print(f'{self.__DOI}: Allowed steps limit has been reached')
            raise RuntimeError('Allowed steps limit has been reached')
            
        if Crawler.DB_connector.collection.find_one({'DOI':self.__DOI}) is not None:
            self.__log.write(f'{datetime.now()} [Message] {self.__DOI}: Paper already in database\n')
            if self.__verbose: print(f'{self.__DOI}: Paper already in database')
            raise AttributeError('Paper already in database')
        

    def request(self) -> None:
        self.__log.write(f'{datetime.now()} [Message] {self.__DOI}: Requesting PubMed...\n')
        if self.__verbose: print(f'{self.__DOI}: Requesting PubMed...')
        result = self.__PubMedRequester(ParsePubMed,PubMedIdTranslator.DOItoPubMed,PubMedIdTranslator.PubMedtoDOI)
        if result is None:
            self.__log.write(f'{datetime.now()} [Message] {self.__DOI}: PubMed didn`t responded well. Trying with PubMed Central...\n')
            if self.__verbose: print(f'{self.__DOI}: PubMed didn`t responded well. Trying with PubMed Central...')
            result = self.__PubMedRequester(ParsePubMedCentral,
                                      PubMedIdTranslator.DOItoPubMedCentral,
                                      PubMedIdTranslator.PubMedCentraltoDOI)
            
        if result is None:
            self.__log.write(f'{datetime.now()} [Message] {self.__DOI}: Cannot find given DOI\n')
            if self.__verbose: print(f'{self.__DOI}: Cannot find given DOI')
            raise ValueError(f'Cannot find given DOI: {self.__DOI}')
        
        self.__log.write(f'{datetime.now()} [Message] {self.__DOI}: Processing references...')
        if self.__verbose: print(f'{self.__DOI}: Processing references...')
        for doi in [r for r in result if r is not None]:
            try:
                new_article = Crawler(doi,self.__ancestors,self.__steps_allowed,self.__verbose,log=self.__log)
                new_article.request()
            except ValueError as e:
                self.__log.write(f'{datetime.now()} [Error] {self.__DOI}: {e}')
                print(e)
        self.__log.write(f'{datetime.now()} [Message] {self.__DOI}: Processing citations...\n')
        if self.__verbose: print(f'{self.__DOI}: Processing citations...')
        citations = Crawler.PMCitations(self.__DOI)
        for doi in citations:
            try:
                new_article = Crawler(doi,self.__ancestors,self.__steps_allowed,self.__verbose,log=self.__log)
                new_article.request()
            except ValueError as e:
                self.__log.write(f'{datetime.now()} [Error] {self.__DOI}: {e}')
                print(e)
        self.__log.write(f'{datetime.now()} [Message] {self.__DOI}: Processing finished.\n')
        if self.__verbose: print(f'{self.__DOI}: Processing finished.')
        
    
    def __PubMedRequester(self,parser_class,id_translator1, id_translator2) -> list:
        try:
            pmid = id_translator1(self.__DOI)
            if pmid is None or pmid == 0:
                raise ValueError('')
            self.__log.write(f'{datetime.now()} [Message] {self.__DOI}: DOI translated\n')
            if self.__verbose: print(f'{self.__DOI}: DOI translated')
            parser = parser_class(pmid,self.__verbose)
            self.__log.write(f'{datetime.now()} [Message] {self.__DOI}: Paper downloaded\n')
            if self.__verbose: print(f'{self.__DOI}: Paper downloaded')
        except ValueError:
            self.__log.write(f'{datetime.now()} [Message] {self.__DOI}: Canot process given ID\n')
            if self.__verbose: print(f'{self.__DOI}: Cannot process given ID')
            return None
        self.__log.write(f'{datetime.now()} [Message] {self.__DOI}: Asking LLM...\n')
        if self.__verbose: print(f'{self.__DOI}: Asking LLM...')
        processing = self.__asking__(parser.Methods if len(parser.Methods) > 0 else parser.Content)
        self.__log.write(f'{datetime.now()} [Message] {self.__DOI}: LLM responded\n')
        if self.__verbose: print(f'{self.__DOI}: LLM responded')
        params = [self.__DOI,parser.Title,parser.Content,parser.Abstract,parser.Intro,parser.Methods,
                                    parser.Results,parser.Discussion,self.__ancestor,self.__step]
        params += processing
        references = [doi for doi in [id_translator2(pmid) for pmid in parser.References] if doi is not None]
        params.append(','.join(references))
        Crawler.DB_connector.insert(*params)
        self.__log.write(f'{datetime.now()} [Message] {self.__DOI}: Saved to database\n')
        if self.__verbose: print(f'{self.__DOI}: Saved to database')
        
        return references

    def __asking__(self,text:str=None) -> list:
        ExceptionHandler.checkType(text,'text',str)
        responses = list()
        r1 = Crawler.LLM_API.ask(Questions.Q1,text)['Answer']
        if r1.startswith('yes') or r1.startswith('YES') or r1.startswith('Yes'):
            r1_2 = Crawler.LLM_API.ask(Questions.Q1_2,text)['Answer']
            responses.append(not r1_2.startswith('yes') and not r1_2.startswith('YES') and not r1_2.startswith('Yes'))
        else:
            responses.append(False)
        if not responses[0]:
            return responses
        for i in range(1,10):
            responses.append(Crawler.LLM_API.ask(Questions._questions[i],text)['Answer'])
        return responses