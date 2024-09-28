#!/usr/bin/env python3
"""Script of ena2json.py is to create objects

___author___ = "woollard@ebi.ac.uk"
___start_date___ = 2024-09-11
__docformat___ = 'reStructuredText'
chmod a+x ena2json.py
"""


import os
import argparse
from ena_portal_api import ena_portal_api_call_basic
import logging
from eDNA_utilities import logger



def display_ena_objects():
    """"""
    get_results_objects_url = 'https://www.ebi.ac.uk/ena/portal/api/results?dataPortal=ena&format=json'
    out = ena_portal_api_call_basic(get_results_objects_url)
    logger.info(f"out={out}")


def main():
    display_ena_objects()

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()
