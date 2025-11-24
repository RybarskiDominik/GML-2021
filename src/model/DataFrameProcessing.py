from dataclasses import dataclass, field
from typing import Optional, Tuple
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

@dataclass
class myDataFrame(pd.DataFrame):

    df_1_sort_list = []
    df_2_sort_list = []

    df_gml: pd.DataFrame = field(default_factory=pd.DataFrame) # ['Działka', 'NR', 'X', 'Y', 'H', 'SPD', 'ISD', 'STB']
    df_gml_list: pd.DataFrame = field(default_factory=pd.DataFrame)  # ['Działka']

    df_memory: pd.DataFrame = field(default_factory=pd.DataFrame)  # ['NR', 'X', 'Y', 'H', 'SPD', 'ISD', 'STB']

    df_1: pd.DataFrame = field(default_factory=pd.DataFrame)  # ['NR', 'X', 'Y', 'H', 'SPD', 'ISD', 'STB']
    df_2: pd.DataFrame = field(default_factory=pd.DataFrame)  # ['NR', 'X', 'Y', 'H', 'SPD', 'ISD', 'STB']
    df_3: pd.DataFrame = field(default_factory=pd.DataFrame)  # ["DX", "DY", "DH", "DL"]

    df_all: pd.DataFrame = field(default_factory=pd.DataFrame)  # [df_1 + df_2 + df_3]

    @classmethod
    def display_data(cls): 
        cls.df_all = pd.concat([cls.df_1, cls.df_2, cls.df_3], axis=1)

        return cls.df_all

    @classmethod
    def drop_H(cls): # Usuwanie kolumny z pd.DataFrame.
        if hasattr(cls, 'df_1') and cls.df_1 is not None and not cls.df_1.empty and "H" in cls.df_1.columns:
            cls.df_1 = cls.df_1.drop(["H"], axis=1)
        if hasattr(cls, 'df_2') and cls.df_2 is not None and not cls.df_2.empty and "H" in cls.df_2.columns:
            cls.df_2 = cls.df_2.drop(["H"], axis=1)
        if hasattr(cls, 'df_3') and cls.df_3 is not None and not cls.df_3.empty and "H" in cls.df_3.columns:
            cls.df_3 = cls.df_3.drop(["H"], axis=1)

    @classmethod
    def read(cls, path=None, df_name=None, separator=None):  # Czytanie danych z pliku.
        try:
            names = [0, 1, 2, 3, 4, 5, 6]
            if  path.endswith('.txt') or path.endswith('.csv'):
                df = pd.read_csv(path, sep = r'\s+', dtype=str, names=names, header = None, on_bad_lines = 'skip', skip_blank_lines = True)
            elif path.endswith('.xlsx'):
                df = pd.read_excel(path, dtype=str, names=names, header=None)
            else:
                return False
        except Exception as e:
            logging.exception(e)
            print(e)
            return False

        setattr(cls, df_name, df)
        return df

    @classmethod
    def drop_H_in_df(cls, df_name=None, df=None):
        if df is None or df.empty:
            df = getattr(cls, df_name)

        if hasattr(cls, df_name) and not df.empty and "H" in df.columns:
            df = df.drop(["H"], axis=1)
        if hasattr(cls, df_name) and not df.empty and "DH" in df.columns:
            df = df.drop(["DH"], axis=1)
        setattr(cls, df_name, df)
        
        return df

    @classmethod
    def drop_columns_in_df(cls, df_name=None, *columns, df=None):
        if df is None or df.empty:
            df = getattr(cls, df_name)

        if hasattr(cls, df_name) and not df.empty:
            df = df.drop(columns=[col for col in columns if col in df.columns])

        setattr(cls, df_name, df)
        return df

    @classmethod 
    def clean(cls, df_name=None, df=None):  # Czyszczenie wierszy o nieodpowiednim formacie.
        if df is None or df.empty:
            df = getattr(cls, df_name)

        df = df.iloc[:,:7].copy()

        df[df.columns[1]] = df[df.columns[1]].fillna(0.00)
        df[df.columns[2]] = df[df.columns[2]].fillna(0.00)
        if df[df.columns[3]].notna().any():  # if len(df.columns) > 3:
            df[df.columns[3]] = df[df.columns[3]].fillna(0.00)

        df[1] = df[1].replace(',', '.', regex=True)
        df[df.columns[1]] = pd.to_numeric(df[df.columns[1]], errors='coerce')
        df[2] = df[2].replace(',', '.', regex=True)
        df[df.columns[2]] = pd.to_numeric(df[df.columns[2]], errors='coerce')
        if df[df.columns[3]].notna().any():  # if len(df.columns) > 3:
            df[3] = df[3].replace(',', '.', regex=True)
            df[df.columns[3]] = pd.to_numeric(df[df.columns[3]], errors='coerce')
        # Przechowujemy kopię DataFrame przed usunięciem wierszy
        original_df = df.copy()

        # Usuwanie wierszy z brakującymi wartościami w odpowiednich kolumnach
        columns_to_check = [df.columns[1], df.columns[2]]
        
        if df[df.columns[3]].notna().any():
            columns_to_check.append(df.columns[3])

        df = df.dropna(subset=[df.columns[1], df.columns[2], df.columns[3]] if df[df.columns[3]].notna().any() else [df.columns[1], df.columns[2]])

        skipped_rows = original_df[~original_df.index.isin(df.index)]

        setattr(cls, df_name, df)
        return df, skipped_rows

    @classmethod
    def set_float_and_name(cls, df_name=None, df=None):  # Nadawanie nazw kolumnom oraz odpowiadającym im typom danych.
        if df is None or df.empty:
            df = getattr(cls, df_name)

        df[0] = df[0].astype(str)
        df = df.rename(columns = {0: 'NR'})

        df[1] = df[1].astype(float).round(2)  # df[1] = df[1].map('{:.2f}'.format).astype(float)
        df = df.rename(columns = {1: 'X'})

        df[2] = df[2].astype(float).round(2)  # df[2] = df[2].map('{:.2f}'.format).astype(float)
        df = df.rename(columns = {2: 'Y'})

        df[3] = df[3].astype(float).round(2)  # df[3] = df[3].map('{:.2f}'.format).astype(float)
        df = df.rename(columns = {3: 'H'})

        df[4] = df[4].round(0)
        df = df.rename(columns = {4: 'SPD'})
        df[5] = df[5].round(0)
        df = df.rename(columns = {5: 'ISD'})
        df[6] = df[6].round(0)
        df = df.rename(columns = {6: 'STB'})

        setattr(cls, df_name, df)
        return df

    @classmethod
    def sort(cls, df_name=None, name=None, df=None):  # Sortowanie danych.
        if df is None or df.empty:
            df = getattr(cls, df_name)
        df = df.copy()
        try:
            df['Rep'] = df[name].str.replace(r'[a-zA-Z]', '', regex=True)                
            df['SortN'] = df['Rep'].str.replace(r'[^a-zA-Z0-9]', '.', regex=True)
            df['SortL'] = df[name].str.replace(r'[^a-zA-Z]', '', regex=True)
            df.loc[df['SortN'] == '', 'SortN'] = np.nan    
            df['SortN'] = df['SortN'].astype(float)
            df = df.sort_values(['SortN', 'SortL'], na_position='first')
        except Exception as e:
            logging.exception(e)
            print(f'Sorting error {e}')
            return

        try:
            df.drop(columns=['Rep', 'SortN', 'SortL'], axis=1, inplace=True)
            df.reset_index(drop=True, inplace=True)
        except:
            pass

        setattr(cls, df_name, df)
        return df

    @classmethod
    def assign(cls):  # Przyporządkowanie danych z tabel df_1 i df_2.
        if cls.df_1.isna().all().all() or cls.df_2.empty:
            print("Empty")
            return False
        df_def = pd.DataFrame()
        df1 = cls.df_1.copy()
        df2 = cls.df_2.copy()

        df1['Numer'] = df1['NR'].astype(str).str.extract(r'(\d+)')
        df2['Numer'] = df2['NR'].astype(str).str.extract(r'(\d+)')

        df_def['Numer'] = df2['Numer']

        df2 = pd.merge(df2, df1[['Numer']], how='outer', on=['Numer'])
        df1 = pd.merge(df1, df_def[['Numer']], how='outer', on=['Numer'])

        df1['NR'] = df1['NR'].fillna(df1['Numer'])
        df2['NR'] = df2['NR'].fillna(df2['Numer'])
        
        try:
            df1 = df1.drop(columns=['Numer'])
            df2 = df2.drop(columns=['Numer'])
        except:
            pass
        #cls.df_1 = df1
        #cls.df_2 = df2
        myDataFrame.sort('df_1', "NR", df1)
        myDataFrame.sort('df_2', "NR", df2)
        return df1, df2

    @classmethod
    def separation(cls, df_name=None, df=None, sort_by_column='NR'):  # Separacja df_1 na df_1 i df_2.
        sort_by = sort_by_column

        if cls.df_1.isna().all().all() and cls.df_2.empty:
        #if cls.df_1.empty and cls.df_2.empty:
            return False
        
        if not cls.df_1.isna().all().all() and not cls.df_2.empty:
        #if not cls.df_1.empty and not cls.df_2.empty:
            return False

        if not cls.df_1.isna().all().all():
        #if not cls.df_1.empty:
            df = cls.df_1
        elif not cls.df_2.empty:
            df = cls.df_2

        df_filtered_1 = df[~df[sort_by].str.contains(r'[a-zA-Z]')]

        df_filtered_1 = df_filtered_1.sort_values(by=sort_by)
        df_filtered_1.reset_index(drop=True, inplace=True)

        df_filtered_2 = df[df[sort_by].str.contains(r'[a-zA-Z]', regex=True)]

        df_filtered_2 = df_filtered_2.sort_values(by=sort_by)
        df_filtered_2.reset_index(drop=True, inplace=True)     

        cls.df_1 = df_filtered_1
        cls.df_2 = df_filtered_2

        return df_filtered_1, df_filtered_2

    @classmethod
    def subtract(cls):  # Rużnica pomiędzy df_1 i df_2.
        df3 = pd.DataFrame()
        df3['DX'] = cls.df_2["X"] - cls.df_1["X"]

        df3['DY'] = cls.df_2["Y"] - cls.df_1["Y"]
        
        try:
            df3['DH'] = cls.df_2["H"] - cls.df_1["H"]
        except:
            df3['DH'] = ""

        df3['DL'] = (df3['DX'] ** 2 + df3['DY'] ** 2) ** 0.5

        df3['DL'] = df3['DL'].astype(float).round(2)
        df3['DX'] = df3['DX'].astype(float).round(2)
        df3['DY'] = df3['DY'].astype(float).round(2)

        if "H" in df3.columns:
            df3['DH'] = df3['DH'].astype(float).round(2)
        
        cls.df_3 = df3
        return df3
    
    @classmethod
    def castling(cls, df_name, lista=[0,1,2,3,4,5,6], df=None):
        if df is None or df.empty:
            df = getattr(cls, df_name)

        df[[0, 1, 2, 3, 4, 5, 6]] = df[lista] # order= [0, 1, 2, 3, 4, 5, 6]  # ['NR', 'X', 'Y', 'H', 'SPD', 'ISD', 'STB']

        setattr(cls, df_name, df)
        return df

    @classmethod
    def is_duplicated_old(cls, df_name=None, subset="NR", df=None):
        if df is None or df.empty:
            df = getattr(cls, df_name)

        df_duplicates = df[df.duplicated(subset, keep='first')].copy() 
        df = df.drop_duplicates(subset)
        if df_name:
            setattr(cls, df_name, df)
        return df, df_duplicates
    
    @classmethod
    def is_duplicated(cls, 
                      df_name: Optional[str] = None, 
                      subset: str = "NR", 
                      df: Optional[pd.DataFrame] = None
                      ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        if df_name is None and df is None:
            raise ValueError("Either 'df_name' or 'df' must be provided.")
        if df is None or df.empty:
            df = getattr(cls, df_name)
        
        df_duplicates = df[df.duplicated(subset, keep='first')].copy()
        df_cleaned = df.drop_duplicates(subset)
        if df_name:
            setattr(cls, df_name, df_cleaned)

        return df_cleaned, df_duplicates
    
    @classmethod
    def create_new_data(cls, przyrostek = "K"):
        try:
            df1 = cls.df_1.copy()
            df1['NR'] = df1['NR'] + przyrostek
            df1['X'] += np.random.uniform(-0.03, 0.04, size=len(df1))
            df1['X'] = df1['X'].astype(float).round(2)
            df1['Y'] += np.random.uniform(-0.03, 0.04, size=len(df1))
            df1['Y'] = df1['Y'].astype(float).round(2)
            try:
                if df1 is not None and not df1.empty and "H" in df1.columns:
                    df1['H'] += np.random.uniform(-0.03, 0.04, size=len(df1))
                    df1['H'] = df1['H'].astype(float).round(2)
            except Exception as e:
                print(e)
                pass
        except Exception as e:
            print(e)
        cls.df_2 = df1

    @classmethod
    def default(cls):
        cls.df_gml = pd.DataFrame(columns=['Działka', 'NR', 'X', 'Y', 'H', 'SPD', 'ISD', 'STB'])
        cls.df_gml_list = pd.DataFrame(columns=['Działka'])
        cls.df_memory = pd.DataFrame(columns=['NR', 'X', 'Y', 'H', "SPD", "ISD", "STB"])

        cls.df_1 = pd.DataFrame(columns=['NR', 'X', 'Y', 'H', "SPD", "ISD", "STB"])
        cls.df_1 = cls.df_1.reindex(range(5))  # cls.df_1.isna().all().all()
        cls.df_2 = pd.DataFrame(columns=['NR', 'X', 'Y', 'H', "SPD", "ISD", "STB"])
        cls.df_3 = pd.DataFrame(columns=["DX", "DY", "DH", "DL"])

    @classmethod
    def synchronize_df_1(cls):
        matching_rows = cls.df_memory[cls.df_memory['NR'].isin(cls.df_1_sort_list)]
        cls.df_1 = matching_rows.reset_index(drop=True)

    @classmethod
    def synchronize_df_2(cls):
        matching_rows = cls.df_memory[cls.df_memory['NR'].isin(cls.df_2_sort_list)]
        cls.df_2 = matching_rows.reset_index(drop=True)

    @classmethod
    def synchronize_manual(cls):
        print("Synchronizing manually...")

        merge_df = pd.concat([cls.df_1, cls.df_2], ignore_index=True)
        df_synchro = merge_df.drop_duplicates(subset="NR")

        try:
            # Synchronize df_1 with df_1_sort_list
            matching_rows1 = df_synchro[df_synchro['NR'].isin(cls.df_1_sort_list)]
            cls.df_1 = matching_rows1.reset_index(drop=True)
        except Exception as e:
            print(f"Error synchronizing df_1: {e}")

        try:
            # Synchronize df_2 with df_2_sort_list
            matching_rows2 = df_synchro[df_synchro['NR'].isin(cls.df_2_sort_list)]
            cls.df_2 = matching_rows2.reset_index(drop=True)
        except Exception as e:
            print(f"Error synchronizing df_2: {e}")

    @classmethod
    def drop_prefix_or_suffix(cls, df_name=None, columns="NR", df=None, prefix_mode=False, prefix_text=None, suffix_mode=False, suffix_text=None):
        if df is None or df.empty:
            df = getattr(cls, df_name)

        if hasattr(cls, df_name) and not df.empty:
            if prefix_mode:
                df[columns] = df[columns].str.removeprefix(prefix_text)
            if suffix_mode:
                df[columns] = df[columns].str.removesuffix(suffix_text)

            setattr(cls, df_name, df)

        return df


if __name__ == "__main__":
    path = r""

    myDataFrame.default()
    myDataFrame.read(path, 'df_1')
    myDataFrame.clean('df_1')
    myDataFrame.set_float_and_name('df_1')

    #myDataFrame.sort('df_1', 0)

    #myDataFrame.create_new_data()
    #myDataFrame.subtract()
    
    #print(myDataFrame.df_1)
    #print('')
    #print(myDataFrame.df_2)
    #print('')
    #print(myDataFrame.df_3)
    #print('')

    #myDataFrame.drop_H_in_df("df_all")
    #myDataFrame.drop_columns_in_df("df_all", "H", "DH")
    #myDataFrame.drop_columns_in_df("df_all", "SPD", "ISD", "STB")

    myDataFrame.display_data()
    print(myDataFrame.df_all)