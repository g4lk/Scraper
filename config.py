class Periodicos():
    def __init__(self):
        self.periodicos = {}
        with open('periodicos.txt','r') as f:
            urls = f.read().split()
            for url in urls:
                self.periodicos[url] = False

class Config():
    def __init__(self, user='URJCReadWrite',password='UniversidadReyJuanCarlos2019', direction='127.0.0.1', port=27017 ):
        self.user = user
        self.password = password
        self.direction = direction
        self.port = port


