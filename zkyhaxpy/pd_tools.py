import pandas as pd
from IPython.display import display, HTML, display_html

def auto_adjust():
    '''
    Set column width = 100
    Max displayed rows = 100
    Max displayed columns = 100
	'''
    set_colwidth(100)
    pd.options.display.max_rows = 100
    pd.options.display.max_columns = 100


def display_html(df):
    '''
    display a dataframe as html table
    '''
    display(HTML(df.to_html()))


def inc_colwidth(inc_colwidth=20,target_colwidth=None):
    '''
    Increase column width of pandas dataframe display

    Return : None

    '''
    if target_colwidth == None:
        curr_max_colwidth = pd.get_option("display.max_colwidth") 
        new_max_colwidth = curr_max_colwidth + inc_colwidth
        pd.set_option('max_colwidth', new_max_colwidth)
    else:
        pd.set_option('max_colwidth', target_colwidth)

    print(f'Current max column width = {pd.get_option("display.max_colwidth")}')


def dec_colwidth(dec_colwidth=20,target_colwidth=None):
    '''
    Decrease column width of pandas dataframe display
    
    Return : None
    '''
    if target_colwidth == None:
        curr_max_colwidth = pd.get_option("display.max_colwidth") 
        new_max_colwidth = curr_max_colwidth - dec_colwidth
        pd.set_option('max_colwidth', new_max_colwidth)
    else:
        pd.set_option('max_colwidth', target_colwidth)   

    print(f'Current max column width = {pd.get_option("display.max_colwidth")}')


def set_colwidth(target_colwidth=100):
    '''
    Decrease column width of pandas dataframe display
    
    Return : None
    '''

    pd.set_option('max_colwidth', target_colwidth)


def curr_colwidth():
    '''
    Decrease column width of pandas dataframe display
    
    Return : None
    '''

    print(f'Current max column width = {pd.get_option("display.max_colwidth")}')
    
    
    
def read_parquets(list_file_path, columns='all'):
    '''

    Read multiple parquet files of the same template into a single pandas dataframe.

	'''
    
    list_df = []
    for file_path in list_file_path:
        if columns=='all':
            list_df.append(pd.read_parquet(file_path))
        else:
            list_df.append(pd.read_parquet(file_path, columns=columns))
        
    df = pd.concat(list_df)
    
    return df