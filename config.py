from pymongo import MongoClient
import datetime

class DB():
    def __init__(self, user='URJCReadWrite',password='UniversidadReyJuanCarlos2019', direction='127.0.0.1', port=27017 ):
        self.user = user
        self.password = password
        self.direction = direction
        self.port = port
        self.client = MongoClient(username=user, password=password, host=direction, port=port)

    def save(self,noticias, palabras):

        # Creamos la conexion a la base de datos y la coleccion que utilizaremos e insertamos
        db = self.client.Noticias
        noticia = db.noticia
        if not noticias:
            print('No hay ninguna noticia a guardar')
        else:
            post_ids = noticia.insert_many([{"url": noticia.url,
                                             "title": noticia.title,
                                             "text": noticia.text,
                                             "date": datetime.datetime.utcnow().replace(second=0,microsecond=0),
                                             "words": ",".join(palabras)} for noticia in noticias]).inserted_ids
            print(f'Insertadas noticias con ids {",".join([str(post_id) for post_id in post_ids])}')

    def save_similarities(self,similaridades, palabras, one_class):

        db = self.client.Noticias
        noticias_procesadas = db.similaridades_noticias
        if similaridades is None:
            print('No hay ninguna similaridad a guardar')
        else:
            post_id = noticias_procesadas.insert_one({"words": ",".join(palabras),
                                                      "similarities": similaridades.tolist(),
                                                      "oneClass": one_class.tolist()}).inserted_id
            print(f'Insertada similaridad con id {post_id}')

    def get_all(self):
        db = self.client.Noticias
        noticia = db.noticia
        all_news = noticia.find()
        return [new for new in all_news]

    def get_similarities(self):
        db = self.client.Noticias
        similarity = db.similaridades_noticias
        all_similarities = similarity.find()
        ret_sim = []
        for doc_similarities in all_similarities:
            for one_sim in doc_similarities['similarities']:
                ret_sim.append(one_sim)
        return ret_sim

    def get_one_class(self):
        db = self.client.Noticias
        similarity = db.similaridades_noticias
        all_similarities = similarity.find()
        return [one_class['oneClass'] for one_class in all_similarities]

