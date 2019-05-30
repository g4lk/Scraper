from periodicos import Periodicos
from config import DB
from pymongo import MongoClient
import argparse, datetime,sys
import numpy as np
import matplotlib.pyplot as plt

conf = DB()
p = Periodicos()

def analizar_textos(args,auto):
    '''
    Si es una lista de palabras, buscamos pòr palabras, si no por urls y guardamos en bbdd
    :param args: Lista de palabras, o una url (String)
    '''

    global conf
    global p

    if type(args) == list:
        noticias = p.search_news_by_words(args,auto)
        conf.save(noticias, args)
        similarity,one_class = p.process_results()
        conf.save_similarities(similarity,args,one_class)
    else:
        noticias,palabras = p.search_news_by_url(url,auto)
        conf.save(noticias, palabras)
        similary,one_class = p.process_results()
        conf.save_similarities(similarity, palabras,one_class)

def crear_array(one_class_results,number):
    '''
    Creamos el array resultado que se mostrará en la gráfica
    :param one_class_results: Resultados de aplicar one class a las noticias
    :param number: posicion de los arrays que se escogerá (resultados de qué periódico)
    :return: Array que indica la línea a mostrar de noticias anómalas del periodico (siempre creciente)
    '''

    numero = 0
    array_final = []
    similaridades_periodico = [sim[number] for sim in one_class_results]
    for anomalo in similaridades_periodico:
        if anomalo == -1:
            numero += 1
            array_final.append(numero)
        else:
            array_final.append(numero)

    return array_final

def line_chart(fig_number, range_min, range_max, labels, one_class_results):
    '''
    Creamos las ventanas con 5 periodicos por cada una y mostramos los resultados del análisis de las noticias.
    :param fig_number: Número de ventana
    :param range_min: Número del periodico en la lista a mostrar mínimo
    :param range_max: Número del periodico en la lista a mostrar máximo
    :param labels: Nombre de cada periodico
    :param one_class_results: Resultados de aplicar oneClassSVM a las noticias.
    '''

    plt.figure(fig_number)
    plt.xlabel('Noticias ordenadas cronológicamente por número ')
    plt.ylabel('Numero de noticias anómalas en cada periódico')

    array_result = []
    for i in range(range_min, range_max):
        array_result.append(crear_array(one_class_results, i))

    numero = 0
    for result in array_result:
        plt.plot([i for i in range(1, len(result) + 1)], result, label=f'{labels[numero]} {result[-1]}')
        plt.annotate(result[-1], (len(result), result[-1]))
        numero += 1

    plt.yticks([y for y in range(0, len(result), 2)])
    plt.xticks([z for z in range(1, len(one_class_results)+1)])
    plt.legend(loc='upper left')
    fig = plt.gcf()
    fig.canvas.set_window_title('Estadisticas de periodicos')
    if 'linux' in sys.platform:
        mng = plt.get_current_fig_manager()
        mng.resize(*mng.window.maxsize())

def bar_chart(fig_number, mas_anomalos, menos_anomalos):
    plt.figure(fig_number)

    plt.subplot(2, 1, 1)
    plt.bar([i for i in range(0, len(mas_anomalos) )], [elem[0] for elem in mas_anomalos], align='center', alpha=0.5)
    plt.xticks([i for i in range(0, len(mas_anomalos) )], [elem[1] for elem in mas_anomalos])
    plt.title('Periódicos con número de noticias anómalas más alta')
    plt.ylabel('Numero de noticias anómalas en el periódico')

    plt.subplot(2, 1, 2)
    plt.bar([i for i in range(0, len(menos_anomalos))], [elem[0] for elem in menos_anomalos], align='center', alpha=0.5)
    plt.xticks([i for i in range(0, len(menos_anomalos))], [elem[1] for elem in menos_anomalos])
    plt.title('Periódicos con número de noticias anómalas más baja')
    plt.ylabel('Numero de noticias anómalas en el periódico')

    fig = plt.gcf()
    fig.canvas.set_window_title('Grafico de barras resumen')
    if 'linux' in sys.platform:
        mng = plt.get_current_fig_manager()
        mng.resize(*mng.window.maxsize())

def show():
    '''
    Cargamos los nombres de los periodicos, cogemos los resultados de aplicar oneClassSVM a las noticias, creamos las ventanas y mostramos
    '''

    global conf
    global p
    periodicos = p.load_newspapers()
    one_class = conf.get_one_class()

    line_chart(1,  0,   5, periodicos[:5]   , one_class)
    line_chart(2,  5,  10, periodicos[5:10] , one_class)
    line_chart(3, 10,  15, periodicos[10:15], one_class)
    line_chart(4, 15,  20, periodicos[15:20], one_class)
    line_chart(5, 20,  26, periodicos[20:]  , one_class)

    # Cogemos los 5 periodicos con valores más altos/bajos de anomalia para crear el chart
    mas_anomalos = sorted([(crear_array(one_class,i)[-1],periodicos[i]) for i in range(0,len(periodicos)-1)], reverse=True)[:5]
    menos_anomalos = sorted([(crear_array(one_class,i)[-1],periodicos[i]) for i in range(0,len(periodicos)-1)])[:5]

    bar_chart(6,mas_anomalos, menos_anomalos)

    plt.show()


def main():
    '''
    Dos modos para recoger argumentos:
    - Recogemos palabras a buscar
    - Recogemos url de la que extraeremos la info para buscar las demas

    Por ultimo indicaremos si queremos mostrar los resultados.
    '''

    parser = argparse.ArgumentParser()
    parser.add_argument('-w', '--words', help='Palabras a buscar')
    parser.add_argument('-u', '--url', help='URL a buscar')
    parser.add_argument('-s', '--show', help='Mostrar gráficas de lo obtenido hasta el momento',action='store_true')
    parser.add_argument('-a', '--auto', help='Recogida automática (beta)',action='store_true')
    args = parser.parse_args()
    if args.words:
        if args.auto:
            analizar_textos(args.words.lower().split(","),True)
        else:
            analizar_textos(args.words.lower().split(","),False)
    elif args.url:
        if args.auto:
            analizar_textos(args.url, True)
        else:
            analizar_textos(args.url, False)
    else:
        parser.print_help()
        sys.exit(-1)

    if args.show:
        show()

if __name__ == '__main__':
    main()

'''

Ahora mismo debido al visor de matplotlib solo funciona en linux: sudo apt-get install tcl-dev tk-dev python-tk python3-tk
https://matplotlib.org/users/pyplot_tutorial.html
https://stackoverflow.com/questions/6319155/show-the-final-y-axis-value-of-each-line-with-matplotlib
https://stackoverflow.com/questions/5812960/change-figure-window-title-in-pylab
https://stackoverflow.com/questions/12439588/how-to-maximize-a-plt-show-window-using-python
https://matplotlib.org/api/_as_gen/matplotlib.pyplot.annotate.html
https://matplotlib.org/gallery/subplots_axes_and_figures/multiple_figs_demo.html
https://stackoverflow.com/questions/19125722/adding-a-legend-to-pyplot-in-matplotlib-in-the-most-simple-manner-possible
https://matplotlib.org/api/_as_gen/matplotlib.pyplot.yticks.html
https://matplotlib.org/api/_as_gen/matplotlib.pyplot.xticks.html
https://matplotlib.org/api/_as_gen/matplotlib.pyplot.plot.html#matplotlib.pyplot.plot
https://stackoverflow.com/questions/36184953/specifying-values-for-my-x-axis-using-the-matplotlib-pyplot
'''