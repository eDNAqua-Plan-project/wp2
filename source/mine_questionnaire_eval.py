#!/usr/bin/env python3
"""Script of mine_bioinfomatics_eval.py is to mine the bioinfomatics evaluation spreadsheet file

___author___ = "woollard@ebi.ac.uk"
___start_date___ = 2024-06-18
__docformat___ = 'reStructuredText'

"""

import os
import pandas as pd
import sys
import logging
import re
import numpy as np
import json
import pprint
import plotly.express as px
from collections import Counter
import networkx as nx
import matplotlib.pyplot as plt

# from pygments.lexers import go

from eDNA_utilities import logger, my_coloredFormatter, coloredlogs,\
    list_freq_pie, get_lists_from_df_column, un_split_list,\
    get_duplicates_in_list, clean_list_replace_nan, plot_countries,\
    plot_sunburst, obj_print_and_display_md


pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)


def get_dataframe():
    ss_url = (r'https://docs.google.com/spreadsheets/d/1bll3zzMJHv0gbe2xH4h7a9wTCMy3INtV/edit?usp=sharing&ouid'
              r'=112917721394157806879&rtpof=true&sd=true')
    sheet_id = '1bll3zzMJHv0gbe2xH4h7a9wTCMy3INtV'
    ss_url = f'https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv'
    ss_url = 'eDNA_Survey-Data.xlsx'
    logger.info(f'Mined questionnaire evaluation spreadsheet: {ss_url}')
    # df = pd.read_csv(ss_url)
    df = pd.read_excel(ss_url)

    col_list = list(df.columns)
    logger.info(f"\n{col_list}")

    def filter_not_raw(value):

        if value.startswith("Raw") or value == "NoRaw":
            return False
        else:
            return True

    logger.info("-------------------------------------------")
    logger.info(f"len of col_list={len(col_list)}")
    not_raw_list = list(filter(filter_not_raw, col_list))
    # logger.info(f"\n{not_raw_list}")
    df = df[not_raw_list]


    return df


def analyse_projects(df):
    project_list = get_lists_from_df_column(df, 'Project')
    print(json.dumps(Counter(project_list)))



def analyse_location(df):
    logger.info("Analysing location<------------------------------------------------------------")
    location_list = get_lists_from_df_column(df, 'Location')
    tmp_list = sorted(set(location_list))
    # txt = "|".join(tmp_list).replace('_', '|').replace('.', '|').replace(' ', '|')
    # tmp_list = sorted(set(txt.split('|')))
    # logger.info(f"\nTMPLIST--------------{tmp_list}")
    #
    # def remove_features(my_list): features_pat = re.compile(
    # r'Mountains|Lagoon|River|sea|^sur|^shelf|^fresh|lake|gulf|ocean|island|Eco|ridge|foreland|atlantic|pacific',
    # flags=re.IGNORECASE) new_list = [] for value in my_list: if re.match(features_pat, value): logger.info(
    # f"\tremoving--->{value}") continue else: new_list.append(value)
    #
    #     return new_list
    # tmp_list = remove_features(tmp_list)
    logger.info(f"{location_list}")
    europe_pats = re.compile(
        r'Oleron|Danube|deVeys|Douro|English|Europe|Ferrol|Finland|France|French|Ferrol|Georgia|Germany|Greece|Heraklion|Léman|Iberia'
        r'|Italy|Karpathos|Kristineberg|Léman|Malta|Mediterranean|Minho|Naples|Netherlands|Norway|Norwegian|OsloFjord'
        r'|Poland|Portugal|Sicily|Slovak|Slovakia|Spain|StAbbs|Svalbard|Sweden|Tatra|Thau|Thessaloniki|UK|Wallonia'
        r'|Bay_Biscay|Gulf_Naples|Cardigan|Minho|Svalbard|OsloFjord|Heraklion|Oleron|StAbbs',
        flags = re.IGNORECASE)
    special_cases_pats = re.compile( r'UK|English|Slovak|StAbbs|Tatra|Douro|OsloFjord|Ferrol|deVeys|Léman|Karpathos|Kristineberg|Oleron|StAbbs|Thau|Wallonia|Heraklion|Thessaloniki|EnglishChannel|Mediterranean|Norwegian_shelf|Bay_Biscay|Gulf_Naples|Cardigan|Minho_River|ArcticOcean_Svalbard', flags = re.IGNORECASE)
    special_cases_dict = {
        'Kristineberg': 'Sweden',
        'Minho_River': "Portugal",
        'Heraklion': "Greece",
        'Thessaloniki': "Greece",
        'Karpathos': "Greece",
        'Wallonia': "Belgium",
        'Thau': "France",
        "Tatra": "Poland", # could be Slovakia
        'Léman': "Switzerland",
        'Slovak': "Slovakia",
        'Douro': "Portugal",
        'Ferrol': "Spain",
        'Oleron': "France",
        'StAbbs': 'United Kingdom',
        'UK': 'United Kingdom',
        'ArcticOcean_Svalbard': "sea(European)",
        'Bay_Biscay': "sea(European)",
        'Norwegian_shelf': "sea(European)",
        'EnglishChannel': "sea(European)",
        'English': "sea(European)",
        'Cardigan': "sea(European)",
        'Mediterranean': "sea(European)",
        'OsloFjord': "sea(European)",
        'deVeys': "sea(European)",
        'Gulf_Naples': "sea(European)"

        }
    europe_list = []
    non_europe_list = []
    for location in location_list:
        match = europe_pats.search(location)
        if match is not None:
            # logger.info(f"match found match={match} in location={location}")
            smatch = special_cases_pats.search(location)
            if smatch is not None:
                logger.info(f"match found smatch={smatch.group(0)} in location={location}")
                if smatch.group(0) in special_cases_dict:
                    europe_list.append(special_cases_dict[smatch.group(0)])
                else:
                    europe_list.append(smatch.group(0))
                # sys.exit()
            else:
                europe_list.append(match.group(0))
        else:
            non_europe_list.append(location)
    print(f"Europe: {len(europe_list)} non-europe: {len(non_europe_list)}")

    my_euro_counter = Counter(europe_list)
    pprint.pprint(my_euro_counter)

    df = pd.DataFrame(my_euro_counter.items(), columns = ['country', 'count']).sort_values(by='count', ascending=False)
    obj_print_and_display_md(df, "survey_country")
    plot_countries(dict(my_euro_counter),'europe', "Reported eDNA related DB location in Europe Frequencies", "../images/survey_europe_countries.png")


