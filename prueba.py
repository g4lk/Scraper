from bs4 import BeautifulSoup
from urllib.request import urlopen
from newspaper import Article
from config import Config
from pymongo import MongoClient
from urllib.parse import urlsplit
import urllib.parse, argparse, datetime, sys, os, ssl

conf = Config()
client = MongoClient(username=conf.user, password= conf.password, host=conf.direction, port=conf.port)

def guardarEnBBDD(url,texto,palabras):

    # Creamos el diccionario (json) que introduciremos en la base de datos
    global client
    post = {"url"  : url,
            "title": texto.get('title'),
            "text" : texto.get('text'),
            "date" : datetime.datetime.utcnow(),
            "words": ",".join(palabras)}
    # Creamos la conexion a la base de datos y la coleccion que utilizaremos e insertamos
    db = client.Noticias
    noticia = db.noticia
    post_id = noticia.insert_one(post).inserted_id
    print(f'Insertada nueva noticia con id: {post_id}, con url: {url}')

def getTexto(url):
    # Recogemos el texto (sin saltos de linea) cuando no puede automaticamente
    print(f'Porfavor, introduce el texto de la noticia desde {url} sin saltos de linea. No he sido capaz de descargarlo yo:\n')
    content = []
    while True:
        line = input()
        if line:
            content.append(line)
        else:
            break
    return '\n'.join(content)

def recolectarTexto(url):
    try:
        # Recogemos automaticamente noticia y titulo
        a = Article(url)
        a.download()
        a.parse()
        if a.text == '':
            a.text = getTexto(url)
        print('\n')
    except Exception:
        # Si no se puede lo hacemos en modo manual
        a.text = getTexto(url)
        a.title = input('Introduce el titulo de la noticia: ')

    return {'title': a.title, 'text': a.text}

def fixURL(url, href):
    # Parseamos la url para comprobación de duplicados y correcion de errores
    getElem = href.find("#")
    if 'http://' in href.lower() or 'https://' in href.lower():
        if getElem != -1:
            return href[:getElem]
        else:
            return href
    elif 'http:/' in href.lower() or 'https:/' in href.lower():
        if getElem != -1:
            return f'{url}{href[href.find("/",7)+1:getElem]}'
        else:
            return f'{url}{href[href.find("/",7)+1:]}'
    else:
        if getElem != -1:
            return urllib.parse.urljoin(url, href[:getElem])
        else:
            return urllib.parse.urljoin(url, href)


def elegirNoticia(url,palabras):
    #Creamos headers y un contexto de ssl para evitar errores o bloqueos
    header = {'User-Agent' :'Mozilla/5.0 (Windows NT 6.1; Win64; x64)'}
    req = urllib.request.Request(url, headers=header)
    if (not os.environ.get('PYTHONHTTPSVERIFY', '') and
            getattr(ssl, '_create_unverified_context', None)):
            ssl._create_default_https_context = ssl._create_unverified_context
    # Hacemos la peticion y parseamos el html
    page = urlopen(req)
    html = page.read()
    soup = BeautifulSoup(html, 'html.parser',from_encoding="iso-8859-1")
    # Guardamos en una lista todos los tags a que tengan una de las palabras metidas en args
    # y guardamos un conjunto de urls para comprobar duplicados de url
    lista = []
    urls = set()
    for link in soup.find_all('a'):
            if link.get('href'):
                urlfixed = fixURL(url,str(link.get('href').replace(" ","")))
            # Si hay alguna palabra en el link y no está ya guardada la metemos
                if any(palabra in str(link).lower() for palabra in palabras) and not urlfixed in urls:
                    lista.append(link)
                    urls.add(urlfixed)
    # Si tenemos solo un atributo lo guardamos, si tenemos mas de uno elegimos cual guardar, y si no, no queremos ninguno.
    if len(lista) > 1:
        lista = list(set(lista))
        for index, element in enumerate(lista):
            print(f'{index}: {element}\n')
        try:
            inp = int(input('Selecciona un número de los anteriores o -1 si no quieres ninguno: '))

            if inp in range(0, len(lista)):
                return fixURL(url,str(lista[inp].get('href')).replace(" ", ""))
            elif inp == -1:
                print(f'No hay noticias que te satisfazcan en {url}, vamos al siguiente')
            else:
                print('El numero no está en rango,saliendo')
                sys.exit(1)
        except Exception:
            print('Siguiente periodico')
    elif len(lista) == 1:
        return fixURL(url,str(lista[0].get('href')).replace(" ", ""))
    else:
        print(f'No hay noticias con las palabras {",".join(palabras)} en {url}, vamos al siguiente')

def analizarTextos(palabras):
    # Por cada periodico elegimos una noticia y recopilamos en base de datos
    with open('periodicos.txt','r') as f:
        urls = f.read().split()
        for url in urls:
            urlNoticia = elegirNoticia(url,palabras)
            if (urlNoticia):
                texto = recolectarTexto(urlNoticia)
                if (texto.get('text') != ''):
                    guardarEnBBDD(urlNoticia , texto, palabras)

def parseArg():
    # Recogemos argumentos
    parser = argparse.ArgumentParser()
    parser.add_argument('-w','--words', help='Words to search')
    args = parser.parse_args()
    return args.words.split(",")

def main():
    palabrasaBuscar = parseArg()
    analizarTextos(palabrasaBuscar)

if __name__ == '__main__':
    main()