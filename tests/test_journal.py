import os
import os.path

import pytest

from tempfile import TemporaryDirectory

from rednotebook.journal import Journal
import argparse
from argparse import Namespace

def test_journal_init(mocker):
    mocker.patch('gi.repository.GObject.timeout_add_seconds')
    mocker.patch('gi.repository.GObject.idle_add')
    mocker.patch('rednotebook.journal.MainWindow')
    #mocker.patch('rednotebook.info.get_commandline_parser')
    mocker.patch('argparse.ArgumentParser.parse_args')
    argparse.ArgumentParser.parse_args.return_value = Namespace(journal=None, start_date=None)
    mocker.patch('rednotebook.journal.Journal.open_journal')
    j=Journal()