def analyse_europe(df):
    location_list = get_lists_from_df_column(df, 'Europe')



def analyse_environment(df):
        label = 'Environment'
        location_list = get_lists_from_df_column(df, label)
        # logger.info(f"\n{location_list}")
        my_title = "Survey: Aquatic Environments"
        list_freq_pie(location_list,'Environment', my_title, "../images/survey_europe_environments.png" )


        # main_aquatic_re = re.compile(r'marine|freshwater|transitional|groundwater', re.IGNORECASE)
        # def map2main_aquatic_type(value):
        #     match = main_aquatic_re.search(value)
        #     if match is not None:
        #         return match.group(0)
        #     else:
        #         return None
        #
        # label = 'Substrate.Env'
        #
        # tmp_df = df[['Substrate', label]]
        # tmp_df['substrate_explode'] = tmp_df['Substrate'] .str.split(';')
        # logger.info(tmp_df.head(10))
        # tmp_df = tmp_df.explode('substrate_explode')
        # logger.info(tmp_df.head(3).to_markdown())
        #
        # tmp_df['main_aquatic_type'] = tmp_df[label].apply(map2main_aquatic_type)
        # path_list = ['main_aquatic_type', 'Substrate']
        # value_field = 'count'
        # plot_df = df.groupby(path_list).size().reset_index(name=value_field)
        # logger.info(f"\n{plot_df.to_string(index=False)}")
        #
        # plot_sunburst(plot_df, "Survey: " + label + " Sunburst", path_list, value_field, "../images/Survey_" + label + "_Sunburst.png")


        logger.info(f"\n{df.columns}")

        label = 'Substrate_Simplified'
        location_list = get_lists_from_df_column(df, label)
        # logger.info(f"\n{location_list}")
        my_title = "Survey: Aquatic Environments - " + label
        list_freq_pie(location_list, 'Substrate_Simplified', my_title, "../images/survey_substrate_simplified_environments.png")

        label = 'Substrate.Env'
        location_list = get_lists_from_df_column(df, label)
        # logger.info(f"\n{location_list}")
        my_title = "Survey: Aquatic - " + label
        list_freq_pie(location_list, label, my_title, "../images/survey_" + label + ".png")

