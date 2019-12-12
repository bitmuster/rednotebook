import os
import os.path

import pytest
import argparse
from argparse import Namespace
from tempfile import TemporaryDirectory

import rednotebook
from rednotebook.data import Month
from rednotebook.journal import Journal
from rednotebook.storage_separate import StorageSeparateFiles
from rednotebook.gui.categories import CategoriesTreeView

def disable_test_journal_init(mocker):
    """Disabled: It seemss like something wild is going on in the categories.py
    properties calls, magic mocks spread everywhere and in the end everything goes wrong
    To run this test some refractoring will be necessary
    """
    with TemporaryDirectory() as td:
        mocker.patch('rednotebook.journal.MainWindow')
        mocker.patch('rednotebook.gui.categories.CategoriesTreeView')
        rednotebook.gui.categories.CategoriesTreeView.get_day_content.return_value = {'text': 'gamble'}
        mocker.patch('argparse.ArgumentParser.parse_args')
        sample_months = {
            '2018-07': Month(2018, 7, {2: {'text': 'sample'}}),
            '2018-06': Month(2018, 6, {3: {'text': 'simple'}}),
        }
        storage=StorageSeparateFiles()
        storage.save_months_to_disk(sample_months, td, saveas=True)
        argparse.ArgumentParser.parse_args.return_value = Namespace(journal=td, start_date=None)
        #mocker.patch('rednotebook.journal.Journal.open_journal')
        j=Journal()
