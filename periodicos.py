from bs4 import BeautifulSoup
import ssl, urllib,os,re,requests
from color import Color

class Noticia():
    ''' Datos necesarios para guardar en bbdd mas score para filtro'''
    def __init__(self,url=None,text=None,title=None,score=0):
        self.url = url
        self.text = text
        self.title = title
        self.score = score



class Periodicos():
    def __init__(self):
        self.__colores = Color()
        self.__periodicos = {   "https://www.elnacional.cat/es":"article-body",
                                "https://www.elmundo.es/":"ue-l-article__body ue-c-article__body",
                                "https://elpais.com/":"articulo-cuerpo",
                                "https://www.lavanguardia.com/":"story-leaf-txt-p",
                                "https://www.elperiodico.com/es/":"ep-detail-body",
                                "https://www.elconfidencial.com/":"news-body-center cms-format",
                                "https://www.eldiario.es/":"mce-body mce no-sticky-adv-socios",
                                "https://www.elindependiente.com/":"article-body p402_premium",
                                "https://www.elespanol.com/":"article-body__content",
                                "https://www.elimparcial.es/":"texto",
                                "https://www.elplural.com/":"body-content",
                                "https://www.lainformacion.com/":"content-modules",
                                "https://www.larazon.es/":"paragraph",
                                "https://www.esdiario.com/":"text CuerpoNoticia",
                                "https://www.libertaddigital.com/":"texto principal",
                                "https://okdiario.com/": "entry-content",
                                "https://www.periodistadigital.com/": "text-block",
                                "https://www.abc.es/": "contenido-articulo",
                                "https://www.20minutos.es/": "gtm-article-text",
                                "https://www.diariovasco.com/": "voc-detail voc-detail-grid",
                                "https://www.farodevigo.es/": "cuerpo_noticia",
                                "https://www.heraldo.es/": "content-modules",
                                "https://www.lasprovincias.es/": "voc-detail voc-detail-grid",
                                "https://www.diariosur.es/": "voc-detail voc-detail-grid",
                                "https://www.elnortedecastilla.es/": "voc-detail voc-detail-grid",
                                "https://www.lavozdegalicia.es/": "text"
                }

    def load_newspapers(self):
        ''' Por si se quiere el diccionario de periodico-clase creado '''
        return self.__periodicos

    def __fix_url(self,url, href):
        ''' Parser de urls '''
        getElem = href.find("#")
        if 'http://' in href.lower() or 'https://' in href.lower():
            if getElem != -1:
                return href[:getElem]
            else:
                return href
        elif 'http:/' in href.lower() or 'https:/' in href.lower():
            if getElem != -1:
                return f'{url}{href[href.find("/", 7) + 1:getElem]}'
            else:
                return f'{url}{href[href.find("/", 7) + 1:]}'
        else:
            if getElem != -1:
                return urllib.parse.urljoin(url, href[:getElem])
            else:
                return urllib.parse.urljoin(url, href)

    def __scraper(self,url):
        ''' Creamos headers y un contexto de ssl para evitar errores o bloqueos
            Luego hacemos una peticion get a la url y devolvemos el objeto bs
        '''
        header = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64)'}
        if (not os.environ.get('PYTHONHTTPSVERIFY', '') and getattr(ssl, '_create_unverified_context', None)):
            ssl._create_default_https_context = ssl._create_unverified_context
        html = requests.get(url,headers=header).content
        return BeautifulSoup(html, 'html.parser', from_encoding="utf-8")

    def __search_text(self,soup,css_class):
        ''' Buscamos la clase que contiene la noticia, y cogemos su texto'''
        tag = soup.select(f"[class='{css_class}']")
        if tag:
            tag = tag[0]
            ps = tag.find_all('p',recursive=False)
            if ps:
                result = ''.join([p.text for p in ps])
                return result
            else:
                ps = tag.find_all('p')
                result = ''.join([p.text for p in ps])
                return result

    def __search_score(self,text,title,words):
        ''' Calculamos el numero de palabras dentro de la noticia '''
        score = 0
        for word in words:
            if word.lower() in text.lower() or word.lower() in title.lower():
                score += 1
        return score

    def __search_title(self,soup):
        ''' Recogemos titulo y eliminamos simbolos raros del final '''
        title = soup.title.string
        busqueda = re.search('[\|\#\[\]\{\}\$-]',title)
        if busqueda:
            end_title = str(title[:busqueda.start()])
            end_title = end_title.replace('\n','').replace('\t','').replace('\r','').strip()
            return end_title
        else:
            return str(title).replace('\n','').replace('\t','').replace('\r','').strip()

    def __select_new(self,news):
        ''' Si no es la noticia que contenga más palabras, escogemos entre las que hemos almacenado'''
        for index,new in enumerate(news):
            print(f'\t{self.__colores.BLUE}{index}: {new.title} - {new.url}{self.__colores.END}')
        inp = int(input(f'{self.__colores.BOLD}Selecciona un número de los anteriores o -1 si no quieres ninguno: {self.__colores.END}'))
        return inp

    def search_news(self,words):
        ''' Cogemos un mapa de periodicos con las clases que hay que buscar,
        recorremos todos los link buscando las palabras en estos, y los que las contengan,
        nos recorremos la noticia y la recogemos. Por ultimo damos por defecto la que mas
        palabras contenga de las buscadas. Si no es esta doy la opción de escoger una de las otras.
        Devolvemos una lista con todos los objetos Noticia recolectados'''
        end_news = []
        for url,css_class in self.__periodicos.items():
            soup = self.__scraper(url)
            news = []
            urlsScrapeadas = set()
            tagsFiltered = [a for a in soup.find_all('a') if a.get('href')]
            for a in tagsFiltered:
                    urlfixed = self.__fix_url(url,str(a.get('href').replace(" ","")))
                    if url in urlfixed and not urlfixed in urlsScrapeadas and any(word.lower() in str(a).lower() for word in words):
                        urlsScrapeadas.add(urlfixed)
                        soup_new = self.__scraper(urlfixed)
                        text= self.__search_text(soup_new,css_class)
                        title = self.__search_title(soup_new)
                        if text:
                            score = self.__search_score(text,title,words)
                            if score > 0:
                                new = Noticia()
                                new.title = title
                                new.text = text
                                new.url = urlfixed
                                new.score = score
                                news.append(new)
            if len(news) != 0:
                new = Noticia()
                for elem in news:
                    if elem.score > new.score:
                        new = elem
                respuesta = str(input(f'[+] ¿Es \'{new.title}\' con url {new.url} la noticia? S/N: '))
                if respuesta.lower() == 's':
                    end_news.append(new)
                else:
                    n = self.__select_new(news)
                    if n != -1 and n < len(news):
                        end_news.append(news[n])
            else:
                print(f'[-] No hay noticias con las palabras buscadas en {url}')
        return end_news