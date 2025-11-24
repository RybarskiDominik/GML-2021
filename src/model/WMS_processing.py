import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pyproj import Transformer

from owslib.wms import WebMapService
from bs4 import BeautifulSoup
import pandas as pd
import requests
import logging
import re


logger = logging.getLogger(__name__)


@dataclass
class Point:
    x: float 
    y: float
    epsg: str  # EPSG:2176 EPSG:2177 #EPSG:2178 #EPSG:2179

    def clean_epsg(self):
        """Zamienia '::' na ':' w kodzie EPSG."""
        self.epsg = self.epsg.replace("::", ":")

    def to_epsg_2180(self):
        transformer = Transformer.from_crs(self.epsg, "EPSG:2180", always_xy=True)
        new_x, new_y = transformer.transform(self.x, self.y)
        return Point(new_x, new_y, "EPSG:2180")
    
    def to_epsg_2000(self):
        transformer = Transformer.from_crs("EPSG:2180", self.epsg, always_xy=True)
        new_x, new_y = transformer.transform(self.x, self.y)
        return Point(new_x, new_y, self.epsg)


class WMS_processing:
    def __init__(self, scene=None):
        self.scene = scene
        self.url = None

        self.raw_data = []
        self.df = pd.DataFrame()


    def WebMapService_info(self):
        wms = WebMapService('https://mapy.geoportal.gov.pl/wss/service/PZGIK/ORTO/WMS/SkorowidzeWgAktualnosci?', version='1.3.0')
        print(list(wms.contents))

        #print(wms.identification.type)
        #print(wms.getOperationByName('GetMap').formatOptions)
        #print(wms['global_mosaic'].crsOptions)
        #print()

    def create_url(self):
        import urllib.parse

        ORTOFOTOMAPA_WMS_URL = "https://mapy.geoportal.gov.pl/wss/service/PZGIK/ORTO/WMS/SkorowidzeWgAktualnosci?"
        LAYER_NAME = "SkorowidzeOrtofotomapy2023"

        params = {
            "SERVICE": "WMS",
            "VERSION": "1.3.0",
            "REQUEST": "GetFeatureInfo",
            "LAYERS": LAYER_NAME,  # Warstwa do wyświetlenia
            "QUERY_LAYERS": LAYER_NAME,  # Warstwa do zapytania
            "BBOX": "182378.300000,508400.000000,182478.300000,508500.000000",
            "CRS": "EPSG:2180",
            "WIDTH": "100",
            "HEIGHT": "100",
            "I": "50",  # Współrzędna X w pikselach (środek obrazu)
            "J": "50",  # Współrzędna Y w pikselach (środek obrazu)
            "INFO_FORMAT": "text/html" 
        }

        # Tworzenie URL
        query_string = urllib.parse.urlencode(params)
        full_url = ORTOFOTOMAPA_WMS_URL + query_string

        print(full_url)

    def get_wms_info(self):
        response = requests.get(self.url)
        
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            
            # Extract namespace dynamically
            namespace = {'wms': root.tag.split('}')[0].strip('{')}
            namespaces = {'wms': 'http://www.opengis.net/wms'}
            
            layers = root.findall(".//wms:Layer", namespace)
            
            print("Dostępne warstwy:")
            for layer in layers:
                name = layer.find("wms:Name", namespace)
                title = layer.find("wms:Title", namespace)
                abstract = layer.find("wms:Abstract", namespace)
                Style = layer.find("wms:Style", namespace)
                CRS = layer.find("wms:CRS", namespace)
                BoundingBox = layer.find("wms:BoundingBox", namespace)
                Queryable = layer.find("wms:Queryable", namespace)
                
                print()
                print(f"Name: {name.text if name is not None else 'Brak'}")
                print(f"Title: {title.text if title is not None else 'Brak'}")
                print(f"Abstract: {abstract.text if abstract is not None else 'Brak'}")
                print(f"Style: {Style.text if Style is not None else 'Brak'}")
                print(f"CRS: {CRS.text if CRS is not None else 'Brak'}")
                print(f"BoundingBox: {BoundingBox.text if BoundingBox is not None else 'Brak'}")
                print(f"Queryable: {Queryable.text if Queryable is not None else 'Brak'}")
                print()
        
        else:
            print("Błąd pobierania GetCapabilities:", response.status_code)


    def repair_data(self, data):
        result = []
        for i in data:
            items = i.strip('{}').split(',')
            data_dict = {}
            for item in items:
                key, value = item.split(":", 1)
                data_dict[key.strip()] = value.strip().strip('"')

            result.append(data_dict)
        self.raw_data = result

    def get_all_wms_layers(self, url):
        wms = WebMapService(url, version='1.3.0')
        return list(wms.contents)

    def get_raster_from_wms(self, url, x, y, epsg):
        point_2000 = Point(x, y, epsg)
        point_2000.clean_epsg()
        point_2180 = point_2000.to_epsg_2180()

        x = point_2180.x
        y = point_2180.y
        
        #print(epsg, url, x, y)
        """
        data = []
        params = {
            "SERVICE": "WMS",
            "VERSION": "1.3.0",
            "REQUEST": "GetFeatureInfo",
            "LAYERS": LAYER_NAME,  # Warstwa do wyświetlenia
            "QUERY_LAYERS": LAYER_NAME,  # Warstwa do zapytania
            'bbox': '%f,%f,%f,%f' % (y-50, x-50, y+50, x+50),
            "CRS": "EPSG:2180",
            "WIDTH": "100",
            "HEIGHT": "100",
            "I": "50",  # Współrzędna X w pikselach (środek obrazu)
            "J": "50",  # Współrzędna Y w pikselach (środek obrazu)
            "INFO_FORMAT": "text/html" 
        }
        """

        data = []
        wms_layers = self.get_all_wms_layers(url)
        
        for LAYER_NAME in wms_layers:
            params = {
                "SERVICE": "WMS",
                "VERSION": "1.3.0",
                "REQUEST": "GetFeatureInfo",
                "LAYERS": LAYER_NAME,  # Warstwa do wyświetlenia
                "QUERY_LAYERS": LAYER_NAME,  # Warstwa do zapytania
                'bbox': '%f,%f,%f,%f' % (y-50, x-50, y+50, x+50),
                "CRS": "EPSG:2180",
                "WIDTH": "100",
                "HEIGHT": "100",
                "I": "50",  # Współrzędna X w pikselach (środek obrazu)
                "J": "50",  # Współrzędna Y w pikselach (środek obrazu)
                "INFO_FORMAT": "text/html" 
            }

            try:
                response = requests.get(url, params=params)
                response.raise_for_status()

                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, "html.parser")

                    script_tags = soup.find_all("script")

                    for script in script_tags:

                        matches = re.findall(r"skorDo5cm.push\((\{.*?\})\);", script.string, re.DOTALL)
                        for match in matches:
                            data.append(match)

            except requests.RequestException as e:
                print(f"Błąd dla warstwy {LAYER_NAME}: {e}")

        return data
    
    def create_and_sort_df(self):
        df_raw = pd.DataFrame(self.raw_data)
        columns = ["url", "ukladWspolrzednych", "aktualnoscRok", "kolor", "wielkoscPiksela", "modulArchiwizacji", "godlo"]
        df_raw = df_raw[columns].copy()
        df_raw = df_raw.sort_values(["aktualnoscRok", "ukladWspolrzednych"], ascending=[False, False], ignore_index=True)
        column_dictionary = {
        #"url": "url",
        "ukladWspolrzednych": "Układ",
        "aktualnoscRok": "Rok",
        "kolor": 'Kolor',
        "wielkoscPiksela" : "Piksel",
        "modulArchiwizacji": "Skala",
        "godlo": "Godło"
        }

        self.df = df_raw.rename(columns=column_dictionary)
        #print(self.df)


