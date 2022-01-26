import pandas as pd

def read_toollistFile():
    # get toollist & footprint
    toollist_df = pd.read_excel("tts_toollist_new.xlsx", sheet_name="toollist")
    fooprint_df = pd.read_excel("tts_toollist_new.xlsx", sheet_name="footprint")
    map_result = pd.merge(toollist_df, fooprint_df, how='left', on=['WS'])
    #print(map_result) 
    return map_result

def read_baylistFile():
    baylist_df = pd.read_excel("tts_toollist_new.xlsx", sheet_name="baylist")
    #print(baylist_df)  
    return baylist_df

def read_existToollistFile():
    existToollist_df = pd.read_excel("tts_toollist_new.xlsx", sheet_name="toollist_exist")
    fooprint_df = pd.read_excel("tts_toollist_new.xlsx", sheet_name="footprint")
    map_result = pd.merge(existToollist_df, fooprint_df, how='left', on=['WS'])
    #print(existToollist_df)  
    return map_result

def read_relation_matrix():
    relation_matrix = pd.read_excel("tts_toollist_new.xlsx", sheet_name="relation_matrix")
    #print(baylist_df)
    return relation_matrix

def read_limit_matrix():
    limit_matrix = pd.read_excel("tts_toollist_new.xlsx", sheet_name="limit_matrix")
    #print(baylist_df)
    return limit_matrix

def read_A12_transfer_loading():
    a1a2_trans_matrix = pd.read_excel("A1A2_relation_score.xlsx", sheet_name="Sheet1")
    a1a2_trans_matrix.set_index("WSG" , inplace=True)
    #print(baylist_df)
    return a1a2_trans_matrix