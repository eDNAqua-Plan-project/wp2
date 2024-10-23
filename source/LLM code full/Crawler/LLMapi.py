import requests
import json
from ParsePubMed import ExceptionHandler

class LLMapi:
    api_url:str = 'http://10.4.24.103'
    api_port:int = 5000

    def __init__(self,URL:str=None,port:int=None,verbose:bool=True):
        ExceptionHandler.checkType(URL,'URL',{str,None.__class__})
        if not ExceptionHandler.checkProperty(URL,raise_exception=False):
            LLMapi.api_url = URL
        ExceptionHandler.checkType(port,'port',{int,None.__class__})
        if not ExceptionHandler.checkProperty(port,raise_exception=False):
            LLMapi.api_port = port
        ExceptionHandler.checkType(verbose,'verbose',{bool,int})
        self.__verbose = verbose
        self.checkConnection()

    def request(self,endpoint:str=None,data:dict=None):
        ExceptionHandler.checkType(endpoint,'endpoint',str)
        uri = f'{self.URI}/{endpoint}'
        response = requests.post(uri,data,headers={'content-type': 'application/json'})
        ExceptionHandler.checkConnection(response)
        content = response.content.decode()
        return content
    
    def checkConnection(self):
        content = self.request(endpoint='checkConnection')
        data = json.loads(content)
        if 'Connection' in data.keys() and data['Connection'] == 'OK':
            if self.__verbose:
                print('Connection ok')
        else:
            raise requests.ConnectionError('Cannot connect with this URI')       

    def ask(self, question:str=None, article:str=None):
        ExceptionHandler.checkType(question,'question',str)
        ExceptionHandler.checkType(article,'article',str)
        content = self.request(endpoint='llm',data=json.dumps(dict(Question=question,Context=article)))
        return json.loads(content)
        
    @property
    def URI(self) -> str:
        return f'{LLMapi.api_url}:{LLMapi.api_port}'

    @property
    def URL(self) -> str:
        return LLMapi.api_url

    @property
    def port(self) -> int:
        return LLMapi.api_port