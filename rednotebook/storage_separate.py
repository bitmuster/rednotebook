# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------
# Copyright (c) 2019 Michael Abel
#
# RedNotebook is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# RedNotebook is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with RedNotebook; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
# -----------------------------------------------------------------------

import codecs
import logging
import os
import re
import shutil
import stat
import sys

from rednotebook.data import Month

from rednotebook.storage import Storage, FsStorage

class StorageSeparateFiles(Storage):
    """Provides the backend for a journal storage within separate files.
    Daily records are stored in a folder tree consisting of
    <year>/<month>/day-<num>.md
    Like: 2018/01/day-15.md
    In addition, a tree of notes shall be stored in a sub-folder named "Tree".
    Like: Tree/<note-name>.md
    Note: At current, subfolders are not supported yet.
    """

    def get_journal_files(self, data_dir):
        # Make check_journal_dir in menu.py happy this seems to be the only
        # import check up to now
        return [None]

    def write_file(self, day_num, day, path):
        os.makedirs(path, exist_ok=True)
        pattern = "day-%02i.md"
        wrote = False
        if day.text:
            try:
                with open(os.path.join(path, pattern%day_num), 'w') as f:
                    f.write(day.text)
                    wrote = True
            except OSError as err:
                print ("Error while writing to file: {0}".format(err))
                raise OSError
        return wrote

    def save_months_to_disk(self, months, journal_dir,
                            exit_imminent=False, saveas=False):
        """Save the day-based part to disk"""

        if not isinstance(months, dict):
            raise SystemError
        if not os.path.exists(journal_dir):
            raise SystemError

        wrote = False

        for keym, month in months.items():
            if month.edited or saveas:
                for keyd, day in month.days.items():

                    # keym e.g. '2018-01'
                    assert int(keym[:-3]) == month.year_number
                    assert int(keym[-2:]) == month.month_number
                    #print( '\t' + day.text )
                    path = os.path.join (journal_dir, "%02i"%month.year_number,
                                         "%02i"%month.month_number )
                    #print('Path:', path)
                    wrote = self.write_file(keyd, day, path)
        return wrote

    def load_month_from_disk(self, year, month, path):
        """"Load all day files from a month directory into a Month object
        year: integer with year
        month: integer with month
        path: path to folder
        """

        day_exp = re.compile('^day-(\d{2}).md$') # e.g. day-05.md
        content = {}

        for day in os.scandir(path):
            match = day_exp.match(day.name)
            if match :
                day_number = int(match.groups()[0])
                if day_number >= 1 and day_number <= 31 :
                    d = ''
                    with open(day.path, 'r') as f:
                        d = f.read()
                    content[day_number] = {'text':d}
                else:
                    pass # Ignore others
            else:
                pass # Ignore others

        mon = Month(year, month, content,
                    os.path.getmtime(month))
        return mon

    def load_all_months_from_disk(self, data_dir):
        """
        Load all day files and return a directory mapping year-month values
        to month objects.
        """

        if not os.path.exists( data_dir ):
            raise SystemError('Folder {0} not found'.format(data_dir))

        logging.debug('Starting to load files in dir "%s"' % data_dir)
        months = {}
        year_exp = re.compile('^\d{4}$')
        for year in os.scandir(data_dir):
            #print('Year', year.name)
            if year.is_dir() and year_exp.match(year.name):
                for month in os.scandir(year.path):
                    mon = self.load_month_from_disk( int(year.name),
                                        int(month.name), month.path)
                    months[self.format_year_and_month( int(year.name),
                            int(month.name))] = mon

        logging.debug('Finished loading files in dir "%s"' % data_dir)
        return months

    def load_all_years_from_disk(self):
        pass
    def load_all_other_Stuff_from_disk(self):
        pass

    def save_tree_to_disk(self, path, tree):
        """Save a structured note tree to disk"""

        basedir = os.path.join(path, 'Tree')
        os.makedirs(basedir, exist_ok=True)
        for k in tree.keys():
            if not isinstance(tree[k], str):
                raise SystemError
            with open( os.path.join( basedir, k+'.md'), 'w') as f:
                f.write(tree[k])

    def load_tree_from_disk(self, dir):
        """Load a structured note tree from disk"""

        basedir = os.path.join( dir , 'Tree')
        ret = {}
        md_exp = re.compile('.+\.md$')
        try:
            for element in os.scandir( basedir ):
                with open( element.path ) as f:
                    if md_exp.match(element.name):
                        ret[element.name[:-3]] = f.read()
                    else:
                        raise(SystemError)
        except:
            #pass
            raise(SystemError)
        return ret
