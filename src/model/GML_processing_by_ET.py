import xml.etree.ElementTree as ET
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class GMLParser:
    def __init__(self, path):
        self.path = path
        self.namespaces = {
            'gml': 'http://www.opengis.net/gml/3.2',
            'egb': 'ewidencjaGruntowIBudynkow:1.0',
            'xlink': 'http://www.w3.org/1999/xlink',
            'ges2021': 'geodezyjnaEwidencjaSieciUzbrojeniaTerenu:1.0',
            'ot2021': 'bazaDanychObiektowTopograficznych500:1.0',
        }

        self.df_PrezentacjaGraficzna = pd.DataFrame()
        self.df_OT_Ogrodzenia = pd.DataFrame()
        self.df_OT_Budowle = pd.DataFrame()
        self.df_OT_Skarpa = pd.DataFrame()
        self.df_EGB_KonturUzytkuGruntowego = pd.DataFrame()
        self.df_EGB_KonturKlasyfikacyjny = pd.DataFrame()
        self.df_EGB_PunktGraniczny = pd.DataFrame()
        self.df_EGB_DzialkaEwidencyjna = pd.DataFrame()
        self.df_EGB_Budynek = pd.DataFrame()
        self.df_EGB_AdresNieruchomosci = pd.DataFrame()

        #self.merged_dfs = pd.DataFrame()

        self.epsg = None
        self.root = []
        self.get_root()

    def get_root(self):
        tree = ET.parse(self.path)
        self.root = tree.getroot()

    def initialize_gml(self):
        self._PrezentacjaGraficzna()
        self._OT_Ogrodzenia()
        self._OT_Budowle()
        self._OT_Skarpa()
        self._EGB_KonturUzytkuGruntowego()
        self._EGB_KonturKlasyfikacyjny()
        self._EGB_PunktGraniczny()
        self._EGB_DzialkaEwidencyjna()
        self._EGB_Budynek()
        self._EGB_AdresNieruchomosci()

        logging.debug("END Initialize.")

        self.merge_all_dataframes()

        logging.debug("END merge dataframe.")

        return self.merged_dfs

    def merge_df_by_PrezentacjaGraficzna(self, df_join):
        df_id = pd.merge(self.df_PrezentacjaGraficzna, df_join, how = "right", left_on = "obiektPrzedstawiany", right_on = "id", )
        return df_id

    def merge_all_dataframes(self):
        # Create a list of all the dataframes with their names
        dataframes_to_merge = [
            ("df_OT_Ogrodzenia", self.df_OT_Ogrodzenia),
            ("df_OT_Budowle", self.df_OT_Budowle),
            ("df_OT_Skarpa", self.df_OT_Skarpa),
            ("df_EGB_KonturUzytkuGruntowego", self.df_EGB_KonturUzytkuGruntowego),
            ("df_EGB_KonturKlasyfikacyjny", self.df_EGB_KonturKlasyfikacyjny),
            ("df_EGB_PunktGraniczny", self.df_EGB_PunktGraniczny),
            ("df_EGB_DzialkaEwidencyjna", self.df_EGB_DzialkaEwidencyjna),
            ("df_EGB_Budynek", self.df_EGB_Budynek),
            ("df_EGB_AdresNieruchomosci", self.df_EGB_AdresNieruchomosci),
        ]

        self.merged_dfs = {}
        for name, df in dataframes_to_merge:
            self.merged_dfs[name] = self.merge_df_by_PrezentacjaGraficzna(df)
        return self.merged_dfs

    def _OT_Ogrodzenia(self):
        data_OT_Ogrodzenia = []
        
        def get_element_value(element_path, is_coordinates=False, is_pos=False):
            element = ogrodzenie.find(element_path, self.namespaces)
            try:
                if element is not None and element.text is not None:
                    if is_pos:
                        coordinates = []
                        for element in ogrodzenie.findall(element_path, self.namespaces):
                            coords = [float(coord) for coord in element.text.strip().split()]
                            coordinates.extend((coords[i], coords[i + 1]) for i in range(0, len(coords), 2))
                        return coordinates
                    if is_coordinates:
                        return [(float(x), float(y)) for x, y in zip(*[iter(element.text.strip().split())]*2)]  # tuples
                        
                        #return [[float(x), float(y)] for x, y in zip(*[iter(element.text.strip().split())]*2)]  # list
                        #coordinates = element.text.strip().split()
                        #return [(float(coordinates[i]), float(coordinates[i + 1])) for i in range(0, len(coordinates), 2)]
                        #return [float(coord) for coord in element.text.strip().split()]
                    return element.text.strip()
            except Exception as e:
                logging.exception(e)
                print(e)
            return None

        for feature_member in self.root.findall('gml:featureMember', self.namespaces):
            for ogrodzenie in feature_member.findall('ot2021:OT_Ogrodzenia', self.namespaces):
                gml_id = ogrodzenie.attrib.get('{http://www.opengis.net/gml/3.2}id')
                
                rodzajOgrodzenia = get_element_value('.//ot2021:rodzajOgrodzenia')
                geometria = get_element_value('.//gml:posList', is_coordinates=True)
                if not geometria:
                    try:
                        geometria = get_element_value('.//gml:pos', is_pos=True)
                    except Exception as e:
                        logging.exception(e)
                        print(e)
                        geometria = []
                
                data_OT_Ogrodzenia.append([gml_id, rodzajOgrodzenia, geometria])
        
        self.df_OT_Ogrodzenia = pd.DataFrame(data_OT_Ogrodzenia, columns=['id', 'rodzajOgrodzenia', 'geometria'])
        return self.df_OT_Ogrodzenia

    def _OT_Budowle(self):
        
        def get_element_value(element_path, is_coordinates=False, is_pos=False):
            element = budowla.find(element_path, self.namespaces)
            try:
                if element is not None and element.text is not None:
                    if is_pos:
                        coordinates = []
                        for element in budowla.findall(element_path, self.namespaces):
                            coords = [float(coord) for coord in element.text.strip().split()]
                            coordinates.extend((coords[i], coords[i + 1]) for i in range(0, len(coords), 2))
                        return coordinates
                    if is_coordinates:
                        return [(float(x), float(y)) for x, y in zip(*[iter(element.text.strip().split())]*2)]
                    return element.text.strip()
            except Exception as e:
                logging.exception(e)
                print(e)
            return None

        data_OT_Budowle = []
        for feature_member in self.root.findall('gml:featureMember', self.namespaces):
            for budowla in feature_member.findall('ot2021:OT_Budowle', self.namespaces):
                gml_id = budowla.attrib.get('{http://www.opengis.net/gml/3.2}id')

                rodzajBudowli = get_element_value('.//ot2021:rodzajBudowli')
                geometria = get_element_value('.//gml:posList', is_coordinates=True)
                if not geometria:
                    try:
                        geometria = get_element_value('.//gml:pos', is_pos=True)
                    except Exception as e:
                        logging.exception(e)
                        print(e)
                        geometria = []

                data_OT_Budowle.append([gml_id, rodzajBudowli, geometria])
        
        self.df_OT_Budowle = pd.DataFrame(data_OT_Budowle, columns = ['id', 'rodzajBudowli', 'geometria'])
        return self.df_OT_Budowle

    def _OT_Skarpa(self):
        data_OT_Skarpa = []

        def get_element_value(element_path, is_coordinates=False, is_pos=False):
            element = skarpa.find(element_path, self.namespaces)
            try:
                if element is not None and element.text is not None:
                    if is_pos:
                        x, y = element.text.split(' ')
                        return round(float(x), 2), round(float(y), 2)
                    if is_coordinates: 
                        return [float(coord) for coord in element.text.strip().split()]
                    return element.text.strip()
            except Exception as e:
                logging.exception(e)
                print(e)
            return None

        for feature_member in self.root.findall('gml:featureMember', self.namespaces):
            for skarpa in feature_member.findall('ot2021:OT_Skarpa', self.namespaces):
                gml_id = skarpa.attrib.get('{http://www.opengis.net/gml/3.2}id')

                rodzajSkarpy = get_element_value('.//ot2021:rodzajSkarpy')

                poczatekGorySkarpy = []
                poczatekGorySkarpy_element = skarpa.find('.//ot2021:poczatekGorySkarpy', self.namespaces)
                if poczatekGorySkarpy_element is not None:
                    pos = poczatekGorySkarpy_element.find('.//gml:pos', self.namespaces)
                    if pos is not None and pos.text:
                        poczatekGorySkarpy = pos.text.strip().split()

                koniecGorySkarpy = []
                koniecGorySkarpy_element = skarpa.find('.//ot2021:koniecGorySkarpy', self.namespaces)
                if koniecGorySkarpy_element is not None:
                    pos = koniecGorySkarpy_element.find('.//gml:pos', self.namespaces)
                    if pos is not None and pos.text:
                        koniecGorySkarpy = pos.text.strip().split()

                geometria_element = skarpa.find('.//ot2021:geometria', self.namespaces)
                if geometria_element is not None:
                    geometria_values = geometria_element.find('.//gml:posList', self.namespaces)
                    coordinates = geometria_values.text.strip().split() if geometria_values is not None else []
                    geometria = [(float(coordinates[i]), float(coordinates[i + 1])) for i in range(0, len(coordinates), 2)]
                else:
                    geometria = []

                data_OT_Skarpa.append([gml_id, rodzajSkarpy, poczatekGorySkarpy, koniecGorySkarpy, geometria])
        self.df_OT_Skarpa = pd.DataFrame(data_OT_Skarpa, columns = ['id', 'rodzajSkarpy', 'poczatekGorySkarpy', 'koniecGorySkarpy', 'geometria'])
        return self.df_OT_Skarpa

    def _EGB_PunktGraniczny(self):
        data_EGB_PunktGraniczny = []

        def get_element_value(element_path, is_coordinates=False, is_pos=False):
            element = punkt.find(element_path, self.namespaces)
            try:        
                if element is not None and element.text is not None:
                    if is_pos:
                        x, y = element.text.split(' ')
                        return round(float(x), 2), round(float(y), 2)
                    if is_coordinates: 
                        return [float(coord) for coord in element.text.strip().split()]
                    return element.text.strip()
            except Exception as e:
                logging.exception(e)
                print(e)
            return None
        
        for feature_member in self.root.findall('gml:featureMember', self.namespaces):
            for punkt in feature_member.findall('egb:EGB_PunktGraniczny', self.namespaces):
                punkt_id = punkt.attrib.get('{http://www.opengis.net/gml/3.2}id')
                
                #geometria = get_element_value('gml:pos', is_pos=True)
                geometria_element = punkt.find('.//egb:geometria/gml:Point/gml:pos', self.namespaces)
                geometria = tuple(map(float, geometria_element.text.strip().split())) if geometria_element is not None else None  # or list

                idPunktu = get_element_value('.//egb:idPunktu')
                sposobPozyskania = get_element_value('.//egb:sposobPozyskania')
                spelnienieWarunkowDokl = get_element_value('.//egb:spelnienieWarunkowDokl')
                rodzajStabilizacji = get_element_value('.//egb:rodzajStabilizacji')
                oznWMaterialeZrodlowym = get_element_value('.//egb:oznWMaterialeZrodlowym')
                numerOperatuTechnicznego = get_element_value('.//egb:numerOperatuTechnicznego')
                dodatkoweInformacje = get_element_value('.//egb:dodatkoweInformacje')

                data_EGB_PunktGraniczny.append([
                    punkt_id, geometria, idPunktu, sposobPozyskania, spelnienieWarunkowDokl,
                    rodzajStabilizacji, oznWMaterialeZrodlowym, numerOperatuTechnicznego, dodatkoweInformacje
                ])

        self.df_EGB_PunktGraniczny = pd.DataFrame(data_EGB_PunktGraniczny, columns=[
            'id', 'geometria', 'idPunktu', 'sposobPozyskania', 'spelnienieWarunkowDokl',
            'rodzajStabilizacji', 'oznWMaterialeZrodlowym', 'numerOperatuTechnicznego', 'dodatkoweInformacje'
        ])
        return self.df_EGB_PunktGraniczny

    def _EGB_Budynek(self):
        data_EGB_Budynek = []

        def get_element_value(element_path, is_coordinates=False, is_pos=False):
            element = budynek.find(element_path, self.namespaces)
            try:
                if element is not None and element.text is not None:
                    if is_pos:
                        coordinates = []
                        for element in budynek.findall(element_path, self.namespaces):
                            coords = [float(coord) for coord in element.text.strip().split()]
                            coordinates.extend((coords[i], coords[i + 1]) for i in range(0, len(coords), 2))
                        return coordinates
                    if is_coordinates:
                        return [(float(x), float(y)) for x, y in zip(*[iter(element.text.strip().split())]*2)]  # tuples
                    return element.text.strip()
            except Exception as e:
                logging.exception(e)
                print(e)
            return None

        for feature_member in self.root.findall('gml:featureMember', self.namespaces):
            for budynek in feature_member.findall('egb:EGB_Budynek', self.namespaces):
                gml_id = budynek.attrib.get('{http://www.opengis.net/gml/3.2}id')

                idBudynku = get_element_value('.//egb:idBudynku')

                geometria = get_element_value('.//gml:posList', is_coordinates=True)
                if not geometria:
                    try:
                        geometria = get_element_value('.//gml:pos', is_pos=True)
                    except Exception as e:
                        logging.exception(e)
                        print(e)
                        geometria = []

                rodzajWgKST = get_element_value('.//egb:rodzajWgKST')

               
                liczbaKondygnacjiNadziemnych = get_element_value('.//egb:liczbaKondygnacjiNadziemnych')
                liczbaKondygnacjiPodziemnych = get_element_value('.//egb:liczbaKondygnacjiPodziemnych')
                powZabudowy = get_element_value('.//egb:powZabudowy')

                data_EGB_Budynek.append([
                    gml_id, idBudynku, rodzajWgKST, liczbaKondygnacjiNadziemnych, 
                    liczbaKondygnacjiPodziemnych, powZabudowy, geometria
                ])

        # Converting the data to a DataFrame
        self.df_EGB_Budynek = pd.DataFrame(data_EGB_Budynek, columns=['id', 'idBudynku', 'rodzajWgKST', 'liczbaKondygnacjiNadziemnych', 'liczbaKondygnacjiPodziemnych', 'powZabudowy', 'geometria'])
        return self.df_EGB_Budynek

    def _EGB_DzialkaEwidencyjna(self):
        def get_element_value(element_path, is_coordinates=False, is_pos=False):
            element = dzialka.find(element_path, self.namespaces)
            try:
                if element is not None and element.text is not None:
                    if is_pos:
                        coordinates = []
                        for element in dzialka.findall(element_path, self.namespaces):
                            coords = [float(coord) for coord in element.text.strip().split()]
                            coordinates.extend((coords[i], coords[i + 1]) for i in range(0, len(coords), 2))
                        return coordinates
                    if is_coordinates:
                        return [(float(x), float(y)) for x, y in zip(*[iter(element.text.strip().split())]*2)]  # tuples
                        
                        #return [[float(x), float(y)] for x, y in zip(*[iter(element.text.strip().split())]*2)]  # list
                        #coordinates = element.text.strip().split()
                        #return [(float(coordinates[i]), float(coordinates[i + 1])) for i in range(0, len(coordinates), 2)]
                        #return [float(coord) for coord in element.text.strip().split()]
                    return element.text.strip()
            except Exception as e:
                logging.exception(e)
                print(e)
            return None
        
        data_EGB_DzialkaEwidencyjna = []
        for feature_member in self.root.findall('gml:featureMember', self.namespaces):
            for dzialka in feature_member.findall('egb:EGB_DzialkaEwidencyjna', self.namespaces):
                gml_id = dzialka.attrib.get('{http://www.opengis.net/gml/3.2}id')

                idDzialki = get_element_value('.//egb:idDzialki')
                numer_kw = get_element_value('.//egb:numerKW')
                geometria = get_element_value('.//gml:posList', is_coordinates=True)
                if not geometria:
                    try:
                        geometria = get_element_value('.//gml:pos', is_pos=True)
                    except Exception as e:
                        logging.exception(e)
                        print(e)
                        geometria = []

                pole_ewidencyjne = get_element_value('.//egb:poleEwidencyjne')

                data_EGB_DzialkaEwidencyjna.append([gml_id, idDzialki, numer_kw, geometria, pole_ewidencyjne])
        self.df_EGB_DzialkaEwidencyjna = pd.DataFrame(data_EGB_DzialkaEwidencyjna, columns=['id', 'idDzialki', "numerKW", "geometria", "poleEwidencyjne"])
        return self.df_EGB_DzialkaEwidencyjna

    def _EGB_KonturUzytkuGruntowego(self):
        def get_element_value(element_path, is_coordinates=False, is_pos=False):
            element = kontur.find(element_path, self.namespaces)
            try:
                if element is not None and element.text is not None:
                    if is_pos:
                        coordinates = []
                        for element in kontur.findall(element_path, self.namespaces):
                            coords = [float(coord) for coord in element.text.strip().split()]
                            coordinates.extend((coords[i], coords[i + 1]) for i in range(0, len(coords), 2))
                        return coordinates
                    if is_coordinates:
                        return [(float(x), float(y)) for x, y in zip(*[iter(element.text.strip().split())]*2)]  # tuples
                        
                        #return [[float(x), float(y)] for x, y in zip(*[iter(element.text.strip().split())]*2)]  # list
                        #coordinates = element.text.strip().split()
                        #return [(float(coordinates[i]), float(coordinates[i + 1])) for i in range(0, len(coordinates), 2)]
                        #return [float(coord) for coord in element.text.strip().split()]
                    return element.text.strip()
            except Exception as e:
                logging.exception(e)
                print(e)
            return None
        
        data_EGB_KonturUzytkuGruntowego = []
        # Przechodzimy przez wszystkie featureMember
        for feature_member in self.root.findall('gml:featureMember', self.namespaces):
            for kontur in feature_member.findall('egb:EGB_KonturUzytkuGruntowego', self.namespaces):
                gml_id = kontur.attrib.get('{http://www.opengis.net/gml/3.2}id')

                # Pobieranie danych z elementów
                idIIP = get_element_value('.//egb:idIIP')
                #startObiekt = get_element_value('.//egb:startObiekt')
                #startWersjaObiekt = get_element_value('.//egb:startWersjaObiekt')
                geometria = get_element_value('.//gml:posList', is_coordinates=True)
                if not geometria:
                    try:
                        geometria = get_element_value('.//gml:pos', is_pos=True)
                    except Exception as e:
                        logging.exception(e)
                        print(e)
                        geometria = []
                idUzytku = get_element_value('.//egb:idUzytku')
                OFU = get_element_value('.//egb:OFU')
                lokalizacjaUzytku = get_element_value('.//egb:lokalizacjaUzytku')

                # Dodajemy dane do listy
                data_EGB_KonturUzytkuGruntowego.append([gml_id, idIIP, geometria, idUzytku, OFU, lokalizacjaUzytku])

        # Zwracamy dane jako DataFrame
        self.df_EGB_KonturUzytkuGruntowego = pd.DataFrame(data_EGB_KonturUzytkuGruntowego,
                                                            columns=['id', 'idIIP', 'geometria', 'idUzytku', 'OFU', 'lokalizacjaUzytku'])
        return self.df_EGB_KonturUzytkuGruntowego

    def _EGB_KonturKlasyfikacyjny(self):
        def get_element_value(element_path, is_coordinates=False, is_pos=False):
            element = kontur.find(element_path, self.namespaces)
            try:
                if element is not None and element.text is not None:
                    if is_pos:
                        coordinates = []
                        for element in kontur.findall(element_path, self.namespaces):
                            coords = [float(coord) for coord in element.text.strip().split()]
                            coordinates.extend((coords[i], coords[i + 1]) for i in range(0, len(coords), 2))
                        return coordinates
                    if is_coordinates:
                        return [(float(x), float(y)) for x, y in zip(*[iter(element.text.strip().split())]*2)]  # tuples
                        
                        #return [[float(x), float(y)] for x, y in zip(*[iter(element.text.strip().split())]*2)]  # list
                        #coordinates = element.text.strip().split()
                        #return [(float(coordinates[i]), float(coordinates[i + 1])) for i in range(0, len(coordinates), 2)]
                        #return [float(coord) for coord in element.text.strip().split()]
                    return element.text.strip()
            except Exception as e:
                logging.exception(e)
                print(e)
            return None
        
        data_EGB_KonturKlasyfikacyjny = []
        # Przechodzimy przez wszystkie featureMember
        for feature_member in self.root.findall('gml:featureMember', self.namespaces):
            for kontur in feature_member.findall('egb:EGB_KonturKlasyfikacyjny', self.namespaces):
                gml_id = kontur.attrib.get('{http://www.opengis.net/gml/3.2}id')

                # Pobieranie danych z elementów
                idIIP = get_element_value('.//egb:idIIP')
                #startObiekt = get_element_value('.//egb:startObiekt')
                #startWersjaObiekt = get_element_value('.//egb:startWersjaObiekt')
                geometria = get_element_value('.//gml:posList', is_coordinates=True)
                if not geometria:
                    try:
                        geometria = get_element_value('.//gml:pos', is_pos=True)
                    except Exception as e:
                        logging.exception(e)
                        print(e)
                        geometria = []
                idKonturu = get_element_value('.//egb:idKonturu')
                OFU = get_element_value('.//egb:OFU')
                OZU = get_element_value('.//egb:OZU')
                OZK = get_element_value('.//egb:OZK')
                lokalizacjaUzytku = get_element_value('.//egb:lokalizacjaUzytku')

                # Dodajemy dane do listy
                data_EGB_KonturKlasyfikacyjny.append([gml_id, idIIP, geometria, idKonturu, OFU, OZU, OZK, lokalizacjaUzytku])

        # Zwracamy dane jako DataFrame
        self.df_EGB_KonturKlasyfikacyjny = pd.DataFrame(data_EGB_KonturKlasyfikacyjny,
                                                            columns=['id', 'idIIP', 'geometria', 'idKonturu', 'OFU', "OZU", "OZK", 'lokalizacjaUzytku'])
        return self.df_EGB_KonturKlasyfikacyjny

    def _EGB_AdresNieruchomosci(self):
        data_EGB_AdresNieruchomosci = []

        def get_element_value(element_path, is_coordinates=False, is_href=False, is_pos=False):
            element = adres.find(element_path, self.namespaces)
            try:
                if is_href and element is not None:
                    return element.attrib.get('{http://www.w3.org/1999/xlink}href') 
                if element is not None and element.text is not None:
                    if is_pos:
                        x, y = element.text.split(' ')
                        return round(float(x), 2), round(float(y), 2)
                    if is_coordinates: 
                        return [float(coord) for coord in element.text.strip().split()]
                    return element.text.strip()
            except Exception as e:
                logging.exception(e)
                print(e)
            return None
        
        for feature_member in self.root.findall('gml:featureMember', self.namespaces):
            for adres in feature_member.findall('egb:EGB_AdresNieruchomosci', self.namespaces):
                adres_id = adres.attrib.get('{http://www.opengis.net/gml/3.2}id')

                geometria = get_element_value('gml:pos', is_pos=True)

                #lokalnyId = get_element_value('.//egb:idIIP/egb:EGB_IdentyfikatorIIP/egb:lokalnyId')
                #przestrzenNazw = get_element_value('.//egb:idIIP/egb:EGB_IdentyfikatorIIP/egb:przestrzenNazw')
                #wersjaId = get_element_value('.//egb:idIIP/egb:EGB_IdentyfikatorIIP/egb:wersjaId')
                #startObiekt = get_element_value('.//egb:startObiekt')
                #startWersjaObiekt = get_element_value('.//egb:startWersjaObiekt')
                operatTechniczny2 = get_element_value('.//egb:operatTechniczny2', is_href = True)
                nazwaMiejscowosci = get_element_value('.//egb:nazwaMiejscowosci')
                idMiejscowosci = get_element_value('.//egb:idMiejscowosci')
                nazwaUlicy = get_element_value('.//egb:nazwaUlicy')
                numerPorzadkowy = get_element_value('.//egb:numerPorzadkowy')

                data_EGB_AdresNieruchomosci.append([
                    adres_id, geometria, operatTechniczny2, nazwaMiejscowosci, idMiejscowosci, 
                    nazwaUlicy, numerPorzadkowy
                ])

        self.df_EGB_AdresNieruchomosci = pd.DataFrame(data_EGB_AdresNieruchomosci, columns=[
            'id', 'geometria', 'operatTechniczny2', 'nazwaMiejscowosci', 'idMiejscowosci', 
            'nazwaUlicy', 'numerPorzadkowy'
        ])
        return self.df_EGB_AdresNieruchomosci

    def _PrezentacjaGraficzna(self):
        data_PrezentacjaGraficzna = []

        def get_element_value(element_path, is_coordinates=False, is_href=False, is_pos=False):
            element = prezentacja.find(element_path, self.namespaces)
            try:
                if is_href and element is not None:
                    return element.attrib.get('{http://www.w3.org/1999/xlink}href')            
                if element is not None and element.text is not None:
                    if is_pos:
                        x, y = element.text.split(' ')
                        return (round(float(x), 2), round(float(y), 2))
                    if is_coordinates: 
                        return [float(coord) for coord in element.text.strip().split()]
                    return element.text.strip()
            except Exception as e:
                logging.exception(e)
                print(e)
            return None

        for feature_member in self.root.findall('gml:featureMember', self.namespaces):
            for prezentacja in feature_member.findall('egb:PrezentacjaGraficzna', self.namespaces):
                pos_value = ("", "")
                pos_value = get_element_value('.//gml:pos', is_pos=True)

                justyfikacja = get_element_value('.//egb:justyfikacja')
                katObrotu = get_element_value('.//egb:katObrotu')
                tekst_value = get_element_value('.//egb:tekst')

                href_value = get_element_value('.//egb:obiektPrzedstawiany', is_href=True)
                
                data_PrezentacjaGraficzna.append([pos_value, katObrotu, justyfikacja, tekst_value, href_value])

        self.df_PrezentacjaGraficzna = pd.DataFrame(data_PrezentacjaGraficzna, columns=['pos', 'katObrotu', 'justyfikacja', 'tekst', 'obiektPrzedstawiany'])
        return self.df_PrezentacjaGraficzna

    def get_epsg_from_root(self):
        crs = None
        for feature_member in self.root:
            geometry_with_srs = feature_member.find('.//*[@srsName]')
            if geometry_with_srs is not None:
                crs = geometry_with_srs.attrib['srsName']
                break
        return crs.lstrip("urn:ogc:def:crs:")

    @staticmethod
    def fill_missing_values(main_df, *dfs, col='ID'):
        # Start with main_df as the base
        result_df = main_df.astype(str).copy()  # result_df = main_df.copy()
        
        for df in dfs:
            if df.empty or col not in df.columns:
                continue  # Skip to the next DataFrame

            df = df.astype(str)

            # Find common columns between result_df and the current df (excluding 'ID')
            common_columns = result_df.columns.intersection(df.columns).tolist()
            if col in common_columns:
                common_columns.remove(col)  # We don't want to fill the 'ID' column itself
            
            # Merge result_df with the current df on 'ID' using a left join
            temp_df = result_df.merge(df, on=col, how='left', suffixes=('', '_temp'))
            
            # Fill missing values in the common columns from the current df
            for col_name in common_columns:
                # Only apply combine_first if the temporary column has non-empty entries
                if temp_df[f"{col_name}_temp"].notna().any():
                    temp_df[col_name] = temp_df[col_name].combine_first(temp_df[f"{col_name}_temp"])
            
            # Drop the temporary columns used for filling
            temp_df = temp_df.drop(columns=[f"{col_name}_temp" for col_name in common_columns])
            # Update result_df to the latest filled version
            result_df = temp_df

        return result_df

    @staticmethod
    def get_crs_epsg(path):
        tree = ET.parse(path)
        root = tree.getroot()
        crs = None
        for feature_member in root:
            geometry_with_srs = feature_member.find('.//*[@srsName]')
            if geometry_with_srs is not None:
                crs = geometry_with_srs.attrib['srsName']
                break
        return crs.lstrip("urn:ogc:def:crs:")


if __name__ == '__main__':
    pass