from bs4 import BeautifulSoup
from urllib.request import urlopen
from newspaper import Article
from config import Config
from pymongo import MongoClient
from urllib.parse import urlsplit, urlunsplit,urlparse
import urllib.parse, argparse, datetime, sys, os, ssl

#p = Periodicos()
conf = Config()
client = MongoClient(username=conf.user, password= conf.password, host=conf.direction, port=conf.port)

def guardarEnBBDD(url,texto):

    global p
    global conf
    global client
    urlLocal = urlsplit(url)
    p.periodicos[f'{urlLocal.scheme}://{urlLocal.netloc}/'] = True
    post = {"url"  : f"{url}",
            "title": f"{texto.get('title')}",
            "text" : f"{texto.get('text')}",
        #    "point": f"{punto}",
            "date" : datetime.datetime.utcnow()}
    db = client.Noticias
    noticia = db.noticia
    post_id = noticia.insert_one(post).inserted_id
    print(f'Insertada nueva noticia con id: {post_id}, con url: {url}')

def getTexto(url):
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

        a = Article(url)
        a.download()
        a.parse()
        if a.text == '':
            a.text = getTexto(url)
        print('\n')
    except Exception:
        a.text = getTexto(url)
        a.title = input('Introduce el titulo de la noticia: ')

    return {'title': a.title, 'text': a.text}

def fixURL(url, href):
    if 'http://' in href.lower() or 'https://' in href.lower():
        return href
    elif 'http:/' in href.lower() or 'https:/' in href.lower():
        return f'{url}{href[href.find("/",7)+1:]}'
    else:
        return urllib.parse.urljoin(url, href)


def elegirNoticia(url,palabra):
    header = {'User-Agent' :'Mozilla/5.0 (Windows NT 6.1; Win64; x64)'}
    req = urllib.request.Request(url, headers=header)
    if (not os.environ.get('PYTHONHTTPSVERIFY', '') and
            getattr(ssl, '_create_unverified_context', None)):
            ssl._create_default_https_context = ssl._create_unverified_context
    page = urlopen(req)
    html = page.read()
    soup = BeautifulSoup(html, 'html.parser')
    lista = []
    urls = set()
    for link in soup.find_all('a'):
        if palabra.lower() in str(link).lower() and not urllib.parse.urljoin(url,str(link.get('href'))) in urls:
            lista.append(link)
            if link.get('href') != None:
                urls.add(fixURL(url,str(link.get('href').replace(" ",""))))
    if len(lista) > 1:
        lista = list(set(lista))
        for index, element in enumerate(lista):
            print(f'{index}: {element}\n')
        try:
            inp = int(input('Selecciona un número de los anteriores: '))

            if inp in range(0, len(lista)):
                return fixURL(url,str(lista[inp].get('href')).replace(" ", ""))
            else:
                print('El numero no está en rango,saliendo')
                sys.exit(1)
        except KeyboardInterrupt:
            print('Siguiente periodico')

    elif len(lista) == 1:
        return fixURL(url,str(lista[0].get('href')).replace(" ", ""))
    else:
        print(f'No hay noticias con la palabra {palabra} en {url}, vamos al siguiente')

def analizarTextos(palabra):
    with open('periodicos.txt','r') as f:
        urls = f.read().split()
        for url in urls:
            urlNoticia = elegirNoticia(url,palabra)
            if (urlNoticia):
                texto = recolectarTexto(urlNoticia)
    #            punto = emocionesTexto(texto.get(text))
                if (texto.get('text') != ''):
                    guardarEnBBDD(urlNoticia , texto)

def parseArg():
    parser = argparse.ArgumentParser()
    parser.add_argument('-w','--word', help='Word to search')
    args = parser.parse_args()
    return args.word

def main():
    palabraaBuscar = parseArg()
    analizarTextos(palabraaBuscar)

if __name__ == '__main__':
    main()