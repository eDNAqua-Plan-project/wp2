#!/usr/bin/env python3
"""Script of mine_bioinfomatics_eval.py is to mine the bioinfomatics evaluation spreadsheet file

___author___ = "woollard@ebi.ac.uk"
___start_date___ = 2024-06-18
__docformat___ = 'reStructuredText'

"""

import logging
import sys
from collections import defaultdict
import pandas as pd
from eDNA_utilities import logger, my_coloredFormatter, coloredlogs, mv_df_col2front

pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)


def clean_df(df):
    logger.info(f"\n{df.head()}")
    logger.info(f"\n{df}")
    logger.info(f"\n{df.dtypes}")

    df['ID'] = df['ID'].fillna(0).astype(int, errors = 'ignore')

    type_list = df['Type'].to_list()
    field_list = df['Name'].to_list()

    data_source_names = get_data_source_names(df)
    # for source in data_source_names:
    #     df[source] = df[source].astype(str, errors='ignore')

    # logger.info(f"\n{df}")
    # sys.exit()

    return df


def get_data_source_names(df):
    exclude_list = ['field_category']
    data_source_names = []
    col_num = 0
    for each_col in df.columns:
        if col_num > 5 and each_col not in exclude_list:
            data_source_names.append(each_col)
        # elif col_num > 2:
        #     logger.info(f"\n{each_col} > 2")
        #     df[each_col] = df[each_col].astype(str)
        col_num += 1

    logger.info(f"\n{data_source_names}")
    for source in data_source_names:
        logger.info(f"\n{source}")
        # for field

    logger.info(f"\n{df.dtypes}")
    return data_source_names


def add_metadata_category(df):
    logger.info(f"\n{df['Name'].to_list()}")
    category_dict = {
        'data_metadata_link': 'metadata',
        'record_URL': 'data_access',
        'metadata_record_URL': 'metadata',
        'paper_DOI_number': 'publication',
        'paper_link': 'publication',
        'DB_name': 'db_profile',
        'DB_use_index': 'db_profile',
        'DB_using community': 'db_profile',
        'number of records': 'db_size',
        'number of records (scaled)': 'db_size',
        'web_interface': 'data_access',
        'API': 'data_access',
        'application': 'data_access',
        'GPS_coordinates_available': 'sample_details',
        'data_export_format': 'data_format',
        'metadata_export_format': 'metadata_format',
        'env_data_contains': 'db_profile',
        'barcode_taxonomy_confidence': 'barcode',
        'annually_updated': 'db_profile',
        'data_paper_location': 'publication',
        'sequences_processed': 'sequence_related',
        'DB_standard_consistent': 'metadata',
        'DB_mandatory_metadata': 'metadata',
        'data_file_format': 'data_format',
        'metadata_file_format': 'metadata_format',
        'metadata_file_schema': 'metadata',
        'DB_active': 'db_profile',
        'DB_curation': 'db_profile',
        'sample_collection': 'sample_details',
        'DNA_extraction': 'experiment_metadata',
        'sequence_methodology': 'experiment_metadata',
        'sequencing_strategy': 'experiment_metadata',
        'analysis_workflow': 'experiment_metadata',
        'directly_uploaded': 'sequence_related',
        'barcode_name': 'barcode',
        'barcode_certain': 'barcode',
        'taxonomy_origin': 'taxonomic',
        'taxonomy_URL': 'taxonomic',
        'taxonomically_identified': 'taxonomic',
        'taxonomical_name': 'taxonomic',
        'taxonomy_linking': 'taxonomic',
        'Primary/Secondary': 'sequence_related'
    }
    df["field_category"] = df['Name'].map(category_dict)
    return df


def get_metadata_category(df):
    tmp_df = df[['Name', 'field_category']].set_index('Name')
    # logger.info(f"\n{df['Name'].value_counts()}")
    # logger.info(f"Duplicated values for Name= {df.duplicated(subset=['Name'])}")
    tmp_metadata_category_dict = tmp_df.to_dict("index")
    # print(json.dumps(tmp_metadata_category_dict, indent = 4))
    metadata_category_dict = {}
    for value in tmp_metadata_category_dict:
        field_cat = tmp_metadata_category_dict[value]['field_category']
        if field_cat in metadata_category_dict:
            metadata_category_dict[field_cat].append(value)
        else:
            metadata_category_dict[field_cat] = [value]
    # print(json.dumps(tmp_metadata_category_dict, indent = 4))
    return metadata_category_dict


