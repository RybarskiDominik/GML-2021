from shapely.geometry import Polygon
import xml.etree.ElementTree as ET
from pathlib import Path
import pandas as pd
import numpy as np
import logging
import time
b6j277w9 = logging.getLogger(__name__)
' Description\n\n------------\nGMLParser – narzędzie do wczytywania, analizy i przetwarzania plików GML \nz ewidencji gruntów i budynków (EGiB) oraz obiektów topograficznych (OT) \nzgodnych ze schematami GUGiK.\n\nProgram odczytuje strukturę pliku GML, rozpoznaje przestrzeń nazw i układ współrzędnych (EPSG),\na następnie tworzy zestaw tabel (DataFrame) z danymi geometrycznymi i opisowymi.\n\nInstrukcja użycia:\n------------------\n1. Utwórz obiekt klasy GMLParser z podaniem ścieżki do pliku:\n      gml = GMLParser("sciezka/do/pliku.gml")\n\n2. Zainicjuj podstawowe parsowanie pliku:\n      gml.initialize_gml_parse()\n\n3. Utwórz dane graficzne (działki, budynki, granice):\n      df_graphic = gml.initialize_graphic_data()\n\n4. Utwórz dane osobowe i własnościowe:\n      df_personal = gml.initialize_personal_data()\n\n5.  Utwórz dane dodatkowe (powiązania, punkty, kontury):\n      df_additional = gml.initialize_additional_data()\n\nNajważniejsze funkcje:\n-----------------------\n- **initialize_gml_parse()** – główne parsowanie pliku GML.\n- **initialize_graphic_data()** – łączenie i przygotowanie danych graficznych.\n- **initialize_personal_data()** – tworzenie zestawienia właścicieli i jednostek rejestrowych.\n- **initialize_additional_data()** – uzupełnianie danych pomocniczych.\n- **get_epsg_from_root()** – wykrycie układu współrzędnych (EPSG).\n- **story_dataframes(), restory_dataframes()** – zapis i przywracanie danych po parsowaniu.\n\nhttps://www.gov.pl/web/gugik/schematy-aplikacyjne\n\n'

