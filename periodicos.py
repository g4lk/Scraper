from bs4 import BeautifulSoup
import ssl, urllib,os,re,requests,sys,spacy,threading
from urllib.parse import urlparse
from color import Color
from collections import Counter
from config import DB
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn import svm


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
        self.__db_con = DB()
        self.__lock = threading.Lock()
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


        #self.__nlp = spacy.load('es_core_news_sm')
        self.__results = []

    def load_newspapers(self):
        ''' Por si se quiere el diccionario de periodico-clase creado '''

        return list(self.__periodicos.keys())

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
                result = ' '.join([p.text for p in ps])
                return result
            else:
                ps = tag.find_all('p')
                result = ' '.join([p.text for p in ps])
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

    def __process(self,url,css):
        ''' Procesamos una noticia a través de su url'''

        soup_new = self.__scraper(url)
        text = self.__search_text(soup_new, css)
        title = self.__search_title(soup_new)
        return (soup_new,text,title)

    def __extract_newspaper(self,url):
        ''' Extraemos la clave que existe en el diccionario de periodicos de una url '''

        newspaper = urlparse(url)
        if 'elnacional' in newspaper.netloc or 'elperiodico' in newspaper.netloc:
            return f'{newspaper.scheme}://{newspaper.netloc}/es'
        else:
            return f'{newspaper.scheme}://{newspaper.netloc}/'


    def __get_words(self,doc):
        '''Cogemos verbos, sustantivos y demás palabras que tengan relevancia
         y escogemos de estas las más repetidas en el texto.'''

        words = [token.text for token in doc if token.is_stop != True and token.is_punct != True and token.pos_ != "CONJ" and token.pos_ != "ADP" and token.pos_ != "VERB"]
        verbs = [token.lemma_ for token in doc if token.pos_ == 'VERB']
        nouns = [token.text for token in doc if token.is_stop != True and token.is_punct != True and token.pos_ == "NOUN"]

        word_freq = Counter(words)
        common_words = word_freq.most_common(10)

        verb_freq = Counter(verbs)
        common_verbs = verb_freq.most_common(10)

        noun_freq = Counter(nouns)
        common_nouns = noun_freq.most_common(10)

        commons = list(set(common_nouns).union(set(common_words)).union(set(common_verbs)))

        return [common[0].lower() for common in commons]

    def __extract_words(self,text=None,title=None):
        '''
        Nos dan la noticia y sacamos las palabras importantes para buscar las demas noticias con spacy
        :param text: Cuerpo de una noticia
        :param text: Titulo de una noticia
        :return words: devolvemos palabras mas importantes de la noticia
        '''

        words = set()
        if text:
            doc = self.__nlp(text)
            words_text = self.__get_words(doc)
            words.update(words_text)
        if title:
            doc = self.__nlp(title)
            words_title = self.__get_words(doc)
            words.update(words_title)

        return list(words)

    def search_news_by_url(self, url):
        '''
        Extraemos datos de la url, guardamos en resultados. Procesamos la noticia,
        para despues extraer las palabras mas comunes a buscar en los otros periodicos

        :param url: url inicial que procesaremos y de la que sacaremos las palabras mas comunes para buscar en los siguientes periodicos
        '''

        nwp = self.__extract_newspaper(url)
        css = self.__periodicos.pop(nwp)
        soup_new, text, title = self.__process(url, css)
        words = self.__extract_words(text, title)
        score = self.__search_score(text, title, words)
        new = Noticia(title=title, text=text, url=url, score=score)
        self.__results.append(new)
        self.search_news_by_words(words)

        return (self.__results,words)

    def __worker(self,words,url,css_class,auto):
        '''
        Recorremos todos los link buscando las palabras en estos, y los que las contengan,
        nos recorremos la noticia y la recogemos. Por ultimo damos por defecto la que mas
        palabras contenga de las buscadas. Si no es esta doy la opción de escoger una de las otras.
        :param words: palabras a buscar
        :param url: url de la que tiramos
        :param css_class: clase de html
        :return:
        '''


        soup = self.__scraper(url)
        news = []
        urlsScrapeadas = set()
        tagsFiltered = [a for a in soup.find_all('a') if a.get('href')]
        for a in tagsFiltered:
            try:
                urlfixed = self.__fix_url(url,str(a.get('href').replace(" ","")))
                #palabras_titulo = self.__extract_words(title=str(a).lower())

                if url in urlfixed and not urlfixed in urlsScrapeadas and any(word.lower() in str(a).lower() for word in words):
                    urlsScrapeadas.add(urlfixed)
                    soup_new,text,title = self.__process(urlfixed,css_class)

                    if text:
                        score = self.__search_score(text,title,words)
                        if score > 0:
                            new = Noticia(title=title,text=text,url=urlfixed,score=score)
                            news.append(new)
            except Exception:
                print(f'Ha fallado algo en {urlfixed}')


        self.__select(news,url,auto)

    def __select(self,news,url,auto):
        '''
        Hacemos un metodo seguro a multithreading para eleccion de noticias.
        '''

        self.__lock.acquire()
        if len(news) != 0:
            news.sort(key=lambda x: x.score, reverse=True)
            new = news[0]
            if auto:
                self.__results.append(new)
            else:
                respuesta = str(input(f'[+] ¿Es \'{new.title}\' con url {new.url} la noticia? S/N: '))
                if respuesta.lower() == 's':
                    self.__results.append(new)
                else:
                    n = self.__select_new(news)
                    if n != -1 and n < len(news):
                        self.__results.append(news[n])
        else:
            print(f'[-] No hay noticias con las palabras buscadas en {url}')
        self.__lock.release()


    def search_news_by_words(self,words,auto):
        '''
        Cogemos un mapa de periodicos con las clases que hay que buscar,
        y llamamos a los threads para que busquen las noticias.
        Devolvemos una lista con todos los objetos Noticia recolectados
        '''
        threads = []
        for url,css_class in self.__periodicos.items():
            threads.append(threading.Thread(target=self.__worker, args=(words,url,css_class,auto)))
            threads[-1].start()

        # Esperamos a que todos los thread hayan terminado
        for thread in threads:
            thread.join()

        return self.__results

    def __sort_results(self):
        '''
        Recibe las noticias sin ordenar y las ordena
        :return: Titulo y texto de cada noticia, en el orden dado de los periodicos
        '''

        noticias = []
        for periodico in self.__periodicos.keys():
            nombre_periodico = urlparse(periodico).netloc
            if any(nombre_periodico in x.url for x in self.__results):
                noticia = next(item for item in self.__results if nombre_periodico in item.url)
                noticias.append(f"{noticia.title}\n{noticia.text}")
            else:
                noticias.append('')

        return noticias

    def process_results(self):
        '''
        Ordenamos las noticias recogidas, luego aplicamos tf-idf
        para transformar los textos a una matriz de valores interpretable por
        la operacion coseno de similaridad. Por último a esto aplicamos
        OneClassSVM para clasificar los nuevos textos.
        :return similarity: se devuelva la similaridad de los textos recien capturados
        :return one_class: se devuelve la clasificación aplicada por el algoritmo
        '''

        noticias = self.__sort_results()

        vect = TfidfVectorizer()
        tfidf = vect.fit_transform(noticias)
        similarity = cosine_similarity(tfidf)
        all_similarities = self.__db_con.get_similarities()
        clf = svm.OneClassSVM(nu=0.5, gamma='scale')
        clf.fit(all_similarities)
        one_class = clf.predict(similarity)
        return similarity,one_class