def analyse_by_category(df):
    logger.info(f"in analyse_by_category")
    # logger.info(f"\n{df}")
    metadata_category_dict = get_metadata_category(df)

    data_source_names = get_data_source_names(df)
    logger.info(f"\n{data_source_names} type={type(data_source_names)}")

    keep_col_list = data_source_names
    keep_col_list.append('Name')
    keep_col_list.append("field_category")
    logger.info(f"\n{keep_col_list}")
    logger.info(f"\n{df.columns}")
    logger.info(f"\n{df.dtypes}")

    tmp_df = df[keep_col_list].sort_values(by = ['field_category', 'Name'], ascending = True)
    tmp_df = mv_df_col2front(tmp_df, 'Name')
    tmp_df = mv_df_col2front(tmp_df, 'field_category')

    print(f"my categories: {list(metadata_category_dict.keys())}")
    for cat in metadata_category_dict:
        print(f"{cat}")
        cat_members = '\n\t'.join(metadata_category_dict[cat])
        print(f"\t{cat_members}\n")

    completed_cats = ['barcode', 'taxonomic', 'experiment_metadata', 'sequence_related', 'db_profile', 'db_size',\
                      'sample_details', 'data_format', 'data_access', 'publication', 'metadata_format', 'metadata']
    completed_cats = []
    for cat in metadata_category_dict:
        if cat in completed_cats:
            continue
        logger.info(f"\n{cat} type={type(cat)}<-------------------------------------")
        print(f"eDNA Inventory: {cat} Category\n")
        vtmp_df = tmp_df.loc[tmp_df.field_category == cat].copy()
        # logger.info(f"\n{vtmp_df.head(1)}")
        # logger.info(f"\n{vtmp_df.columns}")
        # logger.info(f"\n{vtmp_df.Name}")
        vtmp_df['new_index'] = vtmp_df['Name']
        vtmp_df = vtmp_df.set_index('new_index')
        # print("df_transposed---------------------------------------------------------")
        df_transposed_df = vtmp_df.transpose(copy=False)
        df_transposed_df = df_transposed_df.drop('Name')
        df_transposed_df = df_transposed_df.drop('field_category')
        # logger.info(f"head3=\n{df_transposed_df.head(5).to_markdown()}")
        my_columns = df_transposed_df.columns.tolist()
        # logger.info(f"\n{my_columns}")
        # for my_column in my_columns:
        #   print(f"{my_column}++++++++++++++++")
        #   print(df_transposed_df[my_column].to_markdown())

        print(df_transposed_df.to_markdown())
        #logger.info(f"\n{vtmp_df.to_markdown()}")
        logger.info(f"\n------------------------------------------------------------------")
        # sys.exit()

    return df


def mine_bioinfomatics_eval():
    """"""
    ss_url = 'Databases.xlsx'
    sheet_name = 'eDNA'
    # ss_url = r'https://docs.google.com/spreadsheets/d/1yppKMagcIakPDY4RpeOkwYW1EYJ28t0LqRrj37x6oss/edit?usp=sharing'

    # sheet_id = '1yppKMagcIakPDY4RpeOkwYW1EYJ28t0LqRrj37x6oss'
    # ss_url = f'https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}'
    # ss_url = f'https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={sheet_name}'

    # logger.info(f'Mined bioinfomatics evaluation spreadsheet, sheet=eDNA file: {ss_url}')
    # df = pd.read_csv(ss_url, dtype=str, keep_default_na=False)
    # The above almost but not quite worked, as the giz method automatically tried to work out dtype's
    # e.g. tried to change many strings to boolean, which we wanted to keeps as text...
    db_list = ['ENA', 'DDBJ', 'NCBI GenBank', 'OBIS', 'GBIF', 'EukBank', 'Mitofish']
    my_dict = {}
    for db in db_list:
        my_dict[db] = str
    logger.info(f"\n{my_dict}")
    types = defaultdict(str)

    df = pd.read_excel(ss_url, sheet_name = sheet_name)
    df = df.head(42)   #´gets rid of empty rows
    # logger.info(f"\n{df.head(3)}")
    # sys.exit()
    df = clean_df(df)
    df = add_metadata_category(df)
    df = analyse_by_category(df)


def main():
    print("FFS")
    mine_bioinfomatics_eval()


if __name__ == '__main__':
    logging.basicConfig(level = logging.INFO)

    coloredlogs.install(logger = logger)
    logger.propagate = False
    ch = logging.StreamHandler(stream = sys.stdout)
    ch.setFormatter(fmt = my_coloredFormatter)
    logger.addHandler(hdlr = ch)
    logger.setLevel(level = logging.INFO)

    main()
