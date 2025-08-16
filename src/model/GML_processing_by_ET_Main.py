_As='.//*[@srsName]'
_Ar='.//egb:lokalizacjaUzytku'
_Aq='.//egb:idIIP'
_Ap='lokalizacjaUzytku'
_Ao='.//egb:dokumentWlasnosci'
_An='.//egb:koniecWersjaObiekt'
_Am='.//egb:dodatkoweInformacje'
_Al='egb:numerLokalu'
_Ak='egb:numerPorzadkowy'
_Aj='.//egb:JRG'
_Ai='.//egb:EGB_Podmiot'
_Ah='.//egb:mianownikUlamkaOkreslajacegoWartoscUdzialu'
_Ag='.//egb:licznikUlamkaOkreslajacegoWartoscUdzialu'
_Af='.//egb:adresSiedziby'
_Ae='.//egb:regon'
_Ad='.//egb:nazwaSkrocona'
_Ac='.//egb:nazwaPelna'
_Ab='.//egb:OZK'
_Aa='.//egb:OZU'
_AZ='obiektPrzedstawiany'
_AY='klasouzytek'
_AX='adresBudynku'
_AW='dzialkaZabudowana'
_AV='idNazwyUlicy'
_AU='nazwaUlicy'
_AT='idMiejscowosci'
_AS='nazwaMiejscowosci'
_AR='dokumentWlasnosci'
_AQ='lacznaPowUzytkowaPomieszczenPrzynaleznych'
_AP='lacznaPowUzytkowaLokaliNiewyodrebnionych'
_AO='lacznaPowUzytkowaLokaliWyodrebnionych'
_AN='powZabudowy'
_AM='podmiotUprawniony'
_AL='spolkaZarzadajaca'
_AK='osobaFizycznaUprawniona'
_AJ='osobaFizyczna'
_AI='adresStalegoPobytu'
_AH='adresZameldowania'
_AG='kodPocztowy'
_AF='miejscowosc'
_AE='informacjaOSmierci'
_AD='imieMatki'
_AC='drugiCzlonNazwiska'
_AB='pierwszyCzlonNazwiska'
_AA='drugieImie'
_A9='pierwszeImie'
_A8='udzialWladania'
_A7='rodzajWladania'
_A6='udzialWlasnosci'
_A5='rodzajPrawa'
_A4='points_in_dzialki'
_A3='sorted_dzialki'
_A2='graphic_data'
_A1='personal_data'
_A0='File not found: %s'
_z='XML parsing error: %s'
_y='_temp'
_x='koniecWersjaObiekt'
_w='{http://www.w3.org/1999/xlink}href'
_v='.//egb:OFU'
_u='liczbaKondygnacjiPodziemnych'
_t='liczbaKondygnacjiNadziemnych'
_s='rodzajWgKST'
_r='idBudynku'
_q='punktGranicyDzialki'
_p='numerOperatuTechnicznego'
_o='oznWMaterialeZrodlowym'
_n='rodzajStabilizacji'
_m='spelnienieWarunkowDokl'
_l='sposobPozyskania'
_k='idPunktu'
_j='instytucja'
_i='idJednostkiRejestrowej'
_h='grupaRejestrowa'
_g='nazwaSkrocona'
_f='start-ns'
_e='Obl. pow.'
_d='podmiot'
_c='adresSiedziby'
_b='AdresPodmiotu'
_a='numerLokalu'
_Z='numerPorzadkowy'
_Y='regon'
_X='nazwaPelna'
_W='dokladnoscReprezentacjiPola'
_V='.//egb:status'
_U='dodatkoweInformacje'
_T='poleEwidencyjne'
_S=False
_R='id-JRG'
_Q='numerKW'
_P='.//gml:posList'
_O='part1'
_N='status'
_M='outer'
_L='idDzialki'
_K='.'
_J='.//gml:pos'
_I='geometria'
_H='IDM'
_G='left'
_F='part2'
_E='{http://www.opengis.net/gml/3.2}id'
_D='gml:featureMember'
_C=True
_B='id'
_A=None
from shapely.geometry import Polygon
import xml.etree.ElementTree as ET
from pathlib import Path
import pandas as pd,logging,time
logger=logging.getLogger(__name__)
' Description\ngml = GMLParser(PATH)  # the function read root and namespace\ngml.initialize_gml_parse()  # initialize gml parsing and reading data\ndf_graphic_data[NAME] = gml.initialize_graphic_data()  # get df with graphic data\n#initialize_personal_data[NAME] = gml.initialize_personal_data()  # get df with initialize personal data\n\nhttps://www.gov.pl/web/gugik/schematy-aplikacyjne\n\n'
class GMLParser:
	def __init__(self,path=_A):
		self.path=path;self.df_GML_personal_data=pd.DataFrame();self.df_GML_graphic_data=pd.DataFrame();self.df_GML_sorted_działki=pd.DataFrame();self.df_GML_points_in_dzialki=pd.DataFrame();self.df_GML_budynki=pd.DataFrame();self.df_GML_dzialki=pd.DataFrame();self.df_GML_points=pd.DataFrame();self.df_GML_personal_raw_data=pd.DataFrame();self.df_PrezentacjaGraficzna=pd.DataFrame();self.df_OT_Ogrodzenia=pd.DataFrame();self.df_OT_Budowle=pd.DataFrame();self.df_OT_Skarpa=pd.DataFrame();self.df_OT_BudynekNiewykazanyWEGIB=pd.DataFrame();self.df_EGB_JednostkaRejestrowaGruntow=pd.DataFrame();self.df_EGB_KonturUzytkuGruntowego=pd.DataFrame();self.df_EGB_KonturKlasyfikacyjny=pd.DataFrame();self.df_EGB_PunktGraniczny=pd.DataFrame();self.df_EGB_OsobaFizyczna=pd.DataFrame();self.df_EGB_Malzenstwo=pd.DataFrame();self.df_EGB_Instytucja=pd.DataFrame();self.df_EGB_AdresPodmiotu=pd.DataFrame();self.df_EGB_UdzialWeWlasnosci=pd.DataFrame();self.df_EGB_UdzialWeWladaniu=pd.DataFrame();self.df_EGB_PodmiotGrupowy=pd.DataFrame();self.df_EGB_PodmiotGrupowy_nazwaPelna=pd.DataFrame();self.df_EGB_PodmiotGrupowy_instytucja=pd.DataFrame();self.df_EGB_PodmiotGrupowy_osobaFizyczna=pd.DataFrame();self.df_EGB_PodmiotGrupowy_malzenstwo=pd.DataFrame();self.df_EGB_WspolnotaGruntowa=pd.DataFrame();self.df_EGB_WspolnotaGruntowa_nazwa=pd.DataFrame();self.df_EGB_WspolnotaGruntowa_spolkaZarzadajaca=pd.DataFrame();self.df_EGB_WspolnotaGruntowa_podmiotUprawniony=pd.DataFrame();self.df_EGB_WspolnotaGruntowa_malzenstwoUprawnione=pd.DataFrame();self.df_EGB_WspolnotaGruntowa_osobaFizycznaUprawniona=pd.DataFrame();self.df_EGB_DzialkaEwidencyjna=pd.DataFrame();self.df_EGB_Budynek=pd.DataFrame();self.df_EGB_AdresNieruchomosci=pd.DataFrame();self.epsg=_A;self.root=_A;self.default_namespaces={'gml':'http://www.opengis.net/gml/3.2','egb':'ewidencjaGruntowIBudynkow:1.0','xlink':'http://www.w3.org/1999/xlink','ges2021':'geodezyjnaEwidencjaSieciUzbrojeniaTerenu:1.0','ot2021':'bazaDanychObiektowTopograficznych500:1.0'}
		if self.path and Path(self.path).exists():self.get_namespaces_and_root();self.get_epsg_from_root()
		else:return
	def get_namespaces_and_root(self):
		'Parse the GML file, extract root and namespaces.';A='start'
		try:
			namespaces={};context=ET.iterparse(self.path,events=(A,_f))
			for(event,elem)in context:
				if event==_f:prefix,uri=elem;namespaces[prefix]=uri
				elif event==A and self.root is _A:self.root=elem
			self.namespaces=namespaces;self._ensure_required_namespaces()
		except ET.ParseError as e:logger.exception(_z,e)
		except FileNotFoundError:logger.exception(_A0,self.path)
	def _ensure_required_namespaces(self):
		'Ensures all required namespaces are present.'
		for(prefix,uri)in self.default_namespaces.items():
			if prefix not in self.namespaces:self.namespaces[prefix]=uri
	def get_root(self):
		try:tree=ET.parse(self.path);return tree.getroot()
		except ET.ParseError as e:logger.exception(_z,e);return
		except FileNotFoundError:logger.exception(_A0,self.path);return
	def detect_namespaces(self):
		if self.root is _A:return{}
		namespaces={}
		for(_,elem)in ET.iterparse(self.path,events=[_f]):prefix,uri=elem;namespaces[prefix]=uri
		return namespaces
	def restory_dataframes(self,df_dict):self.df_GML_personal_data=df_dict.get(_A1);self.df_GML_graphic_data=df_dict.get(_A2);self.df_GML_sorted_działki=df_dict.get(_A3);self.df_GML_points_in_dzialki=df_dict.get(_A4);self.df_GML_budynki=df_dict.get('budynki');self.df_GML_dzialki=df_dict.get('działki');self.df_GML_points=df_dict.get('points');self.epsg=df_dict.get('epsg')
	def story_dataframes(self):return{_A1:self.df_GML_personal_data,_A2:self.df_GML_graphic_data,_A3:self.df_GML_sorted_działki,_A4:self.df_GML_points_in_dzialki,'budynki':self.df_GML_budynki,'działki':self.df_GML_dzialki,'points':self.df_GML_points,'epsg':self.epsg}
	def initialize_gml_parse(self):
		if self.root is _A:return
		self._PrezentacjaGraficzna();self._OT_Ogrodzenia();self._OT_Budowle();self._OT_Skarpa();self._OT_BudynekNiewykazanyWEGIB();self._EGB_JednostkaRejestrowaGruntow();self._EGB_Malzenstwo();self._EGB_Instytucja();self._EGB_PodmiotGrupowy();self._EGB_WspolnotaGruntowa();self._EGB_OsobaFizyczna();self._EGB_KonturUzytkuGruntowego();self._EGB_KonturKlasyfikacyjny();self._EGB_UdzialWeWlasnosci();self._EGB_UdzialWeWladaniu();self._EGB_AdresPodmiotu();self._EGB_AdresNieruchomosci();self._EGB_PunktGraniczny();self._EGB_DzialkaEwidencyjna();self._EGB_Budynek();logging.debug('GML Parser - Initialize END.')
	def initialize_graphic_data(self):
		if self.root is _A:return
		dataframes_to_merge=[('df_OT_Ogrodzenia',self.df_OT_Ogrodzenia),('df_OT_Budowle',self.df_OT_Budowle),('df_OT_Skarpa',self.df_OT_Skarpa),('df_EGB_KonturUzytkuGruntowego',self.df_EGB_KonturUzytkuGruntowego),('df_EGB_KonturKlasyfikacyjny',self.df_EGB_KonturKlasyfikacyjny),('df_EGB_PunktGraniczny',self.df_EGB_PunktGraniczny),('df_EGB_DzialkaEwidencyjna',self.df_EGB_DzialkaEwidencyjna),('df_EGB_Budynek',self.df_EGB_Budynek),('df_OT_BudynekNiewykazanyWEGIB',self.df_OT_BudynekNiewykazanyWEGIB),('df_EGB_AdresNieruchomosci',self.df_EGB_AdresNieruchomosci)];self.merged_dfs={}
		for(name,df)in dataframes_to_merge:self.merged_dfs[name]=self.merge_df_by_PrezentacjaGraficzna(df,name)
		logging.debug('GML Parser - Merging graphic GML data completed.');self.df_GML_graphic_data=self.merged_dfs;return self.merged_dfs
	def initialize_personal_data(self):
		if self.root is _A:return
		default_columns=[_L,_Q,_T,_W,_A5,_A6,_A7,_A8,_X,_g,_A9,_AA,_AB,_AC,'imieOjca',_AD,'plec','pesel',_Y,_AE,_H,_N,'kraj',_AF,_AG,'ulica',_Z,_a,'kraj_Kores.','miejscowosc_Kores.','kodPocztowy_Kores.','ulica_Kores.','numerPorzadkowy_Kores.','numerLokalu_Kores.',_h,_i];df_GML_personal_data=pd.DataFrame(columns=default_columns);df_GML_sorted_działki=pd.DataFrame();sort_dz_column=[_L,_Q,_T]
		try:df_sort_by=[_O,_F];df_GML_sorted_działki=self.sort_df(self.df_EGB_DzialkaEwidencyjna,sort_by_columns=df_sort_by,on_columns=sort_dz_column)
		except Exception as e:df_GML_sorted_działki=self.df_EGB_DzialkaEwidencyjna[sort_dz_column];logging.exception(e);print(e)
		try:df_GML_Dz_Ewid=pd.merge(self.df_EGB_DzialkaEwidencyjna,self.df_EGB_JednostkaRejestrowaGruntow,how=_M,on=_R)
		except Exception as e:df_GML_personal_raw_data=df_GML_Dz_Ewid;logging.exception(e);print(e)
		try:
			df_GML_udziały=pd.merge(self.df_EGB_UdzialWeWladaniu,self.df_EGB_UdzialWeWlasnosci,how=_M);df_GML_Dz_Ewid_udziały=pd.merge(df_GML_Dz_Ewid,df_GML_udziały,how=_M,on=_R);df_GML_podmioty=pd.DataFrame();df_GML_podmioty=pd.merge(self.df_EGB_OsobaFizyczna,self.df_EGB_Instytucja,how=_M);df_GML_podmioty=pd.merge(df_GML_podmioty,self.df_EGB_PodmiotGrupowy_nazwaPelna,how=_M);df_GML_podmioty=pd.merge(df_GML_podmioty,self.df_EGB_WspolnotaGruntowa_nazwa,how=_M);df_GML_podmioty=pd.merge(df_GML_podmioty,self.df_EGB_AdresPodmiotu,how=_G,left_on=_AH,right_on=_b);df_GML_podmioty=pd.merge(df_GML_podmioty,self.df_EGB_AdresPodmiotu,how=_G,left_on=_AI,right_on=_b,suffixes=('','_Kores.'));df_GML_podmioty=self.merge_dataframe(df_GML_podmioty,self.df_EGB_AdresPodmiotu,how=_G,left_on=_c,right_on=_b);df_GML_Malzenstwo=self.merge_dataframe(self.df_EGB_Malzenstwo,df_GML_podmioty,how=_G,left_on=_H,right_on=_B)
			try:df_GML_PodmiotGrupowy_osobaFizyczna=self.merge_dataframe(self.df_EGB_PodmiotGrupowy_osobaFizyczna,df_GML_podmioty,how=_G,left_on=_AJ,right_on=_B);df_GML_PodmiotGrupowy_instytucja=self.merge_dataframe(self.df_EGB_PodmiotGrupowy_instytucja[[_B,_Y,_N,_c,_j]],df_GML_podmioty,how=_G,left_on=_j,right_on=_B);df_GML_PodmiotGrupowy_malzenstwo=self.merge_dataframe(self.df_EGB_PodmiotGrupowy_malzenstwo,df_GML_Malzenstwo,how=_G,left_on=_H,right_on=_B)
			except Exception as e:logging.exception(e);logging.error('GML_Parser - PodmiotGrupowy error on dataframe merge');print(e)
			try:df_GML_WspolnotaGruntowa_osobaFizycznaUprawniona=self.merge_dataframe(self.df_EGB_WspolnotaGruntowa_osobaFizycznaUprawniona,df_GML_podmioty,how=_G,left_on=_AK,right_on=_B);df_GML_WspolnotaGruntowa_spolkaZarzadajaca=self.merge_dataframe(self.df_EGB_WspolnotaGruntowa_spolkaZarzadajaca,df_GML_podmioty,how=_G,left_on=_AL,right_on=_B);df_GML_WspolnotaGruntowa_podmiotUprawniony=self.merge_dataframe(self.df_EGB_WspolnotaGruntowa_podmiotUprawniony,df_GML_podmioty,how=_G,left_on=_AM,right_on=_B);df_GML_WspolnotaGruntowa_malzenstwoUprawnione=self.merge_dataframe(self.df_EGB_WspolnotaGruntowa_malzenstwoUprawnione,df_GML_Malzenstwo,how=_G,left_on=_H,right_on=_B)
			except Exception as e:logging.exception(e);logging.error('GML_Parser - WspolnotaGruntowa error on dataframe merge');print(e)
			podmioty_dfs=[df_GML_podmioty,df_GML_Malzenstwo,locals().get('df_GML_PodmiotGrupowy_osobaFizyczna'),locals().get('df_GML_PodmiotGrupowy_malzenstwo'),locals().get('df_GML_PodmiotGrupowy_instytucja'),locals().get('df_GML_WspolnotaGruntowa_osobaFizycznaUprawniona'),locals().get('df_GML_WspolnotaGruntowa_spolkaZarzadajaca'),locals().get('df_GML_WspolnotaGruntowa_podmiotUprawniony'),locals().get('df_GML_WspolnotaGruntowa_malzenstwoUprawnione')];df_GML_podmioty_concated=self.concat_dataframe(podmioty_dfs);df_GML_personal_raw_data=self.merge_dataframe(df_GML_Dz_Ewid_udziały,df_GML_podmioty_concated,how=_G,left_on=_d,right_on=_B)
		except Exception as e:logging.exception(e);print(e)
		try:df_GML_personal_raw_data[_H]=self.fill_data_in_col(df_GML_personal_raw_data,main_col=_H,fill_col=_d);df_GML_personal_raw_data[_H]=df_GML_personal_raw_data[_H].astype(str).str.slice(start=19,stop=26)
		except Exception as e:logging.exception(e);print(e)
		try:df_sort_by=[_O,_F,_H,'Właściciele'];df_GML_personal_raw_data=self.sort_df(df_GML_personal_raw_data,df_sort_by)
		except Exception as e:logging.exception(e);print(e)
		try:
			for col in default_columns:
				if col not in df_GML_personal_raw_data.columns:df_GML_personal_raw_data[col]=_A
			df_GML_personal_data=df_GML_personal_raw_data[default_columns]
		except Exception as e:logging.exception(e);print(e)
		try:df_GML_personal_data=df_GML_personal_data.replace(['NaN','None','nan'],'').fillna('')
		except Exception as e:logging.exception(e);print(e)
		self.df_GML_personal_data=df_GML_personal_data;self.df_GML_personal_raw_data=df_GML_personal_raw_data;self.df_GML_sorted_działki=df_GML_sorted_działki;logging.debug('GML Parser - Merging personal GML data completed.');return self.df_GML_personal_data,self.df_GML_sorted_działki
	def initialize_additional_data(self):
		A='_Dz'
		if self.root is _A:return
		points_in_plots_default_col=[_L,_Q,_k,_l,_m,_n,_o,_p,_U,_T,_W,'geometria_punkt']
		try:df_points=self.df_EGB_PunktGraniczny.copy();df_plots=self.df_EGB_DzialkaEwidencyjna.copy();df_plots=df_plots.explode(_q);df_merge=pd.merge(df_points,df_plots,how=_G,left_on=_B,right_on=_q,suffixes=('_punkt',A));self.df_GML_points_in_dzialki=df_merge[points_in_plots_default_col]
		except Exception as e:self.df_GML_points_in_dzialki=pd.DataFrame(columns=points_in_plots_default_col);logging.exception(e);print(e)
		bud_default_col=[_L,_Q,_r,_s,_t,_u,_AN,_AO,_AP,_AQ,_AR,_U,_AS,_AT,_AU,_AV,_Z,_a]
		try:df_Budynki=self.df_EGB_Budynek.copy();df_BudynekNiewykazanyWEGIB=self.df_OT_BudynekNiewykazanyWEGIB.copy();df_Budynki=pd.concat([df_Budynki,df_BudynekNiewykazanyWEGIB],ignore_index=_C);df_AdresNieruchomosci=self.df_EGB_AdresNieruchomosci.copy();df_Budynki=pd.merge(df_Budynki,self.df_EGB_DzialkaEwidencyjna,how=_G,left_on=_AW,right_on=_B,suffixes=('_Bud',A));df_Budynki=pd.merge(df_Budynki,df_AdresNieruchomosci,how=_G,left_on=_AX,right_on=_B);self.df_GML_budynki=self.restore_df_columns(df_Budynki,bud_default_col)
		except Exception as e:self.df_GML_budynki=pd.DataFrame(columns=bud_default_col);logging.exception(e);print(e)
		plots_default_col=[_L,_Q,_T,_W,_e,_AY,_h,_i]
		try:df_dzialki=self.df_EGB_DzialkaEwidencyjna.copy();df_jedn=self.df_EGB_JednostkaRejestrowaGruntow.copy();df_dzialki=pd.merge(df_dzialki,df_jedn,how=_M,on=_R);df_dzialki[_e]=_A;df_dzialki=self.poprawka_pow(df_dzialki,_I,self.epsg);df_dzialki=self.restore_df_columns(df_dzialki,plots_default_col);self.df_GML_dzialki=df_dzialki[plots_default_col]
		except Exception as e:self.df_GML_dzialki=pd.DataFrame(columns=plots_default_col);logging.exception(e);print(e)
		points_default_col=[_k,_I,_l,_m,_n,_o,_p,_U]
		try:df_PunktGraniczny=self.df_EGB_PunktGraniczny.copy();self.df_GML_points=df_PunktGraniczny[points_default_col]
		except Exception as e:self.df_GML_points=pd.DataFrame(columns=points_default_col);logging.exception(e);print(e)
		logging.debug('GML Parser - Merging additional GML data completed.')
	def replace_None_values(self,df):
		df=df.copy()
		try:0
		except Exception as e:logging.exception(e);print(e)
		"\n        for col in columns:\n            if col in df.columns:\n                df[col] = df[col].replace([None, 'None', 'NaN', 'nan'], '')\n        ";return df
	def restore_df_columns(self,df,default_columns):
		try:
			df=df.copy()
			for col in default_columns:
				if col not in df.columns:df[col]=_A
			df=df[default_columns]
		except Exception as e:logging.exception(e);print(e)
		return df
	def merge_df_by_PrezentacjaGraficzna(self,df,name=_A):
		if df.empty:return df
		else:
			try:df=pd.merge(self.df_PrezentacjaGraficzna,df,how='right',left_on=_AZ,right_on=_B)
			except Exception as e:logging.exception(e);logging.error(name);print(e)
		return df
	def sort_df(self,df,sort_by_columns,on_columns=_A):
		if on_columns:df_copy=df[on_columns].copy()
		else:df_copy=df.copy()
		df_copy[[_O,_F]]=df_copy[_L].str.rsplit(_K,n=1,expand=_C);df_copy[_F]=df_copy[_F].str.replace('/',_K);df_copy[_F]=df_copy[_F].astype(float);sort_columns=[_O,_F]+[col for col in sort_by_columns if col in df_copy.columns];df_copy=df_copy.sort_values(sort_columns);return df_copy.drop(columns=[_O,_F])
	def sort_df_OLD(self,df):df=df[[_L,_Q,_T]];df_copy=df.copy();df_copy[[_O,_F]]=df_copy[_L].str.rsplit(_K,n=1,expand=_C);df_copy[_F]=df_copy[_F].str.replace('/',_K);df_copy[_F]=df_copy[_F].astype(float);df_copy=df_copy.sort_values([_O,_F]);sorted_parcels=df_copy.drop(columns=[_O,_F]);return sorted_parcels
	def merge_col(self,df,col1,col2):df[col1]=df[col2].fillna(df[col1]);return df
	def fill_data_in_col(self,df,main_col,fill_col):
		try:df=df.copy();df[main_col]=df[main_col].replace('',_A);df[main_col]=df[main_col].replace('nan',_A);df[main_col]=df[main_col].where(df[main_col].isna(),df[fill_col])
		except Exception as e:logging.exception(e);print(e)
		return df[main_col]
	def _get_element_value(self,element,element_path,pos=_S,coordinates=_S,lista=_S):
		try:
			found_elements=element.findall(element_path,self.namespaces)
			if not found_elements:return
			coordinates_list=[]
			for found_element in found_elements:
				if found_element is not _A and found_element.text:
					text=found_element.text.strip()
					if pos:x,y=map(float,text.split());return round(x,2),round(y,2)
					elif coordinates:
						coords=[float(coord)for coord in text.split()];grouped_coords=[(coords[i],coords[i+1])for i in range(0,len(coords),2)]
						if lista:coordinates_list.append(grouped_coords)
						else:coordinates_list.extend(grouped_coords)
					else:return text
			return coordinates_list if coordinates_list else _A
		except Exception as e:logger.exception('Error extracting element value: %s',e);return
	def _get_element_klasouzytek_list(self,element,element_path):
		'Extracts a list of Klasoużytek values from the XML element.'
		try:
			found_elements=element.findall(element_path,self.namespaces);klasouzytek_list=[]
			for klasouzytek in found_elements:OFU=self._get_element_value(klasouzytek,_v);OZU=self._get_element_value(klasouzytek,_Aa);OZK=self._get_element_value(klasouzytek,_Ab);powierzchnia=self._get_element_value(klasouzytek,'.//egb:powierzchnia');klasouzytek_list.append([OFU,OZU,OZK,powierzchnia])
			return klasouzytek_list
		except Exception as e:logger.exception('Błąd podczas pobierania listy Klasoużytek: %s',e);return[]
	def _get_element_href_list(self,element,element_path):
		'Pobiera listę wartości atrybutów xlink:href dla EGB_PodmiotGrupowy.'
		try:found_elements=element.findall(element_path,self.namespaces);return[el.attrib.get(_w)for el in found_elements if el is not _A]
		except Exception as e:logger.exception('Błąd podczas pobierania atrybutów href: %s',e);return[]
	def _get_element_href(self,element,element_path):
		'Pobiera wartość atrybutu xlink:href.'
		try:found_element=element.find(element_path,self.namespaces);return found_element.attrib.get(_w)if found_element is not _A else _A
		except Exception as e:logger.exception('Błąd podczas pobierania atrybutu href: %s',e);return
	def _get_podmiot(self,element,element_path):
		'Pobiera identyfikator podmiotu we władaniu (ID lub xlink:href).'
		try:
			podmiot_element=element.find(element_path,self.namespaces)
			if podmiot_element is _A:return
			for podmiot_typ in['egb:instytucja1','egb:malzenstwo','egb:osobaFizyczna','egb:podmiotGrupowy','egb:wspolnotaGruntowa']:
				podmiot=podmiot_element.find(f".//{podmiot_typ}",self.namespaces)
				if podmiot is not _A:
					href=podmiot.attrib.get(_w)
					if href:return href
			return
		except Exception as e:logger.exception('Błąd podczas pobierania podmiotu: %s',e);return
	def _iterate_features(self,tag):
		for fm in self.root.findall(_D,self.namespaces):
			for elem in fm.findall(tag,self.namespaces):yield elem
	def _OT_Ogrodzenia(self):
		columns=[_B,'rodzajOgrodzenia',_I];data=[]
		for feature_member in self.root.findall(_D,self.namespaces):
			for ogrodzenie in feature_member.findall('ot2021:OT_Ogrodzenia',self.namespaces):
				gml_id=ogrodzenie.attrib.get(_E);rodzajOgrodzenia=self._get_element_value(ogrodzenie,'.//ot2021:rodzajOgrodzenia');geometria=self._get_element_value(ogrodzenie,_P,coordinates=_C)
				if not geometria:
					try:geometria=self._get_element_value(ogrodzenie,_J,coordinates=_C)
					except Exception as e:logging.exception(e);print(e);geometria=[]
				data.append([gml_id,rodzajOgrodzenia,geometria])
		self.df_OT_Ogrodzenia=pd.DataFrame(data,columns=columns);return self.df_OT_Ogrodzenia
	def _OT_Budowle(self):
		columns=[_B,'rodzajBudowli',_I];data=[]
		for feature_member in self.root.findall(_D,self.namespaces):
			for budowla in feature_member.findall('ot2021:OT_Budowle',self.namespaces):
				gml_id=budowla.attrib.get(_E);rodzajBudowli=self._get_element_value(budowla,'.//ot2021:rodzajBudowli');geometria=self._get_element_value(budowla,_P,coordinates=_C)
				if not geometria:
					try:geometria=self._get_element_value(budowla,_J,coordinates=_C)
					except Exception as e:logging.exception(e);print(e);geometria=[]
				data.append([gml_id,rodzajBudowli,geometria])
		self.df_OT_Budowle=pd.DataFrame(data,columns=columns);return self.df_OT_Budowle
	def _OT_Skarpa(self):
		columns=[_B,'rodzajSkarpy','poczatekGorySkarpy','koniecGorySkarpy',_I];data=[]
		for feature_member in self.root.findall(_D,self.namespaces):
			for skarpa in feature_member.findall('ot2021:OT_Skarpa',self.namespaces):
				gml_id=skarpa.attrib.get(_E);rodzajSkarpy=self._get_element_value(skarpa,'.//ot2021:rodzajSkarpy');poczatekGorySkarpy=[];poczatekGorySkarpy_element=skarpa.find('.//ot2021:poczatekGorySkarpy',self.namespaces)
				if poczatekGorySkarpy_element is not _A:
					pos=poczatekGorySkarpy_element.find(_J,self.namespaces)
					if pos is not _A and pos.text:poczatekGorySkarpy=pos.text.strip().split()
				koniecGorySkarpy=[];koniecGorySkarpy_element=skarpa.find('.//ot2021:koniecGorySkarpy',self.namespaces)
				if koniecGorySkarpy_element is not _A:
					pos=koniecGorySkarpy_element.find(_J,self.namespaces)
					if pos is not _A and pos.text:koniecGorySkarpy=pos.text.strip().split()
				geometria_element=skarpa.find('.//ot2021:geometria',self.namespaces)
				if geometria_element is not _A:geometria_values=geometria_element.find(_P,self.namespaces);coordinates=geometria_values.text.strip().split()if geometria_values is not _A else[];geometria=[(float(coordinates[i]),float(coordinates[i+1]))for i in range(0,len(coordinates),2)]
				else:geometria=[]
				data.append([gml_id,rodzajSkarpy,poczatekGorySkarpy,koniecGorySkarpy,geometria])
		self.df_OT_Skarpa=pd.DataFrame(data,columns=columns);return self.df_OT_Skarpa
	def _OT_BudynekNiewykazanyWEGIB(self):
		columns=[_B,_r,_x,_s,_t,_u,_N,'zrodlo','dataPrzyjeciaDoZasobu',_I];data=[]
		for feature_member in self.root.findall(_D,self.namespaces):
			for budynek in feature_member.findall('ot2021:OT_BudynekNiewykazanyWEGIB',self.namespaces):
				gml_id=budynek.attrib.get(_E);idBudynku='Budynek w BDOT';koniecWersjaObiekt=self._get_element_value(budynek,'.//ot2021:koniecWersjaObiekt');geometria=self._get_element_value(budynek,_P,coordinates=_C)
				if not geometria:
					try:geometria=self._get_element_value(budynek,_J,coordinates=_C)
					except Exception as e:logging.exception(e);print(e);geometria=[]
				rodzajWgKST=self._get_element_value(budynek,'.//ot2021:rodzajKST');liczbaKondygnacjiNadziemnych=self._get_element_value(budynek,'.//ot2021:liczbaKondygnacjiNadziemnych');liczbaKondygnacjiPodziemnych=self._get_element_value(budynek,'.//ot2021:liczbaKondygnacjiPodziemnych');status=self._get_element_value(budynek,'.//ot2021:status');zrodlo=self._get_element_value(budynek,'.//ot2021:zrodlo');dataPrzyjeciaDoZasobu=self._get_element_value(budynek,'.//ot2021:dataPrzyjeciaDoZasobu');data.append([gml_id,idBudynku,koniecWersjaObiekt,rodzajWgKST,liczbaKondygnacjiNadziemnych,liczbaKondygnacjiPodziemnych,status,zrodlo,dataPrzyjeciaDoZasobu,geometria])
		self.df_OT_BudynekNiewykazanyWEGIB=pd.DataFrame(data,columns=columns);return self.df_OT_BudynekNiewykazanyWEGIB
	def _EGB_JednostkaRejestrowaGruntow(self):
		columns=[_R,_i,_h];data=[]
		for feature_member in self.root.findall(_D,self.namespaces):
			for jednostka in feature_member.findall('egb:EGB_JednostkaRejestrowaGruntow',self.namespaces):id=jednostka.attrib.get(_E);idJednostkiRejestrowej=self._get_element_value(jednostka,'.//egb:idJednostkiRejestrowej');grupaRejestrowa=self._get_element_value(jednostka,'.//egb:grupaRejestrowa');data.append([id,idJednostkiRejestrowej,grupaRejestrowa])
		self.df_EGB_JednostkaRejestrowaGruntow=pd.DataFrame(data,columns=columns);return self.df_EGB_JednostkaRejestrowaGruntow
	def _EGB_OsobaFizyczna(self):
		columns=[_B,_A9,_AB,_AC,_AA,'imieOjca',_AD,'pesel','plec',_N,_AE,_AH,_AI];data=[];plec_dict={'1':'M','2':'K'}
		for feature_member in self.root.findall(_D,self.namespaces):
			for osoba in feature_member.findall('egb:EGB_OsobaFizyczna',self.namespaces):id=osoba.attrib.get(_E);pierwszeImie=self._get_element_value(osoba,'.//egb:pierwszeImie');pierwszyCzlonNazwiska=self._get_element_value(osoba,'.//egb:pierwszyCzlonNazwiska');drugiCzlonNazwiska=self._get_element_value(osoba,'.//egb:drugiCzlonNazwiska');drugieImie=self._get_element_value(osoba,'.//egb:drugieImie');imieOjca=self._get_element_value(osoba,'.//egb:imieOjca');imieMatki=self._get_element_value(osoba,'.//egb:imieMatki');pesel=self._get_element_value(osoba,'.//egb:pesel');plec=self._get_element_value(osoba,'.//egb:plec');plec=plec_dict.get(plec,plec);status=self._get_element_value(osoba,_V);informacjaOSmierci=self._get_element_value(osoba,'.//egb:informacjaOSmierci');adresZameldowania=self._get_element_href(osoba,'.//egb:adresZameldowania')or self._get_element_href(osoba,'.//egb:adresOsobyFizycznej');adresStalegoPobytu=self._get_element_href(osoba,'.//egb:adresStalegoPobytu')or self._get_element_href(osoba,'.//egb:adresKorespondencyjnyOF');data.append([id,pierwszeImie,pierwszyCzlonNazwiska,drugiCzlonNazwiska,drugieImie,imieOjca,imieMatki,pesel,plec,status,informacjaOSmierci,adresZameldowania,adresStalegoPobytu])
		self.df_EGB_OsobaFizyczna=pd.DataFrame(data,columns=columns);return self.df_EGB_OsobaFizyczna
	def _EGB_Malzenstwo(self):
		'Parsuje elementy EGB_Malzenstwo i zwraca DataFrame.';A='Małżeństwo';columns=[_B,_H,_N];data=[];status_dict={34:A,35:A}
		for feature_member in self.root.findall(_D,self.namespaces):
			for malzenstwo in feature_member.findall('egb:EGB_Malzenstwo',self.namespaces):id=malzenstwo.attrib.get(_E);osobaFizyczna2=self._get_element_href(malzenstwo,'.//egb:osobaFizyczna2');osobaFizyczna3=self._get_element_href(malzenstwo,'.//egb:osobaFizyczna3');status=self._get_element_value(malzenstwo,_V);status=status_dict.get(int(status),status);data.append([id,osobaFizyczna2,status]);data.append([id,osobaFizyczna3,status])
		self.df_EGB_Malzenstwo=pd.DataFrame(data,columns=columns);return self.df_EGB_Malzenstwo
	def _EGB_Instytucja(self):
		columns=[_B,_X,_g,_Y,_N,_c];data=[]
		for feature_member in self.root.findall(_D,self.namespaces):
			for instytucja in feature_member.findall('egb:EGB_Instytucja',self.namespaces):id=instytucja.attrib.get(_E);nazwaPelna=self._get_element_value(instytucja,_Ac);nazwaSkrocona=self._get_element_value(instytucja,_Ad);regon=self._get_element_value(instytucja,_Ae);status=self._get_element_value(instytucja,_V);adresSiedziby=self._get_element_href(instytucja,_Af)or self._get_element_href(instytucja,'.//egb:adresInstytucji');data.append([id,nazwaPelna,nazwaSkrocona,regon,status,adresSiedziby])
		self.df_EGB_Instytucja=pd.DataFrame(data,columns=columns);return self.df_EGB_Instytucja
	def _EGB_PodmiotGrupowy(self):
		columns=[_B,_X,_g,_Y,_N,_c];columns_instytucja=columns+[_j];columns_osobaFizyczna=columns+[_AJ];columns_malzenstwo=columns+[_H];data_nazwaPelna=[];data_instytucja=[];data_osobaFizyczna=[];data_malzenstwo=[]
		for feature_member in self.root.findall(_D,self.namespaces):
			for podmiot in feature_member.findall('egb:EGB_PodmiotGrupowy',self.namespaces):
				is_nazwaPelna=_S;id=podmiot.attrib.get(_E);nazwaPelna=self._get_element_value(podmiot,_Ac);nazwaSkrocona=self._get_element_value(podmiot,_Ad);regon=self._get_element_value(podmiot,_Ae);status=self._get_element_value(podmiot,_V);adresSiedziby=self._get_element_value(podmiot,_Af)
				if is_nazwaPelna is _S:data_nazwaPelna.append([id,nazwaPelna,nazwaSkrocona,regon,status,adresSiedziby]);is_nazwaPelna=_C
				for pod in podmiot.findall('.//egb:instytucja',self.namespaces):instytucja=self._get_element_href(pod,_K);data_instytucja.append([id,nazwaPelna,nazwaSkrocona,regon,status,adresSiedziby,instytucja])
				for pod in podmiot.findall('.//egb:osobaFizyczna4',self.namespaces):osobaFizyczna=self._get_element_href(pod,_K);data_osobaFizyczna.append([id,nazwaPelna,nazwaSkrocona,regon,status,adresSiedziby,osobaFizyczna])
				for pod in podmiot.findall('.//egb:malzenstwo3',self.namespaces):malzenstwo=self._get_element_href(pod,_K);data_malzenstwo.append([id,nazwaPelna,nazwaSkrocona,regon,status,adresSiedziby,malzenstwo])
		self.df_EGB_PodmiotGrupowy_nazwaPelna=pd.DataFrame(data_nazwaPelna,columns=columns);self.df_EGB_PodmiotGrupowy_instytucja=pd.DataFrame(data_instytucja,columns=columns_instytucja);self.df_EGB_PodmiotGrupowy_osobaFizyczna=pd.DataFrame(data_osobaFizyczna,columns=columns_osobaFizyczna);self.df_EGB_PodmiotGrupowy_malzenstwo=pd.DataFrame(data_malzenstwo,columns=columns_malzenstwo);return self.df_EGB_PodmiotGrupowy_nazwaPelna,self.df_EGB_PodmiotGrupowy_instytucja,self.df_EGB_PodmiotGrupowy_osobaFizyczna,self.df_EGB_PodmiotGrupowy_malzenstwo
	def _EGB_WspolnotaGruntowa(self):
		columns=[_B,_X,_N];columns_spolkaZarzadajaca=columns+[_AL];columns_podmiotUprawniony=columns+[_AM];columns_malzenstwoUprawnione=columns+[_H];columns_osobaFizycznaUprawniona=columns+[_AK];data_nazwa=[];data_spolkaZarzadajaca=[];data_podmiotUprawniony=[];data_malzenstwoUprawnione=[];data_osobaFizycznaUprawniona=[]
		for feature_member in self.root.findall(_D,self.namespaces):
			for wspolnota in feature_member.findall('egb:EGB_WspolnotaGruntowa',self.namespaces):
				is_nazwa=_S;wspolnota_id=wspolnota.attrib.get(_E);nazwa=self._get_element_value(wspolnota,'.//egb:nazwa');status=self._get_element_value(wspolnota,_V)
				if is_nazwa is _S:data_nazwa.append([wspolnota_id,nazwa,status]);is_nazwa=_C
				for wsp in wspolnota.findall('.//egb:spolkaZarzadajaca',self.namespaces):spolkaZarzadajaca=self._get_element_href(wsp,_K);data_spolkaZarzadajaca.append([wspolnota_id,nazwa,status,spolkaZarzadajaca])
				for wsp in wspolnota.findall('.//egb:podmiotUprawniony',self.namespaces):podmiotUprawniony=self._get_element_href(wsp,_K);data_podmiotUprawniony.append([wspolnota_id,nazwa,status,podmiotUprawniony])
				for wsp in wspolnota.findall('.//egb:malzenstwoUprawnione',self.namespaces):malzenstwoUprawnione=self._get_element_href(wsp,_K);data_malzenstwoUprawnione.append([wspolnota_id,nazwa,status,malzenstwoUprawnione])
				for wsp in wspolnota.findall('.//egb:osobaFizycznaUprawniona',self.namespaces)+wspolnota.findall('.//egb:osobaUprawniona',self.namespaces):osobaFizycznaUprawniona=self._get_element_href(wsp,_K);data_osobaFizycznaUprawniona.append([wspolnota_id,nazwa,status,osobaFizycznaUprawniona])
		self.df_EGB_WspolnotaGruntowa_nazwa=pd.DataFrame(data_nazwa,columns=columns);self.df_EGB_WspolnotaGruntowa_spolkaZarzadajaca=pd.DataFrame(data_spolkaZarzadajaca,columns=columns_spolkaZarzadajaca);self.df_EGB_WspolnotaGruntowa_podmiotUprawniony=pd.DataFrame(data_podmiotUprawniony,columns=columns_podmiotUprawniony);self.df_EGB_WspolnotaGruntowa_malzenstwoUprawnione=pd.DataFrame(data_malzenstwoUprawnione,columns=columns_malzenstwoUprawnione);self.df_EGB_WspolnotaGruntowa_osobaFizycznaUprawniona=pd.DataFrame(data_osobaFizycznaUprawniona,columns=columns_osobaFizycznaUprawniona);return self.df_EGB_WspolnotaGruntowa_nazwa,self.df_EGB_WspolnotaGruntowa_spolkaZarzadajaca,self.df_EGB_WspolnotaGruntowa_podmiotUprawniony,self.df_EGB_WspolnotaGruntowa_malzenstwoUprawnione,self.df_EGB_WspolnotaGruntowa_osobaFizycznaUprawniona
	def _EGB_UdzialWeWlasnosci(self):
		columns=[_A5,_A6,_d,_R];data=[];rodzajPrawa_dict={1:'Własność',2:'Władanie samoistne'}
		for feature_member in self.root.findall(_D,self.namespaces):
			for udzial in feature_member.findall('egb:EGB_UdzialWeWlasnosci',self.namespaces):rodzajPrawa=self._get_element_value(udzial,'.//egb:rodzajPrawa');rodzajPrawa=rodzajPrawa_dict.get(int(rodzajPrawa),rodzajPrawa);licznikUlamka=self._get_element_value(udzial,_Ag);mianownikUlamka=self._get_element_value(udzial,_Ah);udzialWlasnosci=f"{licznikUlamka}/{mianownikUlamka}";podmiot_id=self._get_element_href(udzial,'.//egb:podmiotUdzialuWlasnosci')or self._get_podmiot(udzial,_Ai);idJRG=self._get_element_href(udzial,'.//egb:przedmiotUdzialuWlasnosci')or self._get_element_href(udzial,_Aj);data.append([rodzajPrawa,udzialWlasnosci,podmiot_id,idJRG])
		self.df_EGB_UdzialWeWlasnosci=pd.DataFrame(data,columns=columns);return self.df_EGB_UdzialWeWlasnosci
	def _EGB_UdzialWeWladaniu(self):
		columns=[_A7,_A8,_d,_R];data=[];rodzajWladania_dict={'1':'uzytkowanieWieczyste','2':'trwalyZarzad','3':'zarzad','4':'uzytkowanie','5':'innyRodzajWladania','6':'wykonywaniePrawaWlasnosciSPIInnychPrawRzeczowych','7':'gospodarowanieZasobemNieruchomosciSPLubGmPowWoj','8':'gospodarowanieGruntemSPPokrytymWodamiPowierzchniowymi','9':'wykonywanieZadanZarzadcyDrogPub'}
		for feature_member in self.root.findall(_D,self.namespaces):
			for udzial in feature_member.findall('egb:EGB_UdzialWeWladaniu',self.namespaces):rodzajWladania=self._get_element_value(udzial,'.//egb:rodzajWladania');rodzajWladania=rodzajWladania_dict.get(rodzajWladania,rodzajWladania);licznik=self._get_element_value(udzial,_Ag);mianownik=self._get_element_value(udzial,_Ah);udzialWladania=f"{licznik}/{mianownik}";podmiot_id=self._get_element_href(udzial,'.//egb:podmiotUdzialuWeWladaniu')or self._get_podmiot(udzial,_Ai);idJRG=self._get_element_href(udzial,'.//egb:przedmiotUdzialuWladania')or self._get_element_href(udzial,_Aj);data.append([rodzajWladania,udzialWladania,podmiot_id,idJRG])
		self.df_EGB_UdzialWeWladaniu=pd.DataFrame(data,columns=columns);return self.df_EGB_UdzialWeWladaniu
	def _EGB_AdresPodmiotu(self):
		columns=[_b,'kraj',_AF,_AG,'ulica',_Z,_a];data=[]
		for feature_member in self.root.findall(_D,self.namespaces):
			for adres in feature_member.findall('egb:EGB_AdresPodmiotu',self.namespaces)or feature_member.findall('egb:EGB_AdresZameldowania',self.namespaces):id=adres.attrib.get(_E);kraj=self._get_element_value(adres,'egb:kraj');miejscowosc=self._get_element_value(adres,'egb:miejscowosc');kodPocztowy=self._get_element_value(adres,'egb:kodPocztowy');ulica=self._get_element_value(adres,'egb:ulica');numerPorzadkowy=self._get_element_value(adres,_Ak);numerLokalu=self._get_element_value(adres,_Al);data.append([id,kraj,miejscowosc,kodPocztowy,ulica,numerPorzadkowy,numerLokalu])
		self.df_EGB_AdresPodmiotu=pd.DataFrame(data,columns=columns);return self.df_EGB_AdresPodmiotu
	def _EGB_AdresNieruchomosci(self):
		columns=[_B,_AS,_AT,_AU,_AV,_Z,_a,_I];data=[]
		for feature_member in self.root.findall(_D,self.namespaces):
			for adres in feature_member.findall('egb:EGB_AdresNieruchomosci',self.namespaces):id=adres.attrib.get(_E);nazwaMiejscowosci=self._get_element_value(adres,'egb:nazwaMiejscowosci');idMiejscowosci=self._get_element_value(adres,'egb:idMiejscowosci');nazwaUlicy=self._get_element_value(adres,'egb:nazwaUlicy');idNazwyUlicy=self._get_element_value(adres,'egb:idNazwyUlicy');numerPorzadkowy=self._get_element_value(adres,_Ak);numerLokalu=self._get_element_value(adres,_Al);geometria=self._get_element_value(adres,_J,pos=_C);data.append([id,nazwaMiejscowosci,idMiejscowosci,nazwaUlicy,idNazwyUlicy,numerPorzadkowy,numerLokalu,geometria])
		self.df_EGB_AdresNieruchomosci=pd.DataFrame(data,columns=columns);return self.df_EGB_AdresNieruchomosci
	def _EGB_PunktGraniczny(self):
		columns=[_B,_I,_k,_l,_m,_n,_o,_p,_U];data=[]
		for feature_member in self.root.findall(_D,self.namespaces):
			for punkt in feature_member.findall('egb:EGB_PunktGraniczny',self.namespaces):id=punkt.attrib.get(_E);geometria=self._get_element_value(punkt,_J,pos=_C);idPunktu=self._get_element_value(punkt,'.//egb:idPunktu');sposobPozyskania=self._get_element_value(punkt,'.//egb:sposobPozyskania');spelnienieWarunkowDokl=self._get_element_value(punkt,'.//egb:spelnienieWarunkowDokl');rodzajStabilizacji=self._get_element_value(punkt,'.//egb:rodzajStabilizacji');oznWMaterialeZrodlowym=self._get_element_value(punkt,'.//egb:oznWMaterialeZrodlowym');numerOperatuTechnicznego=self._get_element_value(punkt,'.//egb:numerOperatuTechnicznego');dodatkoweInformacje=self._get_element_value(punkt,_Am);data.append([id,geometria,idPunktu,sposobPozyskania,spelnienieWarunkowDokl,rodzajStabilizacji,oznWMaterialeZrodlowym,numerOperatuTechnicznego,dodatkoweInformacje])
		self.df_EGB_PunktGraniczny=pd.DataFrame(data,columns=columns);return self.df_EGB_PunktGraniczny
	def _EGB_Budynek(self):
		columns=[_B,_r,_x,_s,_t,_u,_AN,_AO,_AP,_AQ,_AR,_U,_AW,_AX,_I];data=[]
		for feature_member in self.root.findall(_D,self.namespaces):
			for budynek in feature_member.findall('egb:EGB_Budynek',self.namespaces):
				gml_id=budynek.attrib.get(_E);idBudynku=self._get_element_value(budynek,'.//egb:idBudynku');koniecWersjaObiekt=self._get_element_value(budynek,_An);geometria=self._get_element_value(budynek,_P,coordinates=_C)
				if not geometria:
					try:geometria=self._get_element_value(budynek,_J,coordinates=_C)
					except Exception as e:logging.exception(e);print(e);geometria=[]
				rodzajWgKST=self._get_element_value(budynek,'.//egb:rodzajWgKST');liczbaKondygnacjiNadziemnych=self._get_element_value(budynek,'.//egb:liczbaKondygnacjiNadziemnych');liczbaKondygnacjiPodziemnych=self._get_element_value(budynek,'.//egb:liczbaKondygnacjiPodziemnych');powZabudowy=self._get_element_value(budynek,'.//egb:powZabudowy');lacznaPowUzytkowaLokaliWyodrebnionych=self._get_element_value(budynek,'.//egb:lacznaPowUzytkowaLokaliWyodrebnionych');lacznaPowUzytkowaLokaliNiewyodrebnionych=self._get_element_value(budynek,'.//egb:lacznaPowUzytkowaLokaliNiewyodrebnionych');lacznaPowUzytkowaPomieszczenPrzynaleznych=self._get_element_value(budynek,'.//egb:lacznaPowUzytkowaPomieszczenPrzynaleznych');dokumentWlasnosci=self._get_element_value(budynek,_Ao);dodatkoweInformacje=self._get_element_value(budynek,_Am);dzialkaZabudowana=self._get_element_href(budynek,'.//egb:dzialkaZabudowana');adresBudynku=self._get_element_href(budynek,'.//egb:adresBudynku');data.append([gml_id,idBudynku,koniecWersjaObiekt,rodzajWgKST,liczbaKondygnacjiNadziemnych,liczbaKondygnacjiPodziemnych,powZabudowy,lacznaPowUzytkowaLokaliWyodrebnionych,lacznaPowUzytkowaLokaliNiewyodrebnionych,lacznaPowUzytkowaPomieszczenPrzynaleznych,dokumentWlasnosci,dodatkoweInformacje,dzialkaZabudowana,adresBudynku,geometria])
		self.df_EGB_Budynek=pd.DataFrame(data,columns=columns);return self.df_EGB_Budynek
	def _EGB_DzialkaEwidencyjna(self):
		columns=[_B,_L,_x,_Q,_I,_T,_W,_R,'adresDzialki',_q,_AY];data=[]
		for feature_member in self.root.findall(_D,self.namespaces):
			for dzialka in feature_member.findall('egb:EGB_DzialkaEwidencyjna',self.namespaces):
				gml_id=dzialka.attrib.get(_E);idDzialki=self._get_element_value(dzialka,'.//egb:idDzialki');koniecWersjaObiekt=self._get_element_value(dzialka,_An);numer_kw=self._get_element_value(dzialka,'.//egb:numerKW');dokumentWlasnosci=self._get_element_value(dzialka,_Ao)
				if not numer_kw:numer_kw=dokumentWlasnosci
				geometria=self._get_element_value(dzialka,_P,coordinates=_C)
				if not geometria:
					try:geometria=self._get_element_value(dzialka,_J,coordinates=_C)
					except Exception as e:logging.exception(e);print(e);geometria=[]
				pole_ewidencyjne=self._get_element_value(dzialka,'.//egb:poleEwidencyjne');dokladnoscReprezentacjiPola=self._get_element_value(dzialka,'.//egb:dokladnoscReprezentacjiPola')
				if dokladnoscReprezentacjiPola=='1':dokladnoscReprezentacjiPola='M'
				elif dokladnoscReprezentacjiPola=='2':dokladnoscReprezentacjiPola='Ara'
				idJRG=self._get_element_href(dzialka,'.//egb:JRG2');punktGranicyDzialki=self._get_element_href_list(dzialka,'.//egb:punktGranicyDzialki');adresDzialki=self._get_element_href_list(dzialka,'.//egb:adresDzialki');klasouzytek=self._get_element_klasouzytek_list(dzialka,'.//egb:klasouzytek');data.append([gml_id,idDzialki,koniecWersjaObiekt,numer_kw,geometria,pole_ewidencyjne,dokladnoscReprezentacjiPola,idJRG,adresDzialki,punktGranicyDzialki,klasouzytek])
		self.df_EGB_DzialkaEwidencyjna=pd.DataFrame(data,columns=columns);return self.df_EGB_DzialkaEwidencyjna
	def _EGB_KonturUzytkuGruntowego(self):
		columns=[_B,'idIIP',_I,'idUzytku','OFU',_Ap];data=[]
		for feature_member in self.root.findall(_D,self.namespaces):
			for kontur in feature_member.findall('egb:EGB_KonturUzytkuGruntowego',self.namespaces):
				gml_id=kontur.attrib.get(_E);idIIP=self._get_element_value(kontur,_Aq);geometria=self._get_element_value(kontur,_P,coordinates=_C)
				if not geometria:
					try:geometria=self._get_element_value(kontur,_J,coordinates=_C)
					except Exception as e:logging.exception(e);print(e);geometria=[]
				idUzytku=self._get_element_value(kontur,'.//egb:idUzytku');OFU=self._get_element_value(kontur,_v);lokalizacjaUzytku=self._get_element_href(kontur,_Ar);data.append([gml_id,idIIP,geometria,idUzytku,OFU,lokalizacjaUzytku])
		self.df_EGB_KonturUzytkuGruntowego=pd.DataFrame(data,columns=columns);return self.df_EGB_KonturUzytkuGruntowego
	def _EGB_KonturKlasyfikacyjny(self):
		columns=[_B,'idIIP',_I,'idKonturu','OFU','OZU','OZK',_Ap];data=[]
		for feature_member in self.root.findall(_D,self.namespaces):
			for kontur in feature_member.findall('egb:EGB_KonturKlasyfikacyjny',self.namespaces):
				gml_id=kontur.attrib.get(_E);idIIP=self._get_element_value(kontur,_Aq);geometria=self._get_element_value(kontur,_P,coordinates=_C)
				if not geometria:
					try:geometria=self._get_element_value(kontur,_J,coordinates=_C)
					except Exception as e:logging.exception(e);print(e);geometria=[]
				idKonturu=self._get_element_value(kontur,'.//egb:idKonturu');OFU=self._get_element_value(kontur,_v);OZU=self._get_element_value(kontur,_Aa);OZK=self._get_element_value(kontur,_Ab);lokalizacjaUzytku=self._get_element_href(kontur,_Ar);data.append([gml_id,idIIP,geometria,idKonturu,OFU,OZU,OZK,lokalizacjaUzytku])
		self.df_EGB_KonturKlasyfikacyjny=pd.DataFrame(data,columns=columns);return self.df_EGB_KonturKlasyfikacyjny
	def _PrezentacjaGraficzna(self):
		columns=['pos','katObrotu','justyfikacja','tekst',_AZ];data=[]
		for feature_member in self.root.findall(_D,self.namespaces):
			for prezentacja in feature_member.findall('egb:PrezentacjaGraficzna',self.namespaces):pos_value='','';pos_value=self._get_element_value(prezentacja,_J,pos=_C);justyfikacja=self._get_element_value(prezentacja,'.//egb:justyfikacja');katObrotu=self._get_element_value(prezentacja,'.//egb:katObrotu');tekst_value=self._get_element_value(prezentacja,'.//egb:tekst');href_value=self._get_element_href(prezentacja,'.//egb:obiektPrzedstawiany');data.append([pos_value,katObrotu,justyfikacja,tekst_value,href_value])
		self.df_PrezentacjaGraficzna=pd.DataFrame(data,columns=columns);return self.df_PrezentacjaGraficzna
	def get_epsg_from_root(self):
		if self.root is _A:return
		crs=_A
		for feature_member in self.root:
			geometry_with_srs=feature_member.find(_As)
			if geometry_with_srs is not _A:crs=geometry_with_srs.attrib['srsName'];break
		if crs:self.epsg=crs.lstrip('urn:ogc:def:crs:EPSG::')
		return self.epsg
	@staticmethod
	def fill_missing_values(main_df,*dfs,col='ID'):
		result_df=main_df.astype(str).copy()
		for df in dfs:
			if df.empty or col not in df.columns:continue
			df=df.astype(str);common_columns=result_df.columns.intersection(df.columns).tolist()
			if col in common_columns:common_columns.remove(col)
			temp_df=result_df.merge(df,on=col,how=_G,suffixes=('',_y))
			for col_name in common_columns:
				if temp_df[f"{col_name}_temp"].notna().any():temp_df[col_name]=temp_df[col_name].combine_first(temp_df[f"{col_name}_temp"])
			temp_df=temp_df.drop(columns=[f"{col_name}_temp"for col_name in common_columns]);result_df=temp_df
		return result_df
	@staticmethod
	def concat_dataframe(podmioty_dfs):
		try:
			concat_ready=[df for df in podmioty_dfs if isinstance(df,pd.DataFrame)and not df.empty]
			if concat_ready:df_GML_podmioty_concated=pd.concat(concat_ready,ignore_index=_C);logging.info(f"EGIB_Podmioty successfully concatenated ({len(df_GML_podmioty_concated)} rows).");return df_GML_podmioty_concated
			else:logging.warning('No valid DataFrames to concatenate in EGIB_Podmioty.');return pd.DataFrame()
		except Exception as e:logging.exception('concat_dataframe() failed.');return pd.DataFrame()
	@staticmethod
	def merge_dataframe(main_df,*dfs,how=_M,on=_A,left_on=_A,right_on=_A):
		result_df=main_df.copy()
		for df in dfs:
			if df.empty:continue
			df=df.astype(str).copy();common_columns=result_df.columns.intersection(df.columns).tolist();temp_df=result_df.merge(df,how=how,on=on,left_on=left_on,right_on=right_on,suffixes=('',_y))
			for col_name in common_columns:
				temp_col=f"{col_name}_temp"
				if temp_col in temp_df.columns and temp_df[temp_col].notna().any():temp_df[col_name]=temp_df[col_name].combine_first(temp_df[temp_col])
			temp_df.drop(columns=[f"{col_name}_temp"for col_name in common_columns if f"{col_name}_temp"in temp_df.columns],inplace=_C);result_df=temp_df
		return result_df
	@staticmethod
	def merge_dataframe_old(main_df,*dfs,how=_M,on=_A,left_on=_A,right_on=_A):
		result_df=main_df.copy()
		for df in dfs:
			if df.empty:continue
			df=df.astype(str);df=df.copy();common_columns=result_df.columns.intersection(df.columns).tolist();temp_df=result_df.merge(df,how=how,on=on,left_on=left_on,right_on=right_on,suffixes=('',_y))
			for col_name in common_columns:
				if temp_df[f"{col_name}_temp"].notna().any():temp_df[col_name]=temp_df[col_name].combine_first(temp_df[f"{col_name}_temp"])
			temp_df=temp_df.drop(columns=[f"{col_name}_temp"for col_name in common_columns]);result_df=temp_df
		return result_df
	@staticmethod
	def get_crs_epsg(path):
		tree=ET.parse(path);root=tree.getroot();crs=_A
		for feature_member in root:
			geometry_with_srs=feature_member.find(_As)
			if geometry_with_srs is not _A:crs=geometry_with_srs.attrib['srsName'];break
		return crs.lstrip('urn:ogc:def:crs:')
	@staticmethod
	def poprawka_pow(df,col,epsg):
		try:
			geometry=df[col];avg_coords=[];Pole=[]
			for(id,geom)in zip(df[_L],geometry):
				if isinstance(geom,list)and all(isinstance(point,tuple)for point in geom):
					try:geom=Polygon(geom)
					except Exception as e:logging.exception(e);print(e);continue
					"\n                    if id == '2176':\n                        N = 5\n                    elif id == '2177':\n                        N = 6\n                    elif id == '2178':\n                        N = 7\n                    elif id == '2179':\n                        N = 8\n                    else:\n                        N = 6\n                    ";N={'2176':5,'2177':6,'2178':7,'2179':8}.get(epsg,6);area_hectares=geom.area;area_hectares=area_hectares;area=area_hectares/10000;x,y=geom.exterior.coords.xy;coords=list(zip(x,y));avg_x=sum(x)/len(x);avg_y=sum(y)/len(y);avg_coords.append((avg_x,avg_y));q1=306.752873;q2=-.312616;q3=.006382;q4=.158591;sigmaS=-7.7;m0=.999923;X2000=avg_y;Y2000=avg_x;XGK=X2000/m0;YGK=(Y2000-(N*1000000+500000))/m0;u=(XGK-58e5)*2.*10**-6;v=YGK*2.*10**-6;sigma=sigmaS+m0*v**2*(q1+q2*u+q3*u**2+q4*v**2);m=sigma*10**-5+1;delta_Po=area*(m**2-1);P=area_hectares-delta_Po;P='{:.4f}'.format(round(P/10000,4));Pole.append(P)
			df[_e]=Pole
		except Exception as e:
			logging.exception(e);print(f"Wystąpił błąd podczas: {str(e)}")
			try:df[_e]=_A
			except Exception as e:logging.exception(e);print(f"Wystąpił błąd podczas: {str(e)}")
		return df
if __name__=='__main__':0