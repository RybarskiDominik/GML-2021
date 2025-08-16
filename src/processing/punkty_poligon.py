import xml.dom.minidom
import pandas as pd
import logging

def punkty_w_dzialkach(Path):
    TEXT_DZialki = []
    
    def get_element_value(element, tag_name):
        elements = element.getElementsByTagName(tag_name)
        if elements and elements[0].childNodes:
            return elements[0].childNodes[0].nodeValue
        return ''
    
    try:
        domtree = xml.dom.minidom.parse(str(Path))
        gmlfeatureMember = domtree.documentElement

        for egbEGB_DzialkaEwidencyjna in gmlfeatureMember.getElementsByTagName('egb:EGB_DzialkaEwidencyjna'):
            egbJRG = egbEGB_DzialkaEwidencyjna.getElementsByTagName("egb:punktGranicyDzialki")
            idDzialki = get_element_value(egbEGB_DzialkaEwidencyjna, 'egb:idDzialki') or "Brak"

            TEXT_DZialki.extend([(idDzialki, egbJRG2.getAttribute('xlink:href')) for egbJRG2 in egbJRG])


    except Exception as e:
        logging.exception(e)
        print(f"Wystąpił błąd podczas przetwarzania danych: {str(e)}")
        
    df_działki = pd.DataFrame(TEXT_DZialki, columns=['Działka', 'ID'])
    return df_działki

if __name__ == '__main__':
    pass