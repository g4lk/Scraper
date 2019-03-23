from periodicos import Periodicos
from config import Config
from pymongo import MongoClient
import argparse, datetime

conf = Config()
client = MongoClient(username=conf.user, password= conf.password, host=conf.direction, port=conf.port)

def guardarEnBBDD(noticias,palabras):

    # Creamos el diccionario (json) que introduciremos en la base de datos
    global client
    # Creamos la conexion a la base de datos y la coleccion que utilizaremos e insertamos
    db = client.Noticias
    noticia = db.noticia
    if not noticias:
        print('No hay ninguna noticia a guardar')
    else:
        post_ids = noticia.insert_many([{"url": noticia.url,
                                         "title": noticia.title,
                                         "text": noticia.text,
                                         "date": datetime.datetime.utcnow(),
                                         "words": ",".join(palabras)} for noticia in noticias]).inserted_ids
        print(f'Insertadas noticias con ids {",".join([str(post_id) for post_id in post_ids])}')
        print('fin')

def analizarTextos(palabras):
    # Por cada periodico elegimos una noticia y recopilamos en base de datos
    p = Periodicos()
    noticias = p.search_news(palabras)
    guardarEnBBDD(noticias, palabras)

def parseArg():
    # Recogemos argumentos
    parser = argparse.ArgumentParser()
    parser.add_argument('-w','--words', help='Words to search')
    args = parser.parse_args()
    return args.words.lower().split(",")

def main():
    palabrasaBuscar = parseArg()
    analizarTextos(palabrasaBuscar)

if __name__ == '__main__':
    main()
