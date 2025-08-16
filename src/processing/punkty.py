import xml.dom.minidom
import pandas as pd
import numpy as np
import logging
import time
import sys

def punkt_graniczny(Path):
    punkty = []

    def get_element_value(element, tag_name):
        elements = element.getElementsByTagName(tag_name)
        if elements and elements[0].childNodes:
            return elements[0].childNodes[0].nodeValue
        return '-'

    try:
        domtree = xml.dom.minidom.parse(str(Path))
        gmlfeatureMember = domtree.documentElement
    
        for egbEGB_PunktGraniczny in gmlfeatureMember.getElementsByTagName('egb:EGB_PunktGraniczny'):
            gmlid = egbEGB_PunktGraniczny.getAttribute('gml:id')
            idPunktu = get_element_value(egbEGB_PunktGraniczny, 'egb:idPunktu')
            rodzajStabilizacji = get_element_value(egbEGB_PunktGraniczny, 'egb:rodzajStabilizacji')
            spelnienieWarunkowDokl = get_element_value(egbEGB_PunktGraniczny, 'egb:spelnienieWarunkowDokl')
            sposobPozyskania = get_element_value(egbEGB_PunktGraniczny, 'egb:sposobPozyskania')
            pos = get_element_value(egbEGB_PunktGraniczny, 'gml:pos')
            x, y = pos.split(' ')

            combination_PG = [gmlid, idPunktu, x, y, sposobPozyskania, spelnienieWarunkowDokl, rodzajStabilizacji]
            punkty.append(combination_PG)

    except Exception as e:
        print(f"Wystąpił błąd podczas przetwarzania danych: {str(e)}")
    
    df = pd.DataFrame(punkty, columns=['ID', 'NR', 'X', 'Y', 'SPD', 'ISD','STB'])
    df = df.sort_values(['NR'])
    return df


if __name__ == '__main__':
    pass