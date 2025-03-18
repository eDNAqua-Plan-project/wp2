import requests
import json
from ParsePubMed import ExceptionHandler

class PubMedIdTranslator:
    URL:str = 'https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/'
    
    def __init__(self):
        raise ModuleNotFoundError('This module is not able to function as an object. You cannot instantiate.')
        
    def __URI__(ids:object=None,idtype:str=None) -> str:
        URI = PubMedIdTranslator.URL + '?format=json&ids='
        URI += str(ids) if ids.__class__ is not list else ','.join([str(i) for i in ids])
        if ExceptionHandler.checkProperty(idtype,raise_exception=False):
            return URI
        return URI + f'&idtype={idtype}'
    
    def translate(ids:object=None,tr_from:str=None,tr_to:str=None,raise_exception:bool=True) -> object:
        ExceptionHandler.checkType(ids,'ids',{str,int,list})
        ExceptionHandler.checkType(tr_from,'idtype',{str,None.__class__})
        ExceptionHandler.checkType(tr_to,'idtype',{str,None.__class__})
        ExceptionHandler.checkType(raise_exception,'raise_exception',bool)
        if tr_from not in {"pmcid", "pmid", "doi"}:
            raise AttributeError('Value of tr_from attribute must be "pmcid", "pmid" or "doi"')
        if tr_to not in {"pmcid", "pmid", "doi"}:
            raise AttributeError('Value of tr_to attribute must be "pmcid", "pmid" or "doi"')
        URI = PubMedIdTranslator.__URI__(ids,tr_from)
        response = requests.get(URI)
        ExceptionHandler.checkConnection(response)
        ExceptionHandler.checkContent(response)
        content = json.loads(response.content.decode())
        if 'status' in content['records'][0].keys() and content['records'][0]['status'] == 'error':
            if raise_exception:
                raise RuntimeError(f'Cannot find given {tr_from}: {ids}')
            return None
        try:
            return content['records'][0][tr_to]
        except:
            return None
        
    def DOItoPubMed(DOI:str=None) -> int:
        ExceptionHandler.checkType(DOI,'DOI',str)
        pmid = PubMedIdTranslator.translate(DOI,'doi','pmid',raise_exception=False)
        if pmid is None:
            return 0
        return int(pmid)
        
    def PubMedtoDOI(PMID:int=None) -> str:
        ExceptionHandler.checkType(PMID,'PMID',str)
        return PubMedIdTranslator.translate(PMID,'pmid','doi',raise_exception=False)
        
    def DOItoPubMedCentral(DOI:str=None) -> str:
        ExceptionHandler.checkType(DOI,'DOI',str)
        return PubMedIdTranslator.translate(DOI,'doi','pmcid',raise_exception=False)
    
    def PubMedCentraltoDOI(PMCID:str=None) -> str:
        ExceptionHandler.checkType(PMCID,'PMCID',str)
        return PubMedIdTranslator.translate(PMCID,'pmcid','doi',raise_exception=False)
        
    def PubMedtoDOI(PMID:int=None) -> str:
        ExceptionHandler.checkType(PMID,'PMID',int)
        return PubMedIdTranslator.translate(PMID,'pmid','doi',raise_exception=False)
        
    def PubMedtoPubMedCentral(PMID:int=None) -> str:
        ExceptionHandler.checkType(PMID,'PMID',int)
        return PubMedIdTranslator.translate(PMID,'pmid','pmcid',raise_exception=False)
        
    def PubMedCentraltoPubMed(PMCID:str=None) -> int:
        ExceptionHandler.checkType(PMCID,'PMCID',str)
        pmid = PubMedIdTranslator.translate(PMCID,'pmcid','pmid',raise_exception=False)
        if pmid is None:
            return 0
        return int(pmid)