if __name__ == '__main__':

    
    # ['SkorowidzeOrtofotomapy2024', 'SkorowidzeOrtofotomapy2023', 'SkorowidzeOrtofotomapy2022', 'SkorowidzeOrtofotomapyStarsze', 'SkorowidzeOrtofotomapyZasiegi2024', 'SkorowidzeOrtofotomapyZasiegi2023', 'SkorowidzeOrtofotomapyZasiegi2022', 'SkorowidzeOrtofotomapyZasiegiStarsze']

    ORTOFOTOMAPA_WMS_URL = "https://mapy.geoportal.gov.pl/wss/service/PZGIK/ORTO/WMS/SkorowidzeWgAktualnosci?"
    LAYER_NAME = "SkorowidzeOrtofotomapy2022"
    LAYER_NAME = "SkorowidzeOrtofotomapyStarsze"

    url = "https://mapy.geoportal.gov.pl/wss/service/PZGIK/ORTO/WMS/SkorowidzeWgAktualnosci?SERVICE=WMS&REQUEST=GetCapabilities"

    #x = 6580874.94
    #y = 5486367.14
    x=6581132.0
    y=5486631.0

    x=6581600.636633089
    y=5487000.438177792

    epsg = "EPSG::2177"
    
    gml = WMS_processing()
    data = gml.get_raster_from_wms(ORTOFOTOMAPA_WMS_URL, x, y, epsg)
    gml.repair_data(data)
    gml.create_and_sort_df()






