def get_barcode2tax():
    # from Markers proposed to include in searching DNA barcode repositories
    get_barcode2tax = {
        "12S_rRNA": "fish, amphibians",
        "16S_rRNA": "bacteria",
        "18S_rRNA": "nematodes and many microeukaryota",
        "23S_rRNA": "microalgae / algae",
        "MATK": "plants",
        "matK": "plants",
        "28S_rRNA": "protists",
        "COX1": "invertebrates, vertebrates",
        "Cytb": "fish",
        "ITS1-5.8S-ITS2": "fungi",
        "ITS": "fungi",
        "ITS1": "fungi",
        "ITS2": "fungi",
        "LSU": "fungi",
        "Metagenome": "",
        "Metatranscriptome": "",
        "TROLL": "",
        "anaC": "",
        "anaF": "",
        "cyrA": "",
        "cyrB": "",
        "cyrC": "",
        "cyrJ": "",
        "mcyA": "",
        "mcyB": "",
        "mcyC": "",
        "mcyD": "",
        "mcyE": "",
        "mcyF": "",
        "mcyG": "",
        "mtDNA_ControlRegion": "",
        "pca": "",
        "rbcl": "diatoms/plants",
        "rbcL": "diatoms/plants",
        "sxtA": "",
        "sxtG": "",
        "sxtH": "",
        "sxtI": ""
    }
    return get_barcode2tax

def analyse_tax_from_barcode_list(barcode_list):
    logger.info(f"inside barcode_list")

    barcode_dict = get_barcode2tax()
    logger.info(f"inside barcode_dict{barcode_dict}<------------------------------------")
    label = "barcode"
    barcode_counter = Counter(barcode_list)
    # logger.info(f"inside barcode_counter{barcode_counter}")
    my_df = pd.DataFrame(barcode_counter.items(),
                         columns = [label, 'count']).sort_values(by = 'count', ascending = False)
    logger.info(f"\n{my_df.to_string(index=False)}")
    my_df['barcode_species'] = my_df['barcode'].map(barcode_dict)
    obj_print_and_display_md(my_df,"survey_barcode_species")

def analyse_barcode(df):
    label = 'Markers_Simplified'
    location_list = get_lists_from_df_column(df, label)
    # logger.info(f"\n{location_list}")
    my_title = "Survey: Aquatic :" + label
    list_freq_pie(location_list, label, my_title, "../images/survey_" + label + ".png")
    analyse_tax_from_barcode_list(location_list)

def df_group_count(df, label):
    return df.groupby(label).size().reset_index(name = 'count').sort_values(by = ['count'], ascending = False)

def analyse_sequencing_technologies(df):
    label = 'Seq_Platform'
    location_list = get_lists_from_df_column(df, label)
    logger.info(f"location_list=\n{location_list}")
    my_title = "Survey: Aquatic :" + label
    my_dict = dict(Counter(location_list))
    df_group = pd.DataFrame(my_dict.items(), columns=['instrument', 'count'])
    obj_print_and_display_md(df_group, label)
    list_freq_pie(location_list, label, my_title, "../images/survey_" + label + ".png")


def create_weighted_graph(paths):
    G = nx.Graph()

    for path in paths:
        nodes = path.split(';')
        for i in range(len(nodes) - 1):
            node1 = nodes[i]
            node2 = nodes[i + 1]
            weight = 1  # Each connection counts as 1
            if G.has_edge(node1, node2):
                G[node1][node2]['weight'] += weight
            else:
                G.add_edge(node1, node2, weight = weight)

    return G


def visualize_graph(G, my_title, plotfile):
    pos = nx.spring_layout(G, seed = 42, k =3)  # For consistent layout
    edge_labels = nx.get_edge_attributes(G, 'weight')

    # Calculate edge widths based on weights
    edge_widths = [G[u][v]['weight'] for u, v in G.edges()]

    plt.figure(figsize = (12, 8))
    plt.title(my_title)
    nx.draw(G, pos, with_labels = True, node_color = 'skyblue', node_size = 3000, font_color='green', font_size = 10, font_weight = 'bold',
            width = edge_widths, edge_color="lightgreen")
    nx.draw_networkx_edge_labels(G, pos, edge_labels = edge_labels, font_color = 'red')

    logger.info("Visualizing graph to " + plotfile)
    plt.savefig(plotfile)

def freq_list_2_print(my_list, label):
    my_dict = dict(Counter(my_list))
    df_group = pd.DataFrame(my_dict.items(), columns = [label, 'count'])
    df_group = df_group.sort_values(by = ['count'], ascending = False)
    obj_print_and_display_md(df_group, label)