class GMLParser:

    def __init__(self, path=None):
        self.path = path
        self.valid = False
        self.df_GML_personal_data = pd.DataFrame()
        self.df_GML_graphic_data = pd.DataFrame()
        self.df_GML_sorted_działki = pd.DataFrame()
        self.df_GML_points_in_dzialki = pd.DataFrame()
        self.df_GML_budynki = pd.DataFrame()
        self.df_GML_dzialki = pd.DataFrame()
        self.df_GML_points = pd.DataFrame()
        self.df_GML_documents = pd.DataFrame()
        self.df_GML_personal_raw_data = pd.DataFrame()
        self.df_PrezentacjaGraficzna = pd.DataFrame()
        self.df_OT_Ogrodzenia = pd.DataFrame()
        self.df_OT_Budowle = pd.DataFrame()
        self.df_OT_Skarpa = pd.DataFrame()
        self.df_OT_BudynekNiewykazanyWEGIB = pd.DataFrame()
        self.df_EGB_JednostkaRejestrowaGruntow = pd.DataFrame()
        self.df_EGB_KonturUzytkuGruntowego = pd.DataFrame()
        self.df_EGB_KonturKlasyfikacyjny = pd.DataFrame()
        self.df_EGB_PunktGraniczny = pd.DataFrame()
        self.df_EGB_OsobaFizyczna = pd.DataFrame()
        self.df_EGB_Malzenstwo = pd.DataFrame()
        self.df_EGB_Instytucja = pd.DataFrame()
        self.df_EGB_AdresPodmiotu = pd.DataFrame()
        self.df_EGB_UdzialWeWlasnosci = pd.DataFrame()
        self.df_EGB_UdzialWeWladaniu = pd.DataFrame()
        self.df_EGB_PodmiotGrupowy = pd.DataFrame()
        self.df_EGB_PodmiotGrupowy_nazwaPelna = pd.DataFrame()
        self.df_EGB_PodmiotGrupowy_instytucja = pd.DataFrame()
        self.df_EGB_PodmiotGrupowy_osobaFizyczna = pd.DataFrame()
        self.df_EGB_PodmiotGrupowy_malzenstwo = pd.DataFrame()
        self.df_EGB_WspolnotaGruntowa = pd.DataFrame()
        self.df_EGB_WspolnotaGruntowa_nazwa = pd.DataFrame()
        self.df_EGB_WspolnotaGruntowa_spolkaZarzadajaca = pd.DataFrame()
        self.df_EGB_WspolnotaGruntowa_podmiotUprawniony = pd.DataFrame()
        self.df_EGB_WspolnotaGruntowa_malzenstwoUprawnione = pd.DataFrame()
        self.df_EGB_WspolnotaGruntowa_osobaFizycznaUprawniona = pd.DataFrame()
        self.df_EGB_DzialkaEwidencyjna = pd.DataFrame()
        self.df_EGB_Budynek = pd.DataFrame()
        self.df_EGB_AdresNieruchomosci = pd.DataFrame()
        self.df_EGB_Zmiana = pd.DataFrame()
        self.df_EGB_OperatTechniczny = pd.DataFrame()
        self.df_EGB_Dokument = pd.DataFrame()
        self.epsg = None
        self.root = None
        self.default_namespaces = {'gml': 'http://www.opengis.net/gml/3.2', 'egb': 'ewidencjaGruntowIBudynkow:1.0', 'xlink': 'http://www.w3.org/1999/xlink', 'ges2021': 'geodezyjnaEwidencjaSieciUzbrojeniaTerenu:1.0', 'ot2021': 'bazaDanychObiektowTopograficznych500:1.0'}
        if self.path and Path(self.path).exists():
            self.get_namespaces_and_root()
            self.get_epsg_from_root()
            self.valid = True
        else:
            return

    def get_namespaces_and_root(self):
        """Parse the GML file, extract root and namespaces."""
        try:
            namespaces = {}
            imirs5ny = ET.iterparse(self.path, events=('start', 'start-ns'))
            for x4fre0z7, wlgan466 in imirs5ny:
                if x4fre0z7 == 'start-ns':
                    hkhgkz9a, rc927gjr = wlgan466
                    namespaces[hkhgkz9a] = rc927gjr
                elif x4fre0z7 == 'start' and self.root is None:
                    self.root = wlgan466
            self.namespaces = namespaces
            self._ensure_required_namespaces()
        except ET.ParseError as e:
            b6j277w9.exception('XML parsing error: %s', e)
        except FileNotFoundError:
            b6j277w9.exception('File not found: %s', self.path)

    def _ensure_required_namespaces(self):
        """Ensures all required namespaces are present."""
        for hkhgkz9a, rc927gjr in self.default_namespaces.items():
            if hkhgkz9a not in self.namespaces:
                self.namespaces[hkhgkz9a] = rc927gjr

    def get_root(self):
        try:
            vwp5n46s = ET.parse(self.path)
            return vwp5n46s.getroot()
        except ET.ParseError as e:
            b6j277w9.exception('XML parsing error: %s', e)
            return None
        except FileNotFoundError:
            b6j277w9.exception('File not found: %s', self.path)
            return None

    def detect_namespaces(self):
        if self.root is None:
            return {}
        namespaces = {}
        for _, wlgan466 in ET.iterparse(self.path, events=['start-ns']):
            hkhgkz9a, rc927gjr = wlgan466
            namespaces[hkhgkz9a] = rc927gjr
        return namespaces

    def restory_dataframes(self, df_dict):
        self.df_GML_personal_data = df_dict.get('personal_data')
        self.df_GML_graphic_data = df_dict.get('graphic_data')
        self.df_GML_sorted_działki = df_dict.get('sorted_dzialki')
        self.df_GML_points_in_dzialki = df_dict.get('points_in_dzialki')
        self.df_GML_budynki = df_dict.get('budynki')
        self.df_GML_dzialki = df_dict.get('działki')
        self.df_GML_points = df_dict.get('points')
        self.df_GML_documents = df_dict.get('documents')
        self.epsg = df_dict.get('epsg')

    def story_dataframes(self):
        return {'personal_data': self.df_GML_personal_data, 'graphic_data': self.df_GML_graphic_data, 'sorted_dzialki': self.df_GML_sorted_działki, 'points_in_dzialki': self.df_GML_points_in_dzialki, 'budynki': self.df_GML_budynki, 'działki': self.df_GML_dzialki, 'points': self.df_GML_points, 'documents': self.df_GML_documents, 'epsg': self.epsg}

    def initialize_gml_parse(self):
        if self.root is None:
            return
        self._PrezentacjaGraficzna()
        self._OT_Ogrodzenia()
        self._OT_Budowle()
        self._OT_Skarpa()
        self._OT_BudynekNiewykazanyWEGIB()
        self._EGB_JednostkaRejestrowaGruntow()
        self._EGB_Malzenstwo()
        self._EGB_Instytucja()
        self._EGB_PodmiotGrupowy()
        self._EGB_WspolnotaGruntowa()
        self._EGB_OsobaFizyczna()
        self._EGB_KonturUzytkuGruntowego()
        self._EGB_KonturKlasyfikacyjny()
        self._EGB_UdzialWeWlasnosci()
        self._EGB_UdzialWeWladaniu()
        self._EGB_AdresPodmiotu()
        self._EGB_AdresNieruchomosci()
        self._EGB_PunktGraniczny()
        self._EGB_DzialkaEwidencyjna()
        self._EGB_Budynek()
        self._EGB_Zmiana()
        self._EGB_OperatTechniczny()
        self._EGB_Dokument()
        logging.debug('GML Parser - Initialize END.')

    def initialize_graphic_data(self):
        if self.root is None:
            return
        i0tliq1x = [('df_OT_Ogrodzenia', self.df_OT_Ogrodzenia), ('df_OT_Budowle', self.df_OT_Budowle), ('df_OT_Skarpa', self.df_OT_Skarpa), ('df_EGB_KonturUzytkuGruntowego', self.df_EGB_KonturUzytkuGruntowego), ('df_EGB_KonturKlasyfikacyjny', self.df_EGB_KonturKlasyfikacyjny), ('df_EGB_PunktGraniczny', self.df_EGB_PunktGraniczny), ('df_EGB_DzialkaEwidencyjna', self.df_EGB_DzialkaEwidencyjna), ('df_EGB_Budynek', self.df_EGB_Budynek), ('df_OT_BudynekNiewykazanyWEGIB', self.df_OT_BudynekNiewykazanyWEGIB), ('df_EGB_AdresNieruchomosci', self.df_EGB_AdresNieruchomosci)]
        self.merged_dfs = {}
        for i4vt8qg0, dae5vkdk in i0tliq1x:
            self.merged_dfs[i4vt8qg0] = self.merge_df_by_PrezentacjaGraficzna(dae5vkdk, i4vt8qg0)
        logging.debug('GML Parser - Merging graphic GML data completed.')
        self.df_GML_graphic_data = self.merged_dfs
        return self.merged_dfs

    def initialize_personal_data(self):
        if self.root is None:
            return
        imeddyb6 = ['idDzialki', 'numerKW', 'poleEwidencyjne', 'dokladnoscReprezentacjiPola', 'rodzajPrawa', 'udzialWlasnosci', 'rodzajWladania', 'udzialWladania', 'nazwaPelna', 'nazwaSkrocona', 'pierwszeImie', 'drugieImie', 'pierwszyCzlonNazwiska', 'drugiCzlonNazwiska', 'imieOjca', 'imieMatki', 'plec', 'pesel', 'regon', 'informacjaOSmierci', 'IDM', 'status', 'kraj', 'miejscowosc', 'kodPocztowy', 'ulica', 'numerPorzadkowy', 'numerLokalu', 'kraj_Kores.', 'miejscowosc_Kores.', 'kodPocztowy_Kores.', 'ulica_Kores.', 'numerPorzadkowy_Kores.', 'numerLokalu_Kores.', 'grupaRejestrowa', 'idJednostkiRejestrowej']
        df_GML_personal_data = pd.DataFrame(columns=imeddyb6)
        df_GML_sorted_działki = pd.DataFrame()
        l281zw90 = ['idDzialki', 'numerKW', 'poleEwidencyjne']
        try:
            zosxkrel = ['part1', 'part2']
            df_GML_sorted_działki = self.sort_df(self.df_EGB_DzialkaEwidencyjna, sort_by_columns=zosxkrel, on_columns=l281zw90)
        except Exception as e:
            df_GML_sorted_działki = self.df_EGB_DzialkaEwidencyjna[l281zw90]
            logging.exception(e)
            print(e)
        try:
            na1pbo25 = pd.merge(self.df_EGB_DzialkaEwidencyjna, self.df_EGB_JednostkaRejestrowaGruntow, how='outer', on='id-JRG')
        except Exception as e:
            df_GML_personal_raw_data = na1pbo25
            logging.exception(e)
            print(e)
        try:
            uy3lfu79 = pd.merge(self.df_EGB_UdzialWeWladaniu, self.df_EGB_UdzialWeWlasnosci, how='outer')
            k1k1p85t = pd.merge(na1pbo25, uy3lfu79, how='outer', on='id-JRG')
            m1rqiq5x = pd.DataFrame()
            m1rqiq5x = pd.merge(self.df_EGB_OsobaFizyczna, self.df_EGB_Instytucja, how='outer')
            m1rqiq5x = pd.merge(m1rqiq5x, self.df_EGB_PodmiotGrupowy_nazwaPelna, how='outer')
            m1rqiq5x = pd.merge(m1rqiq5x, self.df_EGB_WspolnotaGruntowa_nazwa, how='outer')
            m1rqiq5x = pd.merge(m1rqiq5x, self.df_EGB_AdresPodmiotu, how='left', left_on='adresZameldowania', right_on='AdresPodmiotu')
            m1rqiq5x = pd.merge(m1rqiq5x, self.df_EGB_AdresPodmiotu, how='left', left_on='adresStalegoPobytu', right_on='AdresPodmiotu', suffixes=('', '_Kores.'))
            m1rqiq5x = self.merge_dataframe(m1rqiq5x, self.df_EGB_AdresPodmiotu, how='left', left_on='adresSiedziby', right_on='AdresPodmiotu')
            ld6kp0x7 = self.merge_dataframe(self.df_EGB_Malzenstwo, m1rqiq5x, how='left', left_on='IDM', right_on='id')
            try:
                zvknhnf7 = self.merge_dataframe(self.df_EGB_PodmiotGrupowy_osobaFizyczna, m1rqiq5x, how='left', left_on='osobaFizyczna', right_on='id')
                f1tx8jzo = self.merge_dataframe(self.df_EGB_PodmiotGrupowy_instytucja[['id', 'regon', 'status', 'adresSiedziby', 'instytucja']], m1rqiq5x, how='left', left_on='instytucja', right_on='id')
                f4ea2o3z = self.merge_dataframe(self.df_EGB_PodmiotGrupowy_malzenstwo, ld6kp0x7, how='left', left_on='IDM', right_on='id')
            except Exception as e:
                logging.exception(e)
                logging.error('GML_Parser - PodmiotGrupowy error on dataframe merge')
                print(e)
            try:
                fhwcb2x0 = self.merge_dataframe(self.df_EGB_WspolnotaGruntowa_osobaFizycznaUprawniona, m1rqiq5x, how='left', left_on='osobaFizycznaUprawniona', right_on='id')
                i8sr0h00 = self.merge_dataframe(self.df_EGB_WspolnotaGruntowa_spolkaZarzadajaca, m1rqiq5x, how='left', left_on='spolkaZarzadajaca', right_on='id')
                tdjw7h44 = self.merge_dataframe(self.df_EGB_WspolnotaGruntowa_podmiotUprawniony, m1rqiq5x, how='left', left_on='podmiotUprawniony', right_on='id')
                ehzlkxlg = self.merge_dataframe(self.df_EGB_WspolnotaGruntowa_malzenstwoUprawnione, ld6kp0x7, how='left', left_on='IDM', right_on='id')
            except Exception as e:
                logging.exception(e)
                logging.error('GML_Parser - WspolnotaGruntowa error on dataframe merge')
                print(e)
            y07rzyq3 = [m1rqiq5x, ld6kp0x7, locals().get('df_GML_PodmiotGrupowy_osobaFizyczna'), locals().get('df_GML_PodmiotGrupowy_malzenstwo'), locals().get('df_GML_PodmiotGrupowy_instytucja'), locals().get('df_GML_WspolnotaGruntowa_osobaFizycznaUprawniona'), locals().get('df_GML_WspolnotaGruntowa_spolkaZarzadajaca'), locals().get('df_GML_WspolnotaGruntowa_podmiotUprawniony'), locals().get('df_GML_WspolnotaGruntowa_malzenstwoUprawnione')]
            daqiksjd = self.concat_dataframe(y07rzyq3)
            df_GML_personal_raw_data = self.merge_dataframe(k1k1p85t, daqiksjd, how='left', left_on='podmiot', right_on='id')
        except Exception as e:
            logging.exception(e)
            print(e)
        try:
            df_GML_personal_raw_data['IDM'] = self.fill_data_in_col(df_GML_personal_raw_data, main_col='IDM', fill_col='podmiot')
            df_GML_personal_raw_data['IDM'] = df_GML_personal_raw_data['IDM'].astype(str).str.slice(start=19, stop=26)
        except Exception as e:
            logging.exception(e)
            print(e)
        try:
            zosxkrel = ['part1', 'part2', 'IDM', 'Właściciele']
            df_GML_personal_raw_data = self.sort_df(df_GML_personal_raw_data, zosxkrel)
        except Exception as e:
            logging.exception(e)
            print(e)
        try:
            for zoixnw95 in imeddyb6:
                if zoixnw95 not in df_GML_personal_raw_data.columns:
                    df_GML_personal_raw_data[zoixnw95] = None
            df_GML_personal_data = df_GML_personal_raw_data[imeddyb6]
        except Exception as e:
            logging.exception(e)
            print(e)
        try:
            df_GML_personal_data = df_GML_personal_data.replace(['NaN', 'None', 'nan'], '').fillna('')
        except Exception as e:
            logging.exception(e)
            print(e)
        self.df_GML_personal_data = df_GML_personal_data
        self.df_GML_personal_raw_data = df_GML_personal_raw_data
        self.df_GML_sorted_działki = df_GML_sorted_działki
        logging.debug('GML Parser - Merging personal GML data completed.')
        return (self.df_GML_personal_data, self.df_GML_sorted_działki)

    def initialize_additional_data(self):
        if self.root is None:
            return
        yq45pu4g = ['idDzialki', 'numerKW', 'idPunktu', 'sposobPozyskania', 'spelnienieWarunkowDokl', 'rodzajStabilizacji', 'oznWMaterialeZrodlowym', 'numerOperatuTechnicznego', 'dodatkoweInformacje', 'poleEwidencyjne', 'dokladnoscReprezentacjiPola', 'geometria_punkt']
        try:
            oi3gdduo = self.df_EGB_PunktGraniczny.copy()
            yr8ts2bc = self.df_EGB_DzialkaEwidencyjna.copy()
            yr8ts2bc = yr8ts2bc.explode('punktGranicyDzialki')
            occmt9d1 = pd.merge(oi3gdduo, yr8ts2bc, how='left', left_on='id', right_on='punktGranicyDzialki', suffixes=('_punkt', '_Dz'))
            self.df_GML_points_in_dzialki = occmt9d1[yq45pu4g]
        except Exception as e:
            self.df_GML_points_in_dzialki = pd.DataFrame(columns=yq45pu4g)
            logging.exception(e)
            print(e)
        gmjhd4wg = ['idDzialki', 'numerKW', 'idBudynku', 'rodzajWgKST', 'liczbaKondygnacjiNadziemnych', 'liczbaKondygnacjiPodziemnych', 'powZabudowy', 'lacznaPowUzytkowaLokaliWyodrebnionych', 'lacznaPowUzytkowaLokaliNiewyodrebnionych', 'lacznaPowUzytkowaPomieszczenPrzynaleznych', 'dokumentWlasnosci', 'dodatkoweInformacje', 'nazwaMiejscowosci', 'idMiejscowosci', 'nazwaUlicy', 'idNazwyUlicy', 'numerPorzadkowy', 'numerLokalu']
        try:
            z218kfe9 = self.df_EGB_Budynek.copy()
            n90a6cx6 = self.df_OT_BudynekNiewykazanyWEGIB.copy()
            z218kfe9 = pd.concat([z218kfe9, n90a6cx6], ignore_index=True)
            ycgwguz5 = self.df_EGB_AdresNieruchomosci.copy()
            z218kfe9 = pd.merge(z218kfe9, self.df_EGB_DzialkaEwidencyjna, how='left', left_on='dzialkaZabudowana', right_on='id', suffixes=('_Bud', '_Dz'))
            z218kfe9 = pd.merge(z218kfe9, ycgwguz5, how='left', left_on='adresBudynku', right_on='id')
            self.df_GML_budynki = self.restore_df_columns(z218kfe9, gmjhd4wg)
        except Exception as e:
            self.df_GML_budynki = pd.DataFrame(columns=gmjhd4wg)
            logging.exception(e)
            print(e)
        gs676x02 = ['idDzialki', 'numerKW', 'poleEwidencyjne', 'dokladnoscReprezentacjiPola', 'Obl. pow.', 'klasouzytek', 'grupaRejestrowa', 'idJednostkiRejestrowej']
        try:
            xl15ospu = self.df_EGB_DzialkaEwidencyjna.copy()
            p3kjqdz2 = self.df_EGB_JednostkaRejestrowaGruntow.copy()
            xl15ospu = pd.merge(xl15ospu, p3kjqdz2, how='outer', on='id-JRG')
            xl15ospu['Obl. pow.'] = None
            xl15ospu = self.poprawka_pow(xl15ospu, 'geometria', self.epsg)
            xl15ospu = self.restore_df_columns(xl15ospu, gs676x02)
            self.df_GML_dzialki = xl15ospu[gs676x02]
        except Exception as e:
            self.df_GML_dzialki = pd.DataFrame(columns=gs676x02)
            logging.exception(e)
            print(e)
        r5w5d9e6 = ['idPunktu', 'geometria', 'sposobPozyskania', 'spelnienieWarunkowDokl', 'rodzajStabilizacji', 'oznWMaterialeZrodlowym', 'numerOperatuTechnicznego', 'dodatkoweInformacje']
        try:
            sj60fm4i = self.df_EGB_PunktGraniczny.copy()
            self.df_GML_points = sj60fm4i[r5w5d9e6]
        except Exception as e:
            self.df_GML_points = pd.DataFrame(columns=r5w5d9e6)
            logging.exception(e)
            print(e)
        logging.debug('GML Parser - Merging additional GML data completed.')
        return

    def initialize_documents_data(self):
        k4ou6zx8 = pd.DataFrame()
        df_GML_dzialki = pd.DataFrame()
        df_EGB_JednostkaRejestrowaGruntow = self.df_EGB_JednostkaRejestrowaGruntow.copy()
        df_EGB_DzialkaEwidencyjna = self.df_EGB_DzialkaEwidencyjna.copy()
        df_EGB_Zmiana = self.df_EGB_Zmiana.copy()
        try:
            df_GML_dzialki = pd.merge(df_EGB_DzialkaEwidencyjna, df_EGB_JednostkaRejestrowaGruntow, how='left', on='id-JRG', suffixes=('', '_JRG'))
            jc6u7hpa = df_GML_dzialki[['idDzialki', 'dokument2', 'operatTechniczny2']]
            pk2g3rmv = jc6u7hpa.explode('dokument2').loc[:, ['idDzialki', 'dokument2']].dropna(subset=['dokument2'])
            gqondanh = jc6u7hpa.explode('operatTechniczny2').loc[:, ['idDzialki', 'operatTechniczny2']].dropna(subset=['operatTechniczny2'])
            jc6u7hpa = pd.concat([pk2g3rmv, gqondanh], ignore_index=True)
            r7vs05jk = pd.concat([df_GML_dzialki[['idDzialki', 'podstawaUtworzeniaWersjiObiektu']], df_GML_dzialki[['idDzialki', 'podstawaUtworzeniaWersjiObiektu_JRG']].rename(columns={'podstawaUtworzeniaWersjiObiektu_JRG': 'podstawaUtworzeniaWersjiObiektu'})], ignore_index=True)
            ywpyra99 = df_EGB_Zmiana.explode('dokument1').loc[:, ['id', 'dataAkceptacjiZmiany', 'dataPrzyjeciaZgloszeniaZmiany', 'nrZmiany', 'opisZmiany', 'dokument1']].dropna(subset=['dokument1'])
            kqd4idkk = df_EGB_Zmiana.explode('operatTechniczny1').loc[:, ['id', 'dataAkceptacjiZmiany', 'dataPrzyjeciaZgloszeniaZmiany', 'nrZmiany', 'opisZmiany', 'operatTechniczny1']].dropna(subset=['operatTechniczny1'])
            ifoadjzi = pd.concat([ywpyra99, kqd4idkk], ignore_index=True)
            pw6ddcfi = self.merge_dataframe(r7vs05jk, ifoadjzi, how='left', left_on='podstawaUtworzeniaWersjiObiektu', right_on='id')
            pw6ddcfi = pw6ddcfi[['idDzialki', 'dataAkceptacjiZmiany', 'dataPrzyjeciaZgloszeniaZmiany', 'opisZmiany', 'dokument1', 'operatTechniczny1']]
            p9bi550c = pd.concat([jc6u7hpa, pw6ddcfi], ignore_index=True)
            k4ou6zx8 = p9bi550c[['idDzialki', 'dataAkceptacjiZmiany', 'dataPrzyjeciaZgloszeniaZmiany', 'opisZmiany', 'dokument1', 'operatTechniczny1', 'dokument2', 'operatTechniczny2']]
            k4ou6zx8 = k4ou6zx8.copy()
            k4ou6zx8['dokument'] = k4ou6zx8['dokument1'].combine_first(k4ou6zx8['dokument2'])
            k4ou6zx8['operatTechniczny'] = k4ou6zx8['operatTechniczny1'].combine_first(k4ou6zx8['operatTechniczny2'])
            k4ou6zx8 = k4ou6zx8.drop(columns=['dokument1', 'dokument2', 'operatTechniczny1', 'operatTechniczny2'])
            k4ou6zx8 = k4ou6zx8.replace('nan', np.nan)
            k4ou6zx8 = self.merge_dataframe(k4ou6zx8, self.df_EGB_Dokument, how='left', left_on='dokument', right_on='id')
            k4ou6zx8 = self.merge_dataframe(k4ou6zx8, self.df_EGB_OperatTechniczny, how='left', left_on='operatTechniczny', right_on='id')
            u3jiidrx = {'operatTechniczny': 'Operat', 'dokument': 'Dokument'}
            for zoixnw95, jv4o82gw in u3jiidrx.items():
                k4ou6zx8.loc[k4ou6zx8[zoixnw95].notna() & (k4ou6zx8[zoixnw95] != ''), zoixnw95] = jv4o82gw
            k4ou6zx8['Nazwa twórcy'] = k4ou6zx8['nazwaTworcyDokumentu'].combine_first(k4ou6zx8['nazwaTworcy'])
            k4ou6zx8['Data'] = k4ou6zx8['dataDokumentu'].combine_first(k4ou6zx8['dataPrzyjeciaDoPZGIK'])
            k4ou6zx8['Sygnatura'] = k4ou6zx8['sygnaturaDokumentu'].combine_first(k4ou6zx8['identyfikatorOperatu'])
            k4ou6zx8['Typ'] = k4ou6zx8['dokument'].combine_first(k4ou6zx8['operatTechniczny'])
            k4ou6zx8 = k4ou6zx8.drop(columns=['dokument', 'operatTechniczny', 'nazwaTworcyDokumentu', 'nazwaTworcy', 'dataDokumentu', 'dataPrzyjeciaDoPZGIK', 'identyfikatorOperatu'])
            k4ou6zx8 = k4ou6zx8.replace({'None': ''}).replace({'[]': ''})
            k4ou6zx8 = k4ou6zx8[['idDzialki', 'Typ', 'rodzajDokumentu', 'Data', 'Sygnatura', 'oznKancelaryjneDokumentu', 'Nazwa twórcy', 'opisDokumentu', 'opisOperatu', 'opisZmiany']]
            qpvvx49n = {'1': 'umowaAktNotarialny', '2': 'aktWlasnosciZiemi', '3': 'decyzjaAdminInnaNizAWZ', '4': 'orzeczenieSaduPostanowienieWyrok', '5': 'wyciagOdpisZKsiegiWieczystej', '6': 'wyciagOdpisZKsiegiHipotecznej', '7': 'odpisAktKWLubZbioruDokumentu', '8': 'zawiadomienieZWydzialuKW', '9': 'wniosekWSprawieZmiany', '10': 'wyciagZDokumentacjiBudowyBudynku', '11': 'protokol', '12': 'ustawa', '13': 'rozporzadzenie', '14': 'uchwala', '15': 'zarzadzenie', '16': 'odpisWyciagZInnegoRejestruPublicznego', '17': 'pelnomocnictwo', '19': 'innyDokument', '20': 'dokArchitektoniczoBud', '21': 'dokPlanistyczny', '22': 'aktPoswiadczeniaDziedziczenia', '23': 'zawiadomienieZPESEL', '24': 'zgloszenieZmianySposobuUzytkowania'}
            k4ou6zx8['rodzajDokumentu'] = k4ou6zx8['rodzajDokumentu'].astype(str).map(qpvvx49n).fillna('')
            self.df_GML_documents = k4ou6zx8
            return self.df_GML_documents
        except Exception as e:
            logging.exception(e)
            print(e)
            self.df_GML_documents = pd.DataFrame()
            return self.df_GML_documents

    def replace_None_values(self, df):
        df = df.copy()
        try:
            pass
        except Exception as e:
            logging.exception(e)
            print(e)
        "\n        for col in columns:\n            if col in df.columns:\n                df[col] = df[col].replace([None, 'None', 'NaN', 'nan'], '')\n        "
        return df

    def restore_df_columns(self, df, default_columns):
        try:
            df = df.copy()
            for zoixnw95 in default_columns:
                if zoixnw95 not in df.columns:
                    df[zoixnw95] = None
            df = df[default_columns]
        except Exception as e:
            logging.exception(e)
            print(e)
        return df

    def merge_df_by_PrezentacjaGraficzna(self, df, name=None):
        if df.empty:
            return df
        else:
            try:
                df = pd.merge(self.df_PrezentacjaGraficzna, df, how='right', left_on='obiektPrzedstawiany', right_on='id')
            except Exception as e:
                logging.exception(e)
                logging.error(name)
                print(e)
        return df

    def sort_df(self, df, sort_by_columns, on_columns=None):
        if on_columns:
            wcdbj0fj = df[on_columns].copy()
        else:
            wcdbj0fj = df.copy()
        wcdbj0fj[['part1', 'part2']] = wcdbj0fj['idDzialki'].str.rsplit('.', n=1, expand=True)
        wcdbj0fj['part2'] = wcdbj0fj['part2'].str.replace('/', '.')
        wcdbj0fj['part2'] = wcdbj0fj['part2'].astype(float)
        sfycxaf0 = ['part1', 'part2'] + [zoixnw95 for zoixnw95 in sort_by_columns if zoixnw95 in wcdbj0fj.columns]
        wcdbj0fj = wcdbj0fj.sort_values(sfycxaf0)
        return wcdbj0fj.drop(columns=['part1', 'part2'])

    def sort_df_OLD(self, df):
        df = df[['idDzialki', 'numerKW', 'poleEwidencyjne']]
        wcdbj0fj = df.copy()
        wcdbj0fj[['part1', 'part2']] = wcdbj0fj['idDzialki'].str.rsplit('.', n=1, expand=True)
        wcdbj0fj['part2'] = wcdbj0fj['part2'].str.replace('/', '.')
        wcdbj0fj['part2'] = wcdbj0fj['part2'].astype(float)
        wcdbj0fj = wcdbj0fj.sort_values(['part1', 'part2'])
        rrsai8xx = wcdbj0fj.drop(columns=['part1', 'part2'])
        return rrsai8xx

    def merge_col(self, df, col1, col2):
        df[col1] = df[col2].fillna(df[col1])
        return df

    def fill_data_in_col(self, df, main_col, fill_col):
        try:
            df = df.copy()
            df[main_col] = df[main_col].replace('', None)
            df[main_col] = df[main_col].replace('nan', None)
            df[main_col] = df[main_col].where(df[main_col].isna(), df[fill_col])
        except Exception as e:
            logging.exception(e)
            print(e)
        return df[main_col]

    def _get_element_value(self, element, element_path, pos=False, coordinates=False, lista=False):
        try:
            elsdbw1v = element.findall(element_path, self.namespaces)
            if not elsdbw1v:
                return None
            a8j6oa61 = []
            for upz5tb7b in elsdbw1v:
                if upz5tb7b is not None and upz5tb7b.text:
                    text = upz5tb7b.text.strip()
                    if pos:
                        f078rigi, awl2pit5 = map(float, text.split())
                        return (round(f078rigi, 2), round(awl2pit5, 2))
                    elif coordinates:
                        cmngtlv9 = [float(j039o8jo) for j039o8jo in text.split()]
                        ryr60amh = [(cmngtlv9[a9icop4s], cmngtlv9[a9icop4s + 1]) for a9icop4s in range(0, len(cmngtlv9), 2)]
                        if lista:
                            a8j6oa61.append(ryr60amh)
                        else:
                            a8j6oa61.extend(ryr60amh)
                    else:
                        return text
            return a8j6oa61 if a8j6oa61 else None
        except Exception as e:
            b6j277w9.exception('Error extracting element value: %s', e)
            return None

    def _get_element_klasouzytek_list(self, element, element_path):
        """Extracts a list of Klasoużytek values from the XML element."""
        try:
            elsdbw1v = element.findall(element_path, self.namespaces)
            hf4jvas6 = []
            for ma118u8z in elsdbw1v:
                efcd4e5e = self._get_element_value(ma118u8z, './/egb:OFU')
                yotyr8s1 = self._get_element_value(ma118u8z, './/egb:OZU')
                zdqgq5x8 = self._get_element_value(ma118u8z, './/egb:OZK')
                hmzu5ia5 = self._get_element_value(ma118u8z, './/egb:powierzchnia')
                hf4jvas6.append([efcd4e5e, yotyr8s1, zdqgq5x8, hmzu5ia5])
            return hf4jvas6
        except Exception as e:
            b6j277w9.exception('Błąd podczas pobierania listy Klasoużytek: %s', e)
            return []

    def _get_element_href_list(self, element, element_path):
        """Pobiera listę wartości atrybutów xlink:href dla EGB_PodmiotGrupowy."""
        try:
            elsdbw1v = element.findall(element_path, self.namespaces)
            return [h15xdttb.attrib.get('{http://www.w3.org/1999/xlink}href') for h15xdttb in elsdbw1v if h15xdttb is not None]
        except Exception as e:
            b6j277w9.exception('Błąd podczas pobierania atrybutów href: %s', e)
            return []

    def _get_element_href(self, element, element_path):
        """Pobiera wartość atrybutu xlink:href."""
        try:
            upz5tb7b = element.find(element_path, self.namespaces)
            return upz5tb7b.attrib.get('{http://www.w3.org/1999/xlink}href') if upz5tb7b is not None else None
        except Exception as e:
            b6j277w9.exception('Błąd podczas pobierania atrybutu href: %s', e)
            return None

    def _get_podmiot(self, element, element_path):
        """Pobiera identyfikator podmiotu we władaniu (ID lub xlink:href)."""
        try:
            we0l6kyk = element.find(element_path, self.namespaces)
            if we0l6kyk is None:
                return None
            for r7al0g09 in ['egb:instytucja1', 'egb:malzenstwo', 'egb:osobaFizyczna', 'egb:podmiotGrupowy', 'egb:wspolnotaGruntowa']:
                blp0aqs4 = we0l6kyk.find(f'.//{r7al0g09}', self.namespaces)
                if blp0aqs4 is not None:
                    pr6n2o5x = blp0aqs4.attrib.get('{http://www.w3.org/1999/xlink}href')
                    if pr6n2o5x:
                        return pr6n2o5x
            return None
        except Exception as e:
            b6j277w9.exception('Błąd podczas pobierania podmiotu: %s', e)
            return None

    def _iterate_features(self, tag):
        for xkwc447g in self.root.findall('gml:featureMember', self.namespaces):
            for wlgan466 in xkwc447g.findall(tag, self.namespaces):
                yield wlgan466

    def _OT_Ogrodzenia(self):
        columns = ['id', 'rodzajOgrodzenia', 'geometria']
        lxrskj21 = []
        for qra8zqzt in self.root.findall('gml:featureMember', self.namespaces):
            for yd2oxzwc in qra8zqzt.findall('ot2021:OT_Ogrodzenia', self.namespaces):
                pisapeu0 = yd2oxzwc.attrib.get('{http://www.opengis.net/gml/3.2}id')
                z9sus6ak = self._get_element_value(yd2oxzwc, './/ot2021:rodzajOgrodzenia')
                k0yevzyb = self._get_element_value(yd2oxzwc, './/gml:posList', coordinates=True)
                if not k0yevzyb:
                    try:
                        k0yevzyb = self._get_element_value(yd2oxzwc, './/gml:pos', coordinates=True)
                    except Exception as e:
                        logging.exception(e)
                        print(e)
                        k0yevzyb = []
                lxrskj21.append([pisapeu0, z9sus6ak, k0yevzyb])
        self.df_OT_Ogrodzenia = pd.DataFrame(lxrskj21, columns=columns)
        return self.df_OT_Ogrodzenia

    def _OT_Budowle(self):
        columns = ['id', 'rodzajBudowli', 'geometria']
        lxrskj21 = []
        for qra8zqzt in self.root.findall('gml:featureMember', self.namespaces):
            for bvao2wc1 in qra8zqzt.findall('ot2021:OT_Budowle', self.namespaces):
                pisapeu0 = bvao2wc1.attrib.get('{http://www.opengis.net/gml/3.2}id')
                atpqlzoc = self._get_element_value(bvao2wc1, './/ot2021:rodzajBudowli')
                k0yevzyb = self._get_element_value(bvao2wc1, './/gml:posList', coordinates=True)
                if not k0yevzyb:
                    try:
                        k0yevzyb = self._get_element_value(bvao2wc1, './/gml:pos', coordinates=True)
                    except Exception as e:
                        logging.exception(e)
                        print(e)
                        k0yevzyb = []
                lxrskj21.append([pisapeu0, atpqlzoc, k0yevzyb])
        self.df_OT_Budowle = pd.DataFrame(lxrskj21, columns=columns)
        return self.df_OT_Budowle

    def _OT_Skarpa(self):
        columns = ['id', 'rodzajSkarpy', 'poczatekGorySkarpy', 'koniecGorySkarpy', 'geometria']
        lxrskj21 = []
        for qra8zqzt in self.root.findall('gml:featureMember', self.namespaces):
            for xajn8591 in qra8zqzt.findall('ot2021:OT_Skarpa', self.namespaces):
                pisapeu0 = xajn8591.attrib.get('{http://www.opengis.net/gml/3.2}id')
                fkml8q1v = self._get_element_value(xajn8591, './/ot2021:rodzajSkarpy')
                cv3dpwz0 = []
                cyi9of6o = xajn8591.find('.//ot2021:poczatekGorySkarpy', self.namespaces)
                if cyi9of6o is not None:
                    pos = cyi9of6o.find('.//gml:pos', self.namespaces)
                    if pos is not None and pos.text:
                        cv3dpwz0 = pos.text.strip().split()
                wgu7vdte = []
                a39u144l = xajn8591.find('.//ot2021:koniecGorySkarpy', self.namespaces)
                if a39u144l is not None:
                    pos = a39u144l.find('.//gml:pos', self.namespaces)
                    if pos is not None and pos.text:
                        wgu7vdte = pos.text.strip().split()
                pvdp93t5 = xajn8591.find('.//ot2021:geometria', self.namespaces)
                if pvdp93t5 is not None:
                    g0v8t1nb = pvdp93t5.find('.//gml:posList', self.namespaces)
                    coordinates = g0v8t1nb.text.strip().split() if g0v8t1nb is not None else []
                    k0yevzyb = [(float(coordinates[a9icop4s]), float(coordinates[a9icop4s + 1])) for a9icop4s in range(0, len(coordinates), 2)]
                else:
                    k0yevzyb = []
                lxrskj21.append([pisapeu0, fkml8q1v, cv3dpwz0, wgu7vdte, k0yevzyb])
        self.df_OT_Skarpa = pd.DataFrame(lxrskj21, columns=columns)
        return self.df_OT_Skarpa

    def _OT_BudynekNiewykazanyWEGIB(self):
        columns = ['id', 'idBudynku', 'koniecWersjaObiekt', 'rodzajWgKST', 'liczbaKondygnacjiNadziemnych', 'liczbaKondygnacjiPodziemnych', 'status', 'zrodlo', 'dataPrzyjeciaDoZasobu', 'geometria']
        lxrskj21 = []
        for qra8zqzt in self.root.findall('gml:featureMember', self.namespaces):
            for b38yyfq5 in qra8zqzt.findall('ot2021:OT_BudynekNiewykazanyWEGIB', self.namespaces):
                pisapeu0 = b38yyfq5.attrib.get('{http://www.opengis.net/gml/3.2}id')
                iy1oy6bl = 'Budynek w BDOT'
                npx7af4e = self._get_element_value(b38yyfq5, './/ot2021:koniecWersjaObiekt')
                k0yevzyb = self._get_element_value(b38yyfq5, './/gml:posList', coordinates=True)
                if not k0yevzyb:
                    try:
                        k0yevzyb = self._get_element_value(b38yyfq5, './/gml:pos', coordinates=True)
                    except Exception as e:
                        logging.exception(e)
                        print(e)
                        k0yevzyb = []
                hd2x9ur4 = self._get_element_value(b38yyfq5, './/ot2021:rodzajKST')
                ll3j2n2f = self._get_element_value(b38yyfq5, './/ot2021:liczbaKondygnacjiNadziemnych')
                wr0t6yo0 = self._get_element_value(b38yyfq5, './/ot2021:liczbaKondygnacjiPodziemnych')
                n7apa2gn = self._get_element_value(b38yyfq5, './/ot2021:status')
                wbtbudem = self._get_element_value(b38yyfq5, './/ot2021:zrodlo')
                rh3pq3ij = self._get_element_value(b38yyfq5, './/ot2021:dataPrzyjeciaDoZasobu')
                lxrskj21.append([pisapeu0, iy1oy6bl, npx7af4e, hd2x9ur4, ll3j2n2f, wr0t6yo0, n7apa2gn, wbtbudem, rh3pq3ij, k0yevzyb])
        self.df_OT_BudynekNiewykazanyWEGIB = pd.DataFrame(lxrskj21, columns=columns)
        return self.df_OT_BudynekNiewykazanyWEGIB

    def _EGB_JednostkaRejestrowaGruntow(self):
        columns = ['id-JRG', 'idJednostkiRejestrowej', 'grupaRejestrowa', 'podstawaUtworzeniaWersjiObiektu']
        lxrskj21 = []
        for qra8zqzt in self.root.findall('gml:featureMember', self.namespaces):
            for iointgb2 in qra8zqzt.findall('egb:EGB_JednostkaRejestrowaGruntow', self.namespaces):
                id = iointgb2.attrib.get('{http://www.opengis.net/gml/3.2}id')
                t4erabpl = self._get_element_value(iointgb2, './/egb:idJednostkiRejestrowej')
                mm2ahybr = self._get_element_value(iointgb2, './/egb:grupaRejestrowa')
                z5uyo10e = self._get_element_href(iointgb2, './/egb:podstawaUtworzeniaWersjiObiektu')
                lxrskj21.append([id, t4erabpl, mm2ahybr, z5uyo10e])
        self.df_EGB_JednostkaRejestrowaGruntow = pd.DataFrame(lxrskj21, columns=columns)
        return self.df_EGB_JednostkaRejestrowaGruntow

    def _EGB_OsobaFizyczna(self):
        columns = ['id', 'pierwszeImie', 'pierwszyCzlonNazwiska', 'drugiCzlonNazwiska', 'drugieImie', 'imieOjca', 'imieMatki', 'pesel', 'plec', 'status', 'informacjaOSmierci', 'adresZameldowania', 'adresStalegoPobytu']
        lxrskj21 = []
        m7tyr133 = {'1': 'M', '2': 'K'}
        for qra8zqzt in self.root.findall('gml:featureMember', self.namespaces):
            for yi82tbvr in qra8zqzt.findall('egb:EGB_OsobaFizyczna', self.namespaces):
                id = yi82tbvr.attrib.get('{http://www.opengis.net/gml/3.2}id')
                qylj9c6c = self._get_element_value(yi82tbvr, './/egb:pierwszeImie')
                nba239r2 = self._get_element_value(yi82tbvr, './/egb:pierwszyCzlonNazwiska')
                xbq3z5sy = self._get_element_value(yi82tbvr, './/egb:drugiCzlonNazwiska')
                qkt9klqk = self._get_element_value(yi82tbvr, './/egb:drugieImie')
                l1hi100p = self._get_element_value(yi82tbvr, './/egb:imieOjca')
                ra3wqnyu = self._get_element_value(yi82tbvr, './/egb:imieMatki')
                drs46trx = self._get_element_value(yi82tbvr, './/egb:pesel')
                tvx4u613 = self._get_element_value(yi82tbvr, './/egb:plec')
                tvx4u613 = m7tyr133.get(tvx4u613, tvx4u613)
                n7apa2gn = self._get_element_value(yi82tbvr, './/egb:status')
                o5xes9g1 = self._get_element_value(yi82tbvr, './/egb:informacjaOSmierci')
                oi184l2r = self._get_element_href(yi82tbvr, './/egb:adresZameldowania') or self._get_element_href(yi82tbvr, './/egb:adresOsobyFizycznej')
                wzn56che = self._get_element_href(yi82tbvr, './/egb:adresStalegoPobytu') or self._get_element_href(yi82tbvr, './/egb:adresKorespondencyjnyOF')
                lxrskj21.append([id, qylj9c6c, nba239r2, xbq3z5sy, qkt9klqk, l1hi100p, ra3wqnyu, drs46trx, tvx4u613, n7apa2gn, o5xes9g1, oi184l2r, wzn56che])
        self.df_EGB_OsobaFizyczna = pd.DataFrame(lxrskj21, columns=columns)
        return self.df_EGB_OsobaFizyczna

    def _EGB_Malzenstwo(self):
        """Parsuje elementy EGB_Malzenstwo i zwraca DataFrame."""
        columns = ['id', 'IDM', 'status']
        lxrskj21 = []
        rcavz7z6 = {34: 'Małżeństwo', 35: 'Małżeństwo'}
        for qra8zqzt in self.root.findall('gml:featureMember', self.namespaces):
            for npvkk4ty in qra8zqzt.findall('egb:EGB_Malzenstwo', self.namespaces):
                id = npvkk4ty.attrib.get('{http://www.opengis.net/gml/3.2}id')
                qtj9fq08 = self._get_element_href(npvkk4ty, './/egb:osobaFizyczna2')
                eaiq6voh = self._get_element_href(npvkk4ty, './/egb:osobaFizyczna3')
                n7apa2gn = self._get_element_value(npvkk4ty, './/egb:status')
                n7apa2gn = rcavz7z6.get(int(n7apa2gn), n7apa2gn)
                lxrskj21.append([id, qtj9fq08, n7apa2gn])
                lxrskj21.append([id, eaiq6voh, n7apa2gn])
        self.df_EGB_Malzenstwo = pd.DataFrame(lxrskj21, columns=columns)
        return self.df_EGB_Malzenstwo

    def _EGB_Instytucja(self):
        columns = ['id', 'nazwaPelna', 'nazwaSkrocona', 'regon', 'status', 'adresSiedziby']
        lxrskj21 = []
        for qra8zqzt in self.root.findall('gml:featureMember', self.namespaces):
            for gy96zw8l in qra8zqzt.findall('egb:EGB_Instytucja', self.namespaces):
                id = gy96zw8l.attrib.get('{http://www.opengis.net/gml/3.2}id')
                exfpugwe = self._get_element_value(gy96zw8l, './/egb:nazwaPelna')
                gn57pid6 = self._get_element_value(gy96zw8l, './/egb:nazwaSkrocona')
                rchhl8ea = self._get_element_value(gy96zw8l, './/egb:regon')
                n7apa2gn = self._get_element_value(gy96zw8l, './/egb:status')
                ct3x66tc = self._get_element_href(gy96zw8l, './/egb:adresSiedziby') or self._get_element_href(gy96zw8l, './/egb:adresInstytucji')
                lxrskj21.append([id, exfpugwe, gn57pid6, rchhl8ea, n7apa2gn, ct3x66tc])
        self.df_EGB_Instytucja = pd.DataFrame(lxrskj21, columns=columns)
        return self.df_EGB_Instytucja

    def _EGB_PodmiotGrupowy(self):
        columns = ['id', 'nazwaPelna', 'nazwaSkrocona', 'regon', 'status', 'adresSiedziby']
        w8dl0tcd = columns + ['instytucja']
        yw4v0c96 = columns + ['osobaFizyczna']
        qk1i5ys5 = columns + ['IDM']
        dvr1s5sw = []
        y43069hu = []
        m6bb8pv6 = []
        l9759rvr = []
        for qra8zqzt in self.root.findall('gml:featureMember', self.namespaces):
            for blp0aqs4 in qra8zqzt.findall('egb:EGB_PodmiotGrupowy', self.namespaces):
                crps3z4f = False
                id = blp0aqs4.attrib.get('{http://www.opengis.net/gml/3.2}id')
                exfpugwe = self._get_element_value(blp0aqs4, './/egb:nazwaPelna')
                gn57pid6 = self._get_element_value(blp0aqs4, './/egb:nazwaSkrocona')
                rchhl8ea = self._get_element_value(blp0aqs4, './/egb:regon')
                n7apa2gn = self._get_element_value(blp0aqs4, './/egb:status')
                ct3x66tc = self._get_element_value(blp0aqs4, './/egb:adresSiedziby')
                if crps3z4f is False:
                    dvr1s5sw.append([id, exfpugwe, gn57pid6, rchhl8ea, n7apa2gn, ct3x66tc])
                    crps3z4f = True
                for cvipjo9j in blp0aqs4.findall('.//egb:instytucja', self.namespaces):
                    gy96zw8l = self._get_element_href(cvipjo9j, '.')
                    y43069hu.append([id, exfpugwe, gn57pid6, rchhl8ea, n7apa2gn, ct3x66tc, gy96zw8l])
                for cvipjo9j in blp0aqs4.findall('.//egb:osobaFizyczna4', self.namespaces):
                    ug8isf70 = self._get_element_href(cvipjo9j, '.')
                    m6bb8pv6.append([id, exfpugwe, gn57pid6, rchhl8ea, n7apa2gn, ct3x66tc, ug8isf70])
                for cvipjo9j in blp0aqs4.findall('.//egb:malzenstwo3', self.namespaces):
                    npvkk4ty = self._get_element_href(cvipjo9j, '.')
                    l9759rvr.append([id, exfpugwe, gn57pid6, rchhl8ea, n7apa2gn, ct3x66tc, npvkk4ty])
        self.df_EGB_PodmiotGrupowy_nazwaPelna = pd.DataFrame(dvr1s5sw, columns=columns)
        self.df_EGB_PodmiotGrupowy_instytucja = pd.DataFrame(y43069hu, columns=w8dl0tcd)
        self.df_EGB_PodmiotGrupowy_osobaFizyczna = pd.DataFrame(m6bb8pv6, columns=yw4v0c96)
        self.df_EGB_PodmiotGrupowy_malzenstwo = pd.DataFrame(l9759rvr, columns=qk1i5ys5)
        return (self.df_EGB_PodmiotGrupowy_nazwaPelna, self.df_EGB_PodmiotGrupowy_instytucja, self.df_EGB_PodmiotGrupowy_osobaFizyczna, self.df_EGB_PodmiotGrupowy_malzenstwo)

    def _EGB_WspolnotaGruntowa(self):
        columns = ['id', 'nazwaPelna', 'status']
        ddseyky8 = columns + ['spolkaZarzadajaca']
        vwya6xa5 = columns + ['podmiotUprawniony']
        oy40s2lf = columns + ['IDM']
        zhm3h6ic = columns + ['osobaFizycznaUprawniona']
        pve36btq = []
        ogt4zpjl = []
        u5nkzy5m = []
        r4568y9r = []
        d5bu42df = []
        for qra8zqzt in self.root.findall('gml:featureMember', self.namespaces):
            for ww7vfxk7 in qra8zqzt.findall('egb:EGB_WspolnotaGruntowa', self.namespaces):
                kfqreaf1 = False
                jd2bu856 = ww7vfxk7.attrib.get('{http://www.opengis.net/gml/3.2}id')
                ehuby3xa = self._get_element_value(ww7vfxk7, './/egb:nazwa')
                n7apa2gn = self._get_element_value(ww7vfxk7, './/egb:status')
                if kfqreaf1 is False:
                    pve36btq.append([jd2bu856, ehuby3xa, n7apa2gn])
                    kfqreaf1 = True
                for xudkcbvn in ww7vfxk7.findall('.//egb:spolkaZarzadajaca', self.namespaces):
                    idxql1h6 = self._get_element_href(xudkcbvn, '.')
                    ogt4zpjl.append([jd2bu856, ehuby3xa, n7apa2gn, idxql1h6])
                for xudkcbvn in ww7vfxk7.findall('.//egb:podmiotUprawniony', self.namespaces):
                    qxofolo6 = self._get_element_href(xudkcbvn, '.')
                    u5nkzy5m.append([jd2bu856, ehuby3xa, n7apa2gn, qxofolo6])
                for xudkcbvn in ww7vfxk7.findall('.//egb:malzenstwoUprawnione', self.namespaces):
                    ip23wriu = self._get_element_href(xudkcbvn, '.')
                    r4568y9r.append([jd2bu856, ehuby3xa, n7apa2gn, ip23wriu])
                for xudkcbvn in ww7vfxk7.findall('.//egb:osobaFizycznaUprawniona', self.namespaces) + ww7vfxk7.findall('.//egb:osobaUprawniona', self.namespaces):
                    cqynl2dh = self._get_element_href(xudkcbvn, '.')
                    d5bu42df.append([jd2bu856, ehuby3xa, n7apa2gn, cqynl2dh])
        self.df_EGB_WspolnotaGruntowa_nazwa = pd.DataFrame(pve36btq, columns=columns)
        self.df_EGB_WspolnotaGruntowa_spolkaZarzadajaca = pd.DataFrame(ogt4zpjl, columns=ddseyky8)
        self.df_EGB_WspolnotaGruntowa_podmiotUprawniony = pd.DataFrame(u5nkzy5m, columns=vwya6xa5)
        self.df_EGB_WspolnotaGruntowa_malzenstwoUprawnione = pd.DataFrame(r4568y9r, columns=oy40s2lf)
        self.df_EGB_WspolnotaGruntowa_osobaFizycznaUprawniona = pd.DataFrame(d5bu42df, columns=zhm3h6ic)
        return (self.df_EGB_WspolnotaGruntowa_nazwa, self.df_EGB_WspolnotaGruntowa_spolkaZarzadajaca, self.df_EGB_WspolnotaGruntowa_podmiotUprawniony, self.df_EGB_WspolnotaGruntowa_malzenstwoUprawnione, self.df_EGB_WspolnotaGruntowa_osobaFizycznaUprawniona)

    def _EGB_UdzialWeWlasnosci(self):
        columns = ['rodzajPrawa', 'udzialWlasnosci', 'podmiot', 'id-JRG']
        lxrskj21 = []
        im6cisib = {1: 'Własność', 2: 'Władanie samoistne'}
        for qra8zqzt in self.root.findall('gml:featureMember', self.namespaces):
            for fcjf5edc in qra8zqzt.findall('egb:EGB_UdzialWeWlasnosci', self.namespaces):
                d2nfp2pk = self._get_element_value(fcjf5edc, './/egb:rodzajPrawa')
                d2nfp2pk = im6cisib.get(int(d2nfp2pk), d2nfp2pk)
                iwgmqswd = self._get_element_value(fcjf5edc, './/egb:licznikUlamkaOkreslajacegoWartoscUdzialu')
                up0ns7v9 = self._get_element_value(fcjf5edc, './/egb:mianownikUlamkaOkreslajacegoWartoscUdzialu')
                i32f95iy = f'{iwgmqswd}/{up0ns7v9}'
                abro6azb = self._get_element_href(fcjf5edc, './/egb:podmiotUdzialuWlasnosci') or self._get_podmiot(fcjf5edc, './/egb:EGB_Podmiot')
                vl541tcw = self._get_element_href(fcjf5edc, './/egb:przedmiotUdzialuWlasnosci') or self._get_element_href(fcjf5edc, './/egb:JRG')
                lxrskj21.append([d2nfp2pk, i32f95iy, abro6azb, vl541tcw])
        self.df_EGB_UdzialWeWlasnosci = pd.DataFrame(lxrskj21, columns=columns)
        return self.df_EGB_UdzialWeWlasnosci

    def _EGB_UdzialWeWladaniu(self):
        columns = ['rodzajWladania', 'udzialWladania', 'podmiot', 'id-JRG']
        lxrskj21 = []
        x13fv0gl = {'1': 'uzytkowanieWieczyste', '2': 'trwalyZarzad', '3': 'zarzad', '4': 'uzytkowanie', '5': 'innyRodzajWladania', '6': 'wykonywaniePrawaWlasnosciSPIInnychPrawRzeczowych', '7': 'gospodarowanieZasobemNieruchomosciSPLubGmPowWoj', '8': 'gospodarowanieGruntemSPPokrytymWodamiPowierzchniowymi', '9': 'wykonywanieZadanZarzadcyDrogPub'}
        for qra8zqzt in self.root.findall('gml:featureMember', self.namespaces):
            for fcjf5edc in qra8zqzt.findall('egb:EGB_UdzialWeWladaniu', self.namespaces):
                f245dlz7 = self._get_element_value(fcjf5edc, './/egb:rodzajWladania')
                f245dlz7 = x13fv0gl.get(f245dlz7, f245dlz7)
                fyel7dwt = self._get_element_value(fcjf5edc, './/egb:licznikUlamkaOkreslajacegoWartoscUdzialu')
                g0ug6x4o = self._get_element_value(fcjf5edc, './/egb:mianownikUlamkaOkreslajacegoWartoscUdzialu')
                oe5h7zxs = f'{fyel7dwt}/{g0ug6x4o}'
                abro6azb = self._get_element_href(fcjf5edc, './/egb:podmiotUdzialuWeWladaniu') or self._get_podmiot(fcjf5edc, './/egb:EGB_Podmiot')
                vl541tcw = self._get_element_href(fcjf5edc, './/egb:przedmiotUdzialuWladania') or self._get_element_href(fcjf5edc, './/egb:JRG')
                lxrskj21.append([f245dlz7, oe5h7zxs, abro6azb, vl541tcw])
        self.df_EGB_UdzialWeWladaniu = pd.DataFrame(lxrskj21, columns=columns)
        return self.df_EGB_UdzialWeWladaniu

    def _EGB_AdresPodmiotu(self):
        columns = ['AdresPodmiotu', 'kraj', 'miejscowosc', 'kodPocztowy', 'ulica', 'numerPorzadkowy', 'numerLokalu']
        lxrskj21 = []
        for qra8zqzt in self.root.findall('gml:featureMember', self.namespaces):
            for bl1i55rz in qra8zqzt.findall('egb:EGB_AdresPodmiotu', self.namespaces) or qra8zqzt.findall('egb:EGB_AdresZameldowania', self.namespaces):
                id = bl1i55rz.attrib.get('{http://www.opengis.net/gml/3.2}id')
                tjadu7zn = self._get_element_value(bl1i55rz, 'egb:kraj')
                ru2qqq4u = self._get_element_value(bl1i55rz, 'egb:miejscowosc')
                ps0ik76q = self._get_element_value(bl1i55rz, 'egb:kodPocztowy')
                ya4ke6g2 = self._get_element_value(bl1i55rz, 'egb:ulica')
                bqvuo33n = self._get_element_value(bl1i55rz, 'egb:numerPorzadkowy')
                ahqoqg0g = self._get_element_value(bl1i55rz, 'egb:numerLokalu')
                lxrskj21.append([id, tjadu7zn, ru2qqq4u, ps0ik76q, ya4ke6g2, bqvuo33n, ahqoqg0g])
        self.df_EGB_AdresPodmiotu = pd.DataFrame(lxrskj21, columns=columns)
        return self.df_EGB_AdresPodmiotu

    def _EGB_AdresNieruchomosci(self):
        columns = ['id', 'nazwaMiejscowosci', 'idMiejscowosci', 'nazwaUlicy', 'idNazwyUlicy', 'numerPorzadkowy', 'numerLokalu', 'geometria']
        lxrskj21 = []
        for qra8zqzt in self.root.findall('gml:featureMember', self.namespaces):
            for bl1i55rz in qra8zqzt.findall('egb:EGB_AdresNieruchomosci', self.namespaces):
                id = bl1i55rz.attrib.get('{http://www.opengis.net/gml/3.2}id')
                xe28unk3 = self._get_element_value(bl1i55rz, 'egb:nazwaMiejscowosci')
                ye6d36bc = self._get_element_value(bl1i55rz, 'egb:idMiejscowosci')
                y2789evt = self._get_element_value(bl1i55rz, 'egb:nazwaUlicy')
                ocrr114c = self._get_element_value(bl1i55rz, 'egb:idNazwyUlicy')
                bqvuo33n = self._get_element_value(bl1i55rz, 'egb:numerPorzadkowy')
                ahqoqg0g = self._get_element_value(bl1i55rz, 'egb:numerLokalu')
                k0yevzyb = self._get_element_value(bl1i55rz, './/gml:pos', pos=True)
                lxrskj21.append([id, xe28unk3, ye6d36bc, y2789evt, ocrr114c, bqvuo33n, ahqoqg0g, k0yevzyb])
        self.df_EGB_AdresNieruchomosci = pd.DataFrame(lxrskj21, columns=columns)
        return self.df_EGB_AdresNieruchomosci

    def _EGB_PunktGraniczny(self):
        columns = ['id', 'koniecWersjaObiekt', 'geometria', 'idPunktu', 'sposobPozyskania', 'spelnienieWarunkowDokl', 'rodzajStabilizacji', 'oznWMaterialeZrodlowym', 'numerOperatuTechnicznego', 'dodatkoweInformacje']
        lxrskj21 = []
        for qra8zqzt in self.root.findall('gml:featureMember', self.namespaces):
            for jart3ibw in qra8zqzt.findall('egb:EGB_PunktGraniczny', self.namespaces):
                id = jart3ibw.attrib.get('{http://www.opengis.net/gml/3.2}id')
                npx7af4e = self._get_element_value(jart3ibw, './/egb:koniecWersjaObiekt')
                k0yevzyb = self._get_element_value(jart3ibw, './/gml:pos', pos=True)
                g7pwu8dt = self._get_element_value(jart3ibw, './/egb:idPunktu')
                nivz81ur = self._get_element_value(jart3ibw, './/egb:sposobPozyskania')
                ilmdgzvt = self._get_element_value(jart3ibw, './/egb:spelnienieWarunkowDokl')
                avf2rq89 = self._get_element_value(jart3ibw, './/egb:rodzajStabilizacji')
                z0wx96ts = self._get_element_value(jart3ibw, './/egb:oznWMaterialeZrodlowym')
                dern707d = self._get_element_value(jart3ibw, './/egb:numerOperatuTechnicznego')
                p1x0fc0j = self._get_element_value(jart3ibw, './/egb:dodatkoweInformacje')
                lxrskj21.append([id, npx7af4e, k0yevzyb, g7pwu8dt, nivz81ur, ilmdgzvt, avf2rq89, z0wx96ts, dern707d, p1x0fc0j])
        self.df_EGB_PunktGraniczny = pd.DataFrame(lxrskj21, columns=columns)
        return self.df_EGB_PunktGraniczny

    def _EGB_Budynek(self):
        columns = ['id', 'idBudynku', 'koniecWersjaObiekt', 'rodzajWgKST', 'liczbaKondygnacjiNadziemnych', 'liczbaKondygnacjiPodziemnych', 'powZabudowy', 'lacznaPowUzytkowaLokaliWyodrebnionych', 'lacznaPowUzytkowaLokaliNiewyodrebnionych', 'lacznaPowUzytkowaPomieszczenPrzynaleznych', 'dokumentWlasnosci', 'dodatkoweInformacje', 'dzialkaZabudowana', 'adresBudynku', 'geometria']
        lxrskj21 = []
        for qra8zqzt in self.root.findall('gml:featureMember', self.namespaces):
            for b38yyfq5 in qra8zqzt.findall('egb:EGB_Budynek', self.namespaces):
                pisapeu0 = b38yyfq5.attrib.get('{http://www.opengis.net/gml/3.2}id')
                iy1oy6bl = self._get_element_value(b38yyfq5, './/egb:idBudynku')
                npx7af4e = self._get_element_value(b38yyfq5, './/egb:koniecWersjaObiekt')
                k0yevzyb = self._get_element_value(b38yyfq5, './/gml:posList', coordinates=True)
                if not k0yevzyb:
                    try:
                        k0yevzyb = self._get_element_value(b38yyfq5, './/gml:pos', coordinates=True)
                    except Exception as e:
                        logging.exception(e)
                        print(e)
                        k0yevzyb = []
                hd2x9ur4 = self._get_element_value(b38yyfq5, './/egb:rodzajWgKST')
                ll3j2n2f = self._get_element_value(b38yyfq5, './/egb:liczbaKondygnacjiNadziemnych')
                wr0t6yo0 = self._get_element_value(b38yyfq5, './/egb:liczbaKondygnacjiPodziemnych')
                o951k734 = self._get_element_value(b38yyfq5, './/egb:powZabudowy')
                ukg130q4 = self._get_element_value(b38yyfq5, './/egb:lacznaPowUzytkowaLokaliWyodrebnionych')
                es47c7oq = self._get_element_value(b38yyfq5, './/egb:lacznaPowUzytkowaLokaliNiewyodrebnionych')
                r6eudl79 = self._get_element_value(b38yyfq5, './/egb:lacznaPowUzytkowaPomieszczenPrzynaleznych')
                y3ji76jo = self._get_element_value(b38yyfq5, './/egb:dokumentWlasnosci')
                p1x0fc0j = self._get_element_value(b38yyfq5, './/egb:dodatkoweInformacje')
                s70tyh01 = self._get_element_href(b38yyfq5, './/egb:dzialkaZabudowana')
                lilluaag = self._get_element_href(b38yyfq5, './/egb:adresBudynku')
                lxrskj21.append([pisapeu0, iy1oy6bl, npx7af4e, hd2x9ur4, ll3j2n2f, wr0t6yo0, o951k734, ukg130q4, es47c7oq, r6eudl79, y3ji76jo, p1x0fc0j, s70tyh01, lilluaag, k0yevzyb])
        self.df_EGB_Budynek = pd.DataFrame(lxrskj21, columns=columns)
        return self.df_EGB_Budynek

    def _EGB_DzialkaEwidencyjna(self):
        columns = ['id', 'idDzialki', 'podstawaUtworzeniaWersjiObiektu', 'koniecWersjaObiekt', 'numerKW', 'geometria', 'poleEwidencyjne', 'dokladnoscReprezentacjiPola', 'id-JRG', 'adresDzialki', 'punktGranicyDzialki', 'klasouzytek', 'dokument2', 'operatTechniczny2']
        lxrskj21 = []
        for qra8zqzt in self.root.findall('gml:featureMember', self.namespaces):
            for z86iq6jl in qra8zqzt.findall('egb:EGB_DzialkaEwidencyjna', self.namespaces):
                pisapeu0 = z86iq6jl.attrib.get('{http://www.opengis.net/gml/3.2}id')
                v8u7h8on = self._get_element_value(z86iq6jl, './/egb:idDzialki')
                z5uyo10e = self._get_element_href(z86iq6jl, './/egb:podstawaUtworzeniaWersjiObiektu')
                npx7af4e = self._get_element_value(z86iq6jl, './/egb:koniecWersjaObiekt')
                if npx7af4e:
                    v8u7h8on = str(v8u7h8on) + '*'
                ltrslvvf = self._get_element_value(z86iq6jl, './/egb:numerKW')
                y3ji76jo = self._get_element_value(z86iq6jl, './/egb:dokumentWlasnosci')
                if not ltrslvvf:
                    ltrslvvf = y3ji76jo
                k0yevzyb = self._get_element_value(z86iq6jl, './/gml:posList', coordinates=True)
                if not k0yevzyb:
                    try:
                        k0yevzyb = self._get_element_value(z86iq6jl, './/gml:pos', coordinates=True)
                    except Exception as e:
                        logging.exception(e)
                        print(e)
                        k0yevzyb = []
                y4an484x = self._get_element_value(z86iq6jl, './/egb:poleEwidencyjne')
                togkso6a = self._get_element_value(z86iq6jl, './/egb:dokladnoscReprezentacjiPola')
                if togkso6a == '1':
                    togkso6a = 'M'
                elif togkso6a == '2':
                    togkso6a = 'Ara'
                vl541tcw = self._get_element_href(z86iq6jl, './/egb:JRG2')
                c6w49ued = self._get_element_href_list(z86iq6jl, './/egb:punktGranicyDzialki')
                gu016s8p = self._get_element_href_list(z86iq6jl, './/egb:adresDzialki')
                ma118u8z = self._get_element_klasouzytek_list(z86iq6jl, './/egb:klasouzytek')
                z3jdlbsk = self._get_element_href_list(z86iq6jl, './/egb:dokument2') or self._get_element_href_list(z86iq6jl, './/egb:dokument1')
                pbny2gfx = self._get_element_href_list(z86iq6jl, './/egb:operatTechniczny2') or self._get_element_href_list(z86iq6jl, './/egb:operatTechniczny1')
                lxrskj21.append([pisapeu0, v8u7h8on, z5uyo10e, npx7af4e, ltrslvvf, k0yevzyb, y4an484x, togkso6a, vl541tcw, gu016s8p, c6w49ued, ma118u8z, z3jdlbsk, pbny2gfx])
        self.df_EGB_DzialkaEwidencyjna = pd.DataFrame(lxrskj21, columns=columns)
        return self.df_EGB_DzialkaEwidencyjna

    def _EGB_KonturUzytkuGruntowego(self):
        columns = ['id', 'idIIP', 'geometria', 'idUzytku', 'OFU', 'lokalizacjaUzytku']
        lxrskj21 = []
        for qra8zqzt in self.root.findall('gml:featureMember', self.namespaces):
            for z7vosfsd in qra8zqzt.findall('egb:EGB_KonturUzytkuGruntowego', self.namespaces):
                pisapeu0 = z7vosfsd.attrib.get('{http://www.opengis.net/gml/3.2}id')
                ddazp5dt = self._get_element_value(z7vosfsd, './/egb:idIIP')
                k0yevzyb = self._get_element_value(z7vosfsd, './/gml:posList', coordinates=True)
                if not k0yevzyb:
                    try:
                        k0yevzyb = self._get_element_value(z7vosfsd, './/gml:pos', coordinates=True)
                    except Exception as e:
                        logging.exception(e)
                        print(e)
                        k0yevzyb = []
                osyfg3ok = self._get_element_value(z7vosfsd, './/egb:idUzytku')
                efcd4e5e = self._get_element_value(z7vosfsd, './/egb:OFU')
                smsf0s5i = self._get_element_href(z7vosfsd, './/egb:lokalizacjaUzytku')
                lxrskj21.append([pisapeu0, ddazp5dt, k0yevzyb, osyfg3ok, efcd4e5e, smsf0s5i])
        self.df_EGB_KonturUzytkuGruntowego = pd.DataFrame(lxrskj21, columns=columns)
        return self.df_EGB_KonturUzytkuGruntowego

    def _EGB_KonturKlasyfikacyjny(self):
        columns = ['id', 'idIIP', 'geometria', 'idKonturu', 'OFU', 'OZU', 'OZK', 'lokalizacjaUzytku']
        lxrskj21 = []
        for qra8zqzt in self.root.findall('gml:featureMember', self.namespaces):
            for z7vosfsd in qra8zqzt.findall('egb:EGB_KonturKlasyfikacyjny', self.namespaces):
                pisapeu0 = z7vosfsd.attrib.get('{http://www.opengis.net/gml/3.2}id')
                ddazp5dt = self._get_element_value(z7vosfsd, './/egb:idIIP')
                k0yevzyb = self._get_element_value(z7vosfsd, './/gml:posList', coordinates=True)
                if not k0yevzyb:
                    try:
                        k0yevzyb = self._get_element_value(z7vosfsd, './/gml:pos', coordinates=True)
                    except Exception as e:
                        logging.exception(e)
                        print(e)
                        k0yevzyb = []
                xbgln2hu = self._get_element_value(z7vosfsd, './/egb:idKonturu')
                efcd4e5e = self._get_element_value(z7vosfsd, './/egb:OFU')
                yotyr8s1 = self._get_element_value(z7vosfsd, './/egb:OZU')
                zdqgq5x8 = self._get_element_value(z7vosfsd, './/egb:OZK')
                smsf0s5i = self._get_element_href(z7vosfsd, './/egb:lokalizacjaUzytku')
                lxrskj21.append([pisapeu0, ddazp5dt, k0yevzyb, xbgln2hu, efcd4e5e, yotyr8s1, zdqgq5x8, smsf0s5i])
        self.df_EGB_KonturKlasyfikacyjny = pd.DataFrame(lxrskj21, columns=columns)
        return self.df_EGB_KonturKlasyfikacyjny

    def _PrezentacjaGraficzna(self):
        columns = ['pos', 'katObrotu', 'justyfikacja', 'tekst', 'obiektPrzedstawiany']
        lxrskj21 = []
        for qra8zqzt in self.root.findall('gml:featureMember', self.namespaces):
            for ndadgb1x in qra8zqzt.findall('egb:PrezentacjaGraficzna', self.namespaces):
                k9odf36i = ('', '')
                k9odf36i = self._get_element_value(ndadgb1x, './/gml:pos', pos=True)
                k9fgy8n8 = self._get_element_value(ndadgb1x, './/egb:justyfikacja')
                foi6f8mv = self._get_element_value(ndadgb1x, './/egb:katObrotu')
                l8dkkwk1 = self._get_element_value(ndadgb1x, './/egb:tekst')
                ecbjf973 = self._get_element_href(ndadgb1x, './/egb:obiektPrzedstawiany')
                lxrskj21.append([k9odf36i, foi6f8mv, k9fgy8n8, l8dkkwk1, ecbjf973])
        self.df_PrezentacjaGraficzna = pd.DataFrame(lxrskj21, columns=columns)
        return self.df_PrezentacjaGraficzna

    def _EGB_Dokument(self):
        columns = ['id', 'startObiekt', 'koniecObiekt', 'tytul', 'dataDokumentu', 'nazwaTworcyDokumentu', 'opisDokumentu', 'rodzajDokumentu', 'sygnaturaDokumentu', 'oznKancelaryjneDokumentu', 'zasobSieciowy', 'zalaczniki']
        lxrskj21 = []
        for xkwc447g in self.root.findall('gml:featureMember', self.namespaces):
            for xvztejr9 in xkwc447g.findall('egb:EGB_Dokument', self.namespaces):
                yzb3687f = xvztejr9.attrib.get('{http://www.opengis.net/gml/3.2}id')
                fqikbrmj = self._get_element_value(xvztejr9, './/egb:startObiekt')
                evhw31k8 = self._get_element_value(xvztejr9, './/egb:koniecObiekt')
                hk67ow64 = self._get_element_value(xvztejr9, './/egb:tytul')
                rgn74dwq = self._get_element_value(xvztejr9, './/egb:dataDokumentu')
                wotas9fc = self._get_element_value(xvztejr9, './/egb:nazwaTworcyDokumentu')
                qy4cg7g8 = self._get_element_value(xvztejr9, './/egb:opisDokumentu')
                jnxd0p4h = self._get_element_value(xvztejr9, './/egb:rodzajDokumentu')
                dcqs44kz = self._get_element_value(xvztejr9, './/egb:sygnaturaDokumentu')
                rr6py3p6 = self._get_element_value(xvztejr9, './/egb:oznKancelaryjneDokumentu')
                ybgfdzd2 = []
                for jedka56q in xvztejr9.findall('.//egb:zasobSieciowy', self.namespaces):
                    o5j82ot5 = jedka56q.find('.//gmd:URL', self.namespaces)
                    if o5j82ot5 is not None and o5j82ot5.text:
                        ybgfdzd2.append(o5j82ot5.text.strip())
                ch9a42yo = []
                for z4n5ikz9 in xvztejr9.findall('.//egb:zalacznikDokumentu', self.namespaces):
                    pr6n2o5x = z4n5ikz9.attrib.get('{http://www.w3.org/1999/xlink}href')
                    if pr6n2o5x:
                        ch9a42yo.append(pr6n2o5x)
                lxrskj21.append([yzb3687f, fqikbrmj, evhw31k8, hk67ow64, rgn74dwq, wotas9fc, qy4cg7g8, jnxd0p4h, dcqs44kz, rr6py3p6, ybgfdzd2, ch9a42yo])
        self.df_EGB_Dokument = pd.DataFrame(lxrskj21, columns=columns)
        return self.df_EGB_Dokument

    def _EGB_OperatTechniczny(self):
        columns = ['id', 'startObiekt', 'koniecObiekt', 'dataPrzyjeciaDoPZGIK', 'dataSporzadzenia', 'identyfikatorOperatu', 'nazwaTworcy', 'opisOperatu', 'zasobSieciowy']
        lxrskj21 = []
        for xkwc447g in self.root.findall('gml:featureMember', self.namespaces):
            for prbestej in xkwc447g.findall('egb:EGB_OperatTechniczny', self.namespaces):
                yzb3687f = prbestej.attrib.get('{http://www.opengis.net/gml/3.2}id')
                fqikbrmj = self._get_element_value(prbestej, './/egb:startObiekt')
                evhw31k8 = self._get_element_value(prbestej, './/egb:koniecObiekt')
                wlay64ba = self._get_element_value(prbestej, './/egb:dataPrzyjeciaDoPZGIK')
                rcf50b2t = self._get_element_value(prbestej, './/egb:dataSporzadzenia')
                wgwwdggn = self._get_element_value(prbestej, './/egb:identyfikatorOperatuWgPZGIK')
                yekl5aj9 = self._get_element_value(prbestej, './/egb:nazwaTworcy')
                vogtwqqv = self._get_element_value(prbestej, './/egb:opisOperatu')
                o5j82ot5 = None
                jedka56q = prbestej.find('.//egb:zasobSieciowy', self.namespaces)
                if jedka56q is not None:
                    gg83g9vm = jedka56q.find('.//gmd:URL', self.namespaces)
                    if gg83g9vm is not None and gg83g9vm.text:
                        o5j82ot5 = gg83g9vm.text.strip()
                lxrskj21.append([yzb3687f, fqikbrmj, evhw31k8, wlay64ba, rcf50b2t, wgwwdggn, yekl5aj9, vogtwqqv, o5j82ot5])
        self.df_EGB_OperatTechniczny = pd.DataFrame(lxrskj21, columns=columns)
        return self.df_EGB_OperatTechniczny

    def _EGB_Zmiana(self):
        columns = ['id', 'startObiekt', 'koniecObiekt', 'dataAkceptacjiZmiany', 'dataPrzyjeciaZgloszeniaZmiany', 'nrZmiany', 'opisZmiany', 'dokument1', 'operatTechniczny1']
        lxrskj21 = []
        for xkwc447g in self.root.findall('gml:featureMember', self.namespaces):
            for xw825p5c in xkwc447g.findall('egb:EGB_Zmiana', self.namespaces):
                yzb3687f = xw825p5c.attrib.get('{http://www.opengis.net/gml/3.2}id')
                fqikbrmj = self._get_element_value(xw825p5c, './/egb:startObiekt')
                evhw31k8 = self._get_element_value(xw825p5c, './/egb:koniecObiekt')
                ouq3drfq = self._get_element_value(xw825p5c, './/egb:dataAkceptacjiZmiany')
                wlay64ba = self._get_element_value(xw825p5c, './/egb:dataPrzyjeciaZgloszeniaZmiany')
                im3bp0dw = self._get_element_value(xw825p5c, './/egb:nrZmiany')
                p84ay5ce = self._get_element_value(xw825p5c, './/egb:opisZmiany')
                nrsvknn9 = []
                for rvdcxli3 in xw825p5c.findall('.//egb:dokument1', self.namespaces):
                    pr6n2o5x = rvdcxli3.attrib.get('{http://www.w3.org/1999/xlink}href')
                    if pr6n2o5x:
                        nrsvknn9.append(pr6n2o5x)
                a7zmixr6 = []
                for dq8iynfy in xw825p5c.findall('.//egb:operatTechniczny1', self.namespaces):
                    pr6n2o5x = dq8iynfy.attrib.get('{http://www.w3.org/1999/xlink}href')
                    if pr6n2o5x:
                        a7zmixr6.append(pr6n2o5x)
                lxrskj21.append([yzb3687f, fqikbrmj, evhw31k8, ouq3drfq, wlay64ba, im3bp0dw, p84ay5ce, nrsvknn9, a7zmixr6])
        self.df_EGB_Zmiana = pd.DataFrame(lxrskj21, columns=columns)
        return self.df_EGB_Zmiana

    def get_epsg_from_root(self):
        if self.root is None:
            return None
        t5ad51d9 = None
        for qra8zqzt in self.root:
            rydloy56 = qra8zqzt.find('.//*[@srsName]')
            if rydloy56 is not None:
                t5ad51d9 = rydloy56.attrib['srsName']
                break
        if t5ad51d9:
            self.epsg = t5ad51d9.lstrip('urn:ogc:def:crs:EPSG::')
        return self.epsg

    @staticmethod
    def fill_missing_values(main_df, *dfs, col='ID'):
        lqh0p28r = main_df.astype(str).copy()
        for df in dfs:
            if df.empty or col not in df.columns:
                continue
            df = df.astype(str)
            x33svo85 = lqh0p28r.columns.intersection(df.columns).tolist()
            if col in x33svo85:
                x33svo85.remove(col)
            khgg2kma = lqh0p28r.merge(df, on=col, how='left', suffixes=('', '_temp'))
            for gkznj6kc in x33svo85:
                if khgg2kma[f'{gkznj6kc}_temp'].notna().any():
                    khgg2kma[gkznj6kc] = khgg2kma[gkznj6kc].combine_first(khgg2kma[f'{gkznj6kc}_temp'])
            khgg2kma = khgg2kma.drop(columns=[f'{gkznj6kc}_temp' for gkznj6kc in x33svo85])
            lqh0p28r = khgg2kma
        return lqh0p28r

    @staticmethod
    def concat_dataframe(podmioty_dfs):
        try:
            wf4c03ut = [df for df in podmioty_dfs if isinstance(df, pd.DataFrame) and (not df.empty)]
            if wf4c03ut:
                daqiksjd = pd.concat(wf4c03ut, ignore_index=True)
                logging.info(f'EGIB_Podmioty successfully concatenated ({len(daqiksjd)} rows).')
                return daqiksjd
            else:
                logging.warning('No valid DataFrames to concatenate in EGIB_Podmioty.')
                return pd.DataFrame()
        except Exception as e:
            logging.exception('concat_dataframe() failed.')
            return pd.DataFrame()

    @staticmethod
    def merge_dataframe(main_df, *dfs, how='outer', on=None, left_on=None, right_on=None):
        lqh0p28r = main_df.copy()
        for df in dfs:
            if df.empty:
                continue
            df = df.astype(str).copy()
            x33svo85 = lqh0p28r.columns.intersection(df.columns).tolist()
            khgg2kma = lqh0p28r.merge(df, how=how, on=on, left_on=left_on, right_on=right_on, suffixes=('', '_temp'))
            for gkznj6kc in x33svo85:
                u3ost48o = f'{gkznj6kc}_temp'
                if u3ost48o in khgg2kma.columns and khgg2kma[u3ost48o].notna().any():
                    khgg2kma[gkznj6kc] = khgg2kma[gkznj6kc].combine_first(khgg2kma[u3ost48o])
            khgg2kma.drop(columns=[f'{gkznj6kc}_temp' for gkznj6kc in x33svo85 if f'{gkznj6kc}_temp' in khgg2kma.columns], inplace=True)
            lqh0p28r = khgg2kma
        return lqh0p28r

    @staticmethod
    def merge_dataframe_old(main_df, *dfs, how='outer', on=None, left_on=None, right_on=None):
        lqh0p28r = main_df.copy()
        for df in dfs:
            if df.empty:
                continue
            df = df.astype(str)
            df = df.copy()
            x33svo85 = lqh0p28r.columns.intersection(df.columns).tolist()
            khgg2kma = lqh0p28r.merge(df, how=how, on=on, left_on=left_on, right_on=right_on, suffixes=('', '_temp'))
            for gkznj6kc in x33svo85:
                if khgg2kma[f'{gkznj6kc}_temp'].notna().any():
                    khgg2kma[gkznj6kc] = khgg2kma[gkznj6kc].combine_first(khgg2kma[f'{gkznj6kc}_temp'])
            khgg2kma = khgg2kma.drop(columns=[f'{gkznj6kc}_temp' for gkznj6kc in x33svo85])
            lqh0p28r = khgg2kma
        return lqh0p28r

    @staticmethod
    def get_crs_epsg(path):
        vwp5n46s = ET.parse(path)
        root = vwp5n46s.getroot()
        t5ad51d9 = None
        for qra8zqzt in root:
            rydloy56 = qra8zqzt.find('.//*[@srsName]')
            if rydloy56 is not None:
                t5ad51d9 = rydloy56.attrib['srsName']
                break
        return t5ad51d9.lstrip('urn:ogc:def:crs:')

    @staticmethod
    def poprawka_pow(df, col, epsg):
        try:
            dncb3cs3 = df[col]
            o1kh9lbz = []
            lapv6mvo = []
            for id, jxmy5t72 in zip(df['idDzialki'], dncb3cs3):
                if isinstance(jxmy5t72, list) and all((isinstance(macar3eu, tuple) for macar3eu in jxmy5t72)):
                    try:
                        jxmy5t72 = Polygon(jxmy5t72)
                    except Exception as e:
                        logging.exception(e)
                        print(e)
                        continue
                    "\n                    if id == '2176':\n                        N = 5\n                    elif id == '2177':\n                        N = 6\n                    elif id == '2178':\n                        N = 7\n                    elif id == '2179':\n                        N = 8\n                    else:\n                        N = 6\n                    "
                    vkjr32l9 = {'2176': 5, '2177': 6, '2178': 7, '2179': 8}.get(epsg, 6)
                    ryn3s47z = jxmy5t72.area
                    ryn3s47z = ryn3s47z
                    area = ryn3s47z / 10000
                    f078rigi, awl2pit5 = jxmy5t72.exterior.coords.xy
                    coords = list(zip(f078rigi, awl2pit5))
                    mqymcg35 = sum(f078rigi) / len(f078rigi)
                    j1jp1o49 = sum(awl2pit5) / len(awl2pit5)
                    o1kh9lbz.append((mqymcg35, j1jp1o49))
                    pqhrkzi3 = 306.752873
                    rx8nr2dd = -0.312616
                    y8lw49wp = 0.006382
                    nj0gakup = 0.158591
                    ezn80gkd = -7.7
                    wezofoph = 0.999923
                    irknopjc = j1jp1o49
                    a93qx43q = mqymcg35
                    a3tuotmy = irknopjc / wezofoph
                    n38plboc = (a93qx43q - (vkjr32l9 * 1000000 + 500000)) / wezofoph
                    gg83g9vm = (a3tuotmy - 5800000.0) * 2.0 * 10 ** (-6)
                    mkenf042 = n38plboc * 2.0 * 10 ** (-6)
                    va0iue0k = ezn80gkd + wezofoph * mkenf042 ** 2 * (pqhrkzi3 + rx8nr2dd * gg83g9vm + y8lw49wp * gg83g9vm ** 2 + nj0gakup * mkenf042 ** 2)
                    s2qko52u = va0iue0k * 10 ** (-5) + 1
                    fnthk7sm = area * (s2qko52u ** 2 - 1)
                    tmvaciqp = ryn3s47z - fnthk7sm
                    tmvaciqp = '{:.4f}'.format(round(tmvaciqp / 10000, 4))
                    lapv6mvo.append(tmvaciqp)
            df['Obl. pow.'] = lapv6mvo
        except Exception as e:
            logging.exception(e)
            print(f'Wystąpił błąd podczas: {str(e)}')
            try:
                df['Obl. pow.'] = None
            except Exception as e:
                logging.exception(e)
                print(f'Wystąpił błąd podczas: {str(e)}')
        return df
if __name__ == '__main__':
    pass
    logging.basicConfig(level=logging.NOTSET, filename='log.log', filemode='w', format='%(asctime)s - %(lineno)d - %(levelname)s - %(message)s')
    path = 'C:\\Users\\Dominik\\Kopia\\OneDrive\\Baza\\Projekty\\454\\PZGIK.gml'
    nul8ead0 = time.perf_counter()
    try:
        c9z9vwrp = GMLParser(path)
        c9z9vwrp.initialize_gml_parse()
        c9z9vwrp.initialize_documents_data()
        print(c9z9vwrp.df_GML_documents)
        '\n        parser.initialize_additional_data()\n        print(parser.df_GML_points)\n        print(parser.df_GML_dzialki)\n        print(parser.df_GML_budynki)\n        print(parser.df_GML_points_in_dzialki)\n        '
    except Exception as e:
        logging.exception(e)
        print(e)
    mgc6t1pe = time.perf_counter()
    print('GML READ END! TIME: ', f'{mgc6t1pe - nul8ead0:.4}')