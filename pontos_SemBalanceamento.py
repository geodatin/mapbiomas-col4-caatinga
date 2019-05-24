#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Produzido por Geodatin - Dados e Geoinformacao
DISTRIBUIDO COM GPLv2
@author: geodatin
"""
import ee

ee.Initialize()

limite_bioma = ee.Geometry.Polygon(
        [[[-42.73681640625, -3.35988909487339],
          [-43.6376953125, -5.943899579425586],
          [-44.12109375, -8.68963906812765],
          [-44.49462890625, -9.947208977327021],
          [-43.57177734375, -10.379765224421455],
          [-43.57177734375, -13.111580118251648],
          [-43.48388671875, -14.477234210156505],
          [-44.14306640625, -14.200488387358332],
          [-44.3408203125, -14.477234210156505],
          [-44.560546875, -15.771109173575281],
          [-43.83544921875, -16.214674588248542],
          [-42.73681640625, -15.982453522973495],
          [-42.64892578125, -15.24178985596171],
          [-41.85791015625, -15.326571801420831],
          [-40.869140625, -15.135764354595798],
          [-40.078125, -14.455958231194025],
          [-39.8583984375, -13.517837674890671],
          [-40.166015625, -13.49647276575895],
          [-39.287109375, -12.768946439455942],
          [-38.16650390625, -12.27559889056172],
          [-37.68310546875, -11.845847044118482],
          [-37.0458984375, -10.35815140094367],
          [-36.474609375, -10.228437266155943],
          [-36.36474609375, -9.70905706861821],
          [-36.4306640625, -9.188870084473393],
          [-35.44189453125, -8.58102121564184],
          [-35.04638671875, -7.514980942395871],
          [-35.04638671875, -5.922044619883305],
          [-35.33203125, -5.025282908609298],
          [-36.36474609375, -4.93772427430248],
          [-37.50732421875, -4.54357027937176],
          [-38.82568359375, -3.3160183381615123],
          [-40.10009765625, -2.657737790139788],
          [-41.484375, -2.6357885741666065],
          [-42.47314453125, -3.3160183381615123]]])


bioma = "CAATINGA" #nome do bioma setado nos metadados
asset_bacias = 'users/diegocosta/baciasRecticadaCaatinga'

biomas = ee.FeatureCollection('users/SEEGMapBiomas/bioma_1milhao_uf2015_250mil_IBGE_geo_v4_revisao_pampa_lagoas')
biomapol = biomas.filterMetadata('CD_LEGENDA', "equals", bioma)


# ftcol poligonos com as bacias da caatinga
ftcol_bacias = ee.FeatureCollection(asset_bacias)


#diretorio de saida para as bacias que serao 
dirout = 'projects/mapbiomas-workspace/AMOSTRAS/'


anos =['1985','1986','1987','1988','1989','1990','1991','1992','1993','1994','1995','1996',
  '1997','1998','1999','2000','2001','2002','2003','2004','2005','2006','2007','2008','2009','2010',
  '2011','2012','2013','2014','2015','2016','2017']

#converte os anos em numeros do gee
anos = map(lambda ano: ee.Number.parse(ano, 10), anos)

#converte a lista de anos numa lista gee
list_anos = ee.List(anos)


#retorna vetor com strings 'classification_$ano', onde $ano eh cada um dos anos recebida como parametro na variavel myList        
def tuplaContinua (myList):
  myAnos = map(lambda item: 'classification_'+str(item), myList)
  return myAnos;

#salva ftcol para um asset
def saveToAsset(collection, name):
    #diretorio do asset
    outAsset = 'projects/mapbiomas-workspace/AMOSTRAS/col4/CAATINGA/BACIA_PEQUENA_SEM_BALANCEAR/'
    optExp = {
            'collection': collection, 
            'description': name, 
            'assetId': outAsset + name           
    }
    task = ee.batch.Export.table.toAsset(**optExp)
    task.start()
    print("exportando carta $s ...!", name)


#retorna uma lista com as strings referentes a janela dada, por exemplo em janela 5, no ano 1999, o metodo retornaria
#['classification_1997', 'classification_1998', 'classification_1999', 'classification_2000', 'classification_2001']
#desse jeito pode-se extrair as bandas referentes as janelas
def mapeiaAnos(ano, janela, anos):
    primeiroAno = anos[0]
    ultimoAno = anos[-1]
    indice = anos.index(ano)
    if ano == primeiroAno:
        return tuplaContinua(anos[0:janela])
    elif ano == anos[1]:
        return tuplaContinua(anos[0:janela])
    elif ano == anos[-2]:
        return tuplaContinua(anos[-janela:])
    elif ano == ultimoAno:
        return tuplaContinua(anos[-janela:])
    else:
        return tuplaContinua(anos[indice-2:indice+3])


terrain = ee.Image("JAXA/ALOS/AW3D30_V1_1").select("AVE")
slope = ee.Terrain.slope(terrain)
square = ee.Kernel.square(**{'radius': 3}) 

#colecao de integracao do mapbiomas
assetMapbiomasP = 'projects/mapbiomas-workspace/public/collection3_1/mapbiomas_collection31_integration_v1'
lista_janela = ee.List([]);

# @collection1: mapas de uso e cobertura Mapbiomas ==> para extrair as areas estaveis
#collection1 = ee.ImageCollection(dirsamples).filterMetadata('biome', 'equals', bioma)
classMapB = [3, 4, 5, 9,12,13,15,18,19,20,21,22,23,24,25,26,29,30,31,32,33]
classNew = [3, 4, 3, 3,12,12,21,21,21,21,21,22,22,22,22,33,29,22,33,12,33] 
collection1 = ee.Image(assetMapbiomasP)

# @mosaicos: ImageCollection com os mosaicos de Mapbiomas 
mosaicos = ee.ImageCollection('projects/mapbiomas-workspace/MOSAICOS/workspace-c3')#.filterMetadata('biome', 'equals', bioma)
#nameBacias = ftcol_bacias.reduceColumns(ee.Reducer.toList(), ['ID_NIVEL2']).get('list').getInfo()
list_anos = list_anos.getInfo()
#tamanho da janela de estabilidade
janela = 5
k = 0

#variavel que define o metodo de amostragem. o metodo 2 balanceia por area e por representatividade estatistica
# baciasFeitas = [] 

def iterate_bacias(bacia):
    #colecao responsavel por executar o controle de execucao, caso optem por executar o codigo em terminais paralelos,
    #ou seja, em mais de um terminal simultaneamente..
    #caso deseje executar num unico terminal, deixar colecao vazia. 
    baciasFeitas = [] #'759', '7611','766','767','771',7612','7613','7614','7615','772', '773', '774', '775', '777','776', '763','7618'
                     #,'765',  '762', '746', '7619', '7616', '7617', '744', '745', '747', '732', '743', '742', '741','752','753', '751'
                     #, '754', '756', '755','758' , '757'
    nomeBacia = bacia.get('nunivotto3').getInfo()
    print("bacia ", nomeBacia)
    if nomeBacia not in baciasFeitas:
        #print("comezo bacia :", nomeBacia)        
        BuffBacia = bacia.geometry()
        colecaoPontos = ee.FeatureCollection([])
        imgBacia = collection1.clip(BuffBacia)
        mosaicosBacia = mosaicos.filterBounds(BuffBacia)       
        colAnos = map(lambda ano: mapeiaAnos(ano, janela, list_anos), list_anos)
        anoCount = 1985
                
        for intervalo in colAnos:
            print (anoCount)
            imgTemp = imgBacia.select(intervalo)
            
            #@reducida: cria uma imagem que cada pixel diz quanto variou entre todas as bandas
            reducida =  imgTemp.reduce(ee.Reducer.countDistinct())
            
            #@imgTemp: sera o mapa de uso e cobertura Mapbiomas ao que sera masked com as classes 
            #estaveis na janela de 5 anos       
            imgTemp = imgBacia.select('classification_'+str(anoCount)).remap(classMapB, classNew)
            imgTemp = imgTemp.rename(['class'])
             
            reducida = reducida.eq(1)
            reducida = reducida.set('anos', anoCount)
           
            # processo de masked da imagem mapa mapbiomas com 2 bandas adicionais Longitude Latitude
            imgTemp = imgTemp.mask(reducida)
            #print(imgTemp.bandNames().getInfo()) 
            lsClasse = [3,4,12,21,22,33,29]
            lsPtos = [1500,1500,1500,1500,1500,1500,1500]
            
           
            imgTemp.set('anos', anoCount)
            imgTemp = imgTemp.addBands(ee.Image.pixelLonLat())            
            mosaicosBaciaAno = ee.Image(mosaicosBacia.filterMetadata('year', 'equals', anoCount).mosaic())
            
            #passando a geometria da bacia de novo para o mosaico 
            mosaicosBaciaAno = mosaicosBaciaAno.set("system:footprint", BuffBacia)
            mosaicosBaciaAno = mosaicosBaciaAno.addBands(imgTemp)
            mosaicosBaciaAno = mosaicosBaciaAno.mask(reducida)
           
            mosaicosBaciaAno = mosaicosBaciaAno.clip(BuffBacia)
            #print(mosaicosBaciaAno.bandNames().getInfo())
            #opcoes para o sorteio estratificadoBuffBacia
            optionPtos = {
                    'numPoints': 0,
                    'classBand': 'class', 
                    'region': BuffBacia, 
                    'scale': 30,
                    'classValues': lsClasse,
                    'classPoints': lsPtos
                    }
            ptosTemp = mosaicosBaciaAno.stratifiedSample(numPoints= 0,classBand= 'class',region= BuffBacia,
            scale= 30,classValues= lsClasse,classPoints= lsPtos)
            #print(ptosTemp.limit(20).size().getInfo())
            #insere informacoes em cada ft
            ptosTemp = ptosTemp.map(lambda ponto: ponto.set({'year': anoCount}))
            ptosTemp = ptosTemp.map(lambda ponto: ponto.set({'bacia': nomeBacia}))
            ptosTemp = ptosTemp.map(lambda ponto: ponto.setGeometry(ee.Geometry.Point(ee.List([ponto.get('longitude'), ponto.get('latitude')]))))

            #merge com colecoes anteriores 
            colecaoPontos = colecaoPontos.merge(ptosTemp)
            anoCount+=1
        #print(colecaoPontos.propertyNames().getInfo())
        saveToAsset(colecaoPontos, str(nomeBacia))
    
tamanho = ftcol_bacias.size().getInfo()
#trasforma a ftcol em lista para poder iterar nela com um loop nativo
ft_bacias = ftcol_bacias.toList(ftcol_bacias.size())

print ftcol_bacias.size().getInfo()

#faz a extracao das amostras para cada bacia
for i in range(tamanho):
    iterate_bacias(ee.Feature(ft_bacias.get(i)))