def analyse_repository(df):
    label = 'ProcessedRepository_Simplified'
    my_list = get_lists_from_df_column(df, label)
    my_title = "Survey: Aquatic :" + label

    logger.info(f"\n{my_list} type={type(my_list)}")
    my_unif_list = []
    for key in my_list:
        logger.info(f"\n{key}")
        if key.startswith("NCBI"):
            new_key = "NCBI"
        elif key.startswith("EBI"):
            new_key = "ENA"
        else:
            new_key = key
        my_unif_list.append(new_key)
    freq_list_2_print(my_unif_list, "survey_" + label)

    # logger.info(f"\n{my_unif_list}")


    list_freq_pie(my_unif_list, label, my_title, "../images/survey_" + label + ".png")

def analyse_processed_metadata(df):
    label = 'Processed_Metadata'
    location_list = get_lists_from_df_column(df, label)

    freq_list_2_print(location_list, "survey_" + label)
    my_title = "Survey: Aquatic :" + label
    list_freq_pie(location_list, label, my_title, "../images/survey_" + label + ".png")

    #print(df[label].value_counts())
    my_df = df.groupby(label).size().reset_index(name="count").sort_values(by = 'count', ascending = False)
    print(my_df.head())
    logger.info(f"{my_df}")

    my_list = df[label].to_list()
    org_len = len(my_list)
    my_list = [x for x in my_list if str(x) != 'nan']
    clean_len = len(my_list)
    print(f"Total db collections = {org_len}, total collections with metadata types recorded = {clean_len}, collections without = {org_len - clean_len}")
    logger.debug(my_list)
    g = create_weighted_graph(my_list)
    print(g)
    visualize_graph(g, "Figure: survey \"" + label + "\" frequency co-occurrence graph", "../images/survey_" + label + "_graph.png")

    label = 'Processed_MetadataStandard'
    location_list = get_lists_from_df_column(df, label)
    my_title = "Survey: Aquatic :" + label

    label = 'Processed_MetadataStandard_Structure'
    my_list = df[label].to_list()
    orig_len = len(my_list)
    my_list = clean_list_replace_nan(my_list)
    logger.info(f"orig len = {orig_len} cleaned len = {len(my_list)}")
    logger.info(my_list)
    tmp_df = df.groupby(label).size().reset_index(name="count").sort_values(by = 'count', ascending = False)
    obj_print_and_display_md(tmp_df, label)

    my_title = "Survey: Aquatic :" + label
    list_freq_pie(my_list, label, my_title, "../images/survey_" + label + ".png")
    sys.exit(label)

def analyse_read_runs(df):
    label = 'NReads_Simplified'
    my_list = get_lists_from_df_column(df, label)
    my_title = "Survey: Aquatic :" + label
    list_freq_pie(my_list, label, my_title, "../images/survey_" + label + ".png")
    freq_list_2_print(my_list, "survey_" + label)

def analyse_answer(df):
    answer_list = get_lists_from_df_column(df, 'Answer')
    df['row_num'] = range(len(df))
    logger.info(f"\n{df.head(3)}")


    tmp_df = df[['row_num','Answer', 'Project']].set_index(['row_num','Answer']).drop_duplicates()

    answer_df = tmp_df.stack().str.split(';', expand=True).stack().unstack(-2).reset_index(-1, drop=True).reset_index()
    logger.info(f"\n{answer_df}")

    print(f"Total questionnaire submitters: {len(df)}, and total dbs: {len(answer_df)}")
    print(f"mean # {len(answer_df)/len(df)}   median # of dbs submitted.by submitter: {answer_df.groupby('Answer').count().apply(np.median)}")


def mine_questionnaire_eval():
    """"""
    df = get_dataframe()
    row_vals_2_drop = ['[NO ANSWER]']
    df = df[~df.Project.isin(row_vals_2_drop)]
    logger.info(f"\n{list(df.columns)}")
    proj_list = df['Project'].to_list()
    proj_list = un_split_list(proj_list)
    print(f"This many questionnaire evaluations were done: {len(df)} covering {len(proj_list)} projects")
    analyse_answer(df)
    analyse_projects(df)
    analyse_location(df)
    analyse_europe(df)
    analyse_environment(df)
    analyse_barcode(df)
    analyse_sequencing_technologies(df)
    analyse_read_runs(df)
    analyse_processed_metadata(df)
    analyse_repository(df)



def main():
    print("FFS")
    mine_questionnaire_eval()


if __name__ == '__main__':
    logging.basicConfig(level = logging.INFO)

    coloredlogs.install(logger = logger)
    logger.propagate = False
    ch = logging.StreamHandler(stream = sys.stdout)
    ch.setFormatter(fmt = my_coloredFormatter)
    logger.addHandler(hdlr = ch)
    logger.setLevel(level = logging.INFO)

    main()
