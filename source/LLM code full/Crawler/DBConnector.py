from pymongo import MongoClient
import json
from ParsePubMed import ExceptionHandler

class DBConnector:
    DB_addr: str = 'mongodb://127.0.0.1'
    DB_port: int = 27017
    DB_name: str = 'test'
    Collection_name: str = 'test'

    client: MongoClient = None
    db = None
    collection = None

    def __init__(self,database_name: str=None, collection_name: str=None,URL:str=None,port:int=None,verbose:bool=True):
        if ExceptionHandler.checkProperty(database_name,raise_exception=False) == False:
            ExceptionHandler.checkType(database_name,'database_name',str)
            DBConnector.DB_name = database_name
        if ExceptionHandler.checkProperty(collection_name,raise_exception=False) == False:
            ExceptionHandler.checkType(collection_name,'collection_name',str)
            DBConnector.Collection_name = collection_name
        ExceptionHandler.checkType(URL,'URL',{str,None.__class__})
        if not ExceptionHandler.checkProperty(URL,raise_exception=False):
            DBConnector.DB_addr = URL
        ExceptionHandler.checkType(port,'port',{int,None.__class__})
        if not ExceptionHandler.checkProperty(port,raise_exception=False):
            DBConnector.DB_port = port
        ExceptionHandler.checkType(verbose,'verbose',{bool,int})
        if DBConnector.client is None:
            if verbose:
                print(f'Connecting to database {DBConnector.DB_addr} on port {DBConnector.DB_port}...',end='')
            DBConnector.client = MongoClient(DBConnector.DB_addr,DBConnector.DB_port)
        if verbose:
            print('Client connected')

        ## testing database
        if DBConnector.DB_name not in DBConnector.client.list_database_names() and verbose:
            print(f'Database "{DBConnector.DB_name}" does not exist. This will be created now.')
        elif verbose:
            print(f'Connecting to database "{DBConnector.DB_name}"')
        DBConnector.db = DBConnector.client[DBConnector.DB_name]
        if verbose: 
            print('Connected')
        if DBConnector.Collection_name not in DBConnector.db.list_collection_names() and verbose:
            print(f'Collection "{DBConnector.Collection_name}" does not exist. This will be created now.')
        elif verbose:
            print(f'Selecting collection "{DBConnector.Collection_name}"')
        DBConnector.collection = DBConnector.db[DBConnector.Collection_name]
        if verbose:
            print('OK')

    def insert(self, DOI:str=None, title:str=None, content:str=None, abstract:str=None, intro:str=None, methods:str=None, 
               results:str=None, discussion:str=None, ancestor:str=None,step:int=None, Q1:bool=None, Q2:str=None, Q3:str=None, Q4:str=None, 
               Q5:str=None, Q6:str=None, Q7:str=None, Q8:str=None, Q9:str=None, Q10:str=None,references:str=None):
        self.__validate_insert(DOI=DOI,title=title,content=content,abstract=abstract,intro=intro,methods=methods,
                   results=results, discussion=discussion,ancestor=ancestor,step=step,Q1=Q1,Q2=Q2,Q3=Q3,Q4=Q4,Q5=Q5,Q6=Q6,Q7=Q7,
                               Q8=Q8,Q9=Q9,Q10=Q10,references=references)
        doc = dict(DOI=DOI,title=title,content=content,abstract=abstract,intro=intro,methods=methods,
                   results=results,discussion=discussion,ancestor=ancestor,step=step,Q1=Q1)
        for name,value in zip(('Q2','Q3','Q4','Q5','Q6','Q7','Q8','Q9','Q10'),(Q2,Q3,Q4,Q5,Q6,Q7,Q8,Q9,Q10)):
            if value is not None:
                doc[name] = value
        doc['references']=references

        DBConnector.collection.insert_one(doc)

    def select(self, DOI:str=None, title:str=None, content:str=None, abstract:str=None,step:int=None, intro:str=None,
               methods:str=None, results:str=None, discussion:str=None, ancestor:str=None, Q1:bool=None, Q2:str=None,
               Q3:str=None, Q4:str=None,Q5:str=None, Q6:str=None, Q7:str=None, Q8:str=None, Q9:str=None, Q10:str=None,references:str=None) -> tuple:
        self.__validate_select(DOI=DOI,title=title,content=content,abstract=abstract,intro=intro,methods=methods,
results=results,discussion=discussion,ancestor=ancestor,step=step,Q1=Q1,Q2=Q2,Q3=Q3,Q4=Q4,Q5=Q5,Q6=Q6,Q7=Q7,Q8=Q8,Q9=Q9,Q10=Q10,references=references)
        query = self.__make_query(DOI=DOI,title=title,content=content,abstract=abstract,intro=intro,methods=methods,
                   results=results,discussion=discussion,ancestor=ancestor,step=step,Q1=Q1,Q2=Q2,Q3=Q3,Q4=Q4,Q5=Q5,Q6=Q6,Q7=Q7,Q8=Q8,Q9=Q9,Q10=Q10,references=references)
        response = tuple(DBConnector.collection.find(query))
        return response

    def __validate_insert(self,DOI:str=None, title:str=None, content:str=None, abstract:str=None, intro:str=None,
                          methods:str=None,results:str=None, discussion:str=None, ancestor:str=None,step:int=None, Q1:bool=None, 
                          Q2:str=None, Q3:str=None, Q4:str=None, Q5:str=None, Q6:str=None, Q7:str=None, Q8:str=None, 
                          Q9:str=None, Q10:str=None,references:str=None):
        ExceptionHandler.checkProperty(DOI,exception_text='DOI number is necessary here.')
        ExceptionHandler.checkProperty(title,exception_text='Title is necessary here.')
        ExceptionHandler.checkProperty(content,exception_text='Content is necessary here.')
