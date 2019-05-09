from periodicos import Periodicos
from config import DB
from pymongo import MongoClient
import argparse, datetime,sys
from sklearn.metrics.pairwise import cosine_similarity
from sklearn import svm
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

conf = DB()

def analizarTextos(args):
    '''
    Si es una lista de palabras, buscamos pòr palabras, si no por urls y guardamos en bbdd
    :param args: Lista de palabras, o una url (String)
    '''
    global conf
    p = Periodicos()

    if type(args) == list:
        noticias = p.search_news_by_words(args)
        conf.save(noticias, args)
        similarities = p.process_results()
        conf.save_similarities(similarities,args)
    else:
        noticias,palabras = p.search_news_by_url(url)
        conf.save(noticias, palabras)
        similarities = p.process_results()
        conf.save_similarities(similarities, palabras)




def parseArg():
    '''
    Dos modos para recoger argumentos:
    - Recogemos palabras a buscar
    - Recogemos url de la que extraeremos la info para buscar las demas
    :return uno de los dos modos:
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument('-w','--words', help='Words to search')
    parser.add_argument('-u','--url', help='URL to search for')
    args = parser.parse_args()
    if args.words:
        return args.words.lower().split(",")
    elif args.url:
        return args.url
    else:
        parser.print_help()
        sys.exit(-1)

def main():
    args = parseArg()
    analizarTextos(args)

if __name__ == '__main__':
    main()