from bs4 import BeautifulSoup
from urllib.request import urlopen
from newspaper import Article
from config import *
from pymongo import MongoClient
import urllib.parse, argparse, datetime, sys

def guardarEnBBDD(url,texto):
    conf = Config()
    client = MongoClient(username=conf.user, password= conf.password, host=conf.direction, port=conf.port)
    
    post = {"url"  : f"{url}",
            "title": f"{texto.get('title')}",
            "text" : f"{texto.get('text')}",
        #    "point": f"{punto}",
            "date" : datetime.datetime.utcnow()}
    db = client.Noticias
    noticia = db.noticia
    post_id = noticia.insert_one(post).inserted_id
    print(f'Inserted new post with id {post_id} from url: {url}')

def recolectarTexto(url):
    try:
        a = Article(url)
        a.download()
        a.parse()
    except Exception:
        print(f'Couldnt get the article {url}')
        a.text = ''
        a.title = ''

    return {'title': a.title, 'text': a.text}

def elegirNoticia(url,palabra):
    page = urlopen(url)
    html = page.read()
    soup = BeautifulSoup(html, 'html.parser')
    lista = []

    for link in soup.find_all('a'):
        if palabra in str(link):
            lista.append(link)

    if len(lista) > 0:
        lista = list(set(lista))
        for index, element in enumerate(lista):
            print(f'{index}: {element}\n')

        inp = int(input('Selecciona un número de los anteriores: '))

        if inp in range(0, len(lista) - 1):
            return urllib.parse.urljoin(url,lista[inp].get('href'))
        else:
            print('This number isn\'t in range, exiting')
            sys.exit(1)
    else:
        print(f'There aren\'t news with the word {palabra} on {url}, exiting')
        sys.exit(1)

def analizarTextos(palabra):
    with open('periodicos.txt','r') as f:
        urls = f.read().split()
        for url in urls:
            urlNoticia = elegirNoticia(url,palabra)
            texto = recolectarTexto(urlNoticia)
#            punto = emocionesTexto(texto.get(text))
            guardarEnBBDD(urlNoticia , texto)

def parseArg():
    parser = argparse.ArgumentParser()
    parser.add_argument('--word', help='Word to search')
    args = parser.parse_args()
    if args("--word"):
        return args("--word")
    else:
        print('No word on args, exiting')
        sys.exit(1)

def main():
    palabraaBuscar = parseArg()
    analizarTextos(palabraaBuscar)

if __name__ == '__main__':
    main()