#         ExceptionHandler.checkProperty(abstract,exception_text='Abstract is necessary here.')
#         ExceptionHandler.checkProperty(intro,exception_text='Introduction is necessary here.')
#         ExceptionHandler.checkProperty(methods,exception_text='Materials and methods is necessary here.')
#         ExceptionHandler.checkProperty(results,exception_text='Results is necessary here.')
#         ExceptionHandler.checkProperty(discussion,exception_text='Discussion is necessary here.')
        ExceptionHandler.checkProperty(ancestor,exception_text='Ancestor is necessary here.')
        ExceptionHandler.checkProperty(step,exception_text='Step is necessary here.')
        ExceptionHandler.checkProperty(Q1,exception_text='Q1 is necessary here.')
        ExceptionHandler.checkProperty(references,exception_text='References are necessary')
        
        ExceptionHandler.checkType(DOI,'DOI number',str)
        ExceptionHandler.checkType(title,'title',str)
        ExceptionHandler.checkType(content,'content',str)
        ExceptionHandler.checkType(abstract,'abstract',{str,None.__class__})
        ExceptionHandler.checkType(intro,'intro',{str,None.__class__})
        ExceptionHandler.checkType(methods,'methods',{str,None.__class__})
        ExceptionHandler.checkType(results,'results',{str,None.__class__})
        ExceptionHandler.checkType(discussion,'discussion',{str,None.__class__})
        ExceptionHandler.checkType(ancestor,'ancestor',str)
        ExceptionHandler.checkType(step,'step',int)
        ExceptionHandler.checkType(Q1,'Q1',bool)
        ExceptionHandler.checkType(Q2,'Q2',{str,None.__class__})
        ExceptionHandler.checkType(Q3,'Q3',{str,None.__class__})
        ExceptionHandler.checkType(Q4,'Q4',{str,None.__class__})
        ExceptionHandler.checkType(Q5,'Q5',{str,None.__class__})
        ExceptionHandler.checkType(Q6,'Q6',{str,None.__class__})
        ExceptionHandler.checkType(Q7,'Q7',{str,None.__class__})
        ExceptionHandler.checkType(Q8,'Q8',{str,None.__class__})
        ExceptionHandler.checkType(Q9,'Q9',{str,None.__class__})
        ExceptionHandler.checkType(Q10,'Q10',{str,None.__class__})
        ExceptionHandler.checkType(references,'references',str)

    def __validate_select(self,**kw_args):
        for key,value in kw_args.items():
            if key != 'Q1':
                ExceptionHandler.checkType(value,key,{str,None.__class__})
            else:
                ExceptionHandler.checkType(value,key,{bool,None.__class__})

    def __make_query(self,**kw_args):
        query = dict()
        for key,value in kw_args.items():
            try:
                ExceptionHandler.checkProperty(value)
                query[key] = value
            except:
                pass
        return query

    @property
    def dbName(self) -> str:
        return DBConnector.DB_name
    @property
    def collectionName(self) -> str:
        return DBConnector.Collection_name
    @property
    def URI(self) -> str:
        return f'{DBConnector.DB_addr}:{DBConnector.DB_port}'
    @property
    def port(self) -> int:
        return DBConnector.DB_port
    @property
    def URL(self) -> str:
        return DBConnector.DB_addr