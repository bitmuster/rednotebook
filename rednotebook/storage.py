# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------
# Copyright (c) 2009  Jendrik Seipp
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


try:
    import yaml
except ImportError:
    logging.error('PyYAML not found. Please install it (python3-yaml).')
    sys.exit(1)

try:
    from yaml import CLoader as Loader
    from yaml import CSafeDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper
    logging.info('Using pyyaml for loading and dumping')

from rednotebook.data import Month

class Storage():

    def format_year_and_month(self, year, month):
        return '%04d-%02d' % (year, month)

class FsStorage(Storage):

    def get_journal_files(self, data_dir):
        # Format: 2010-05.txt
        date_exp = re.compile(r'(\d{4})-(\d{2})\.txt$')

        for file in sorted(os.listdir(data_dir)):
            match = date_exp.match(file)
            if match:
                year = int(match.group(1))
                month = int(match.group(2))
                assert month in range(1, 12 + 1)
                path = os.path.join(data_dir, file)
                yield (path, year, month)
            else:
                logging.debug('%s is not a valid month filename' % file)

    def _load_month_from_disk(self, path, year_number, month_number):
        '''
        Load the month file at path and return a month object

        If an error occurs, return None
        '''
        try:
            # Try to read the contents of the file.
            with codecs.open(path, 'rb', encoding='utf-8') as month_file:
                logging.debug('Loading file "%s"' % path)
                month_contents = yaml.load(month_file, Loader=Loader)
                month = Month(year_number, month_number, month_contents, os.path.getmtime(path))
                return month
        except yaml.YAMLError as exc:
            logging.error('Error in file %s:\n%s' % (path, exc))
        except IOError:
            # If that fails, there is nothing to load, so just display an error message.
            logging.error('Error: The file %s could not be read' % path)
        except Exception:
            logging.error('An error occured while reading %s:' % path)
            raise
        # If we continued here, the possibly corrupted file would be overwritten.
        sys.exit(1)


    def load_all_months_from_disk(self, data_dir):
        '''
        Load all months and return a directory mapping year-month values
        to month objects.
        '''
        months = {}

        logging.debug('Starting to load files in dir "%s"' % data_dir)
        for path, year_number, month_number in self.get_journal_files(data_dir):
            month = self._load_month_from_disk(path, year_number, month_number)
            if month:
                months[self.format_year_and_month(year_number, month_number)] = month

        logging.debug('Finished loading files in dir "%s"' % data_dir)
        return months


    def _save_month_to_disk(self, month, journal_dir):
        """
        When overwriting 2014-12.txt:
            write new content to 2014-12.new.txt
            cp 2014-12.txt 2014-12.old.txt
            mv 2014-12.new.txt 2014-12.txt
            rm 2014-12.old.txt
        """
        content = {}
        for day_number, day in month.days.items():
            if not day.empty:
                content[day_number] = day.content

        def get_filename(infix):
            year_and_month = self.format_year_and_month(month.year_number, month.month_number)
            return os.path.join(journal_dir, '%s%s.txt' % (year_and_month, infix))

        old = get_filename('.old')
        new = get_filename('.new')
        filename = get_filename('')

        # Do not save empty month files.
        if not content and not os.path.exists(filename):
            return False

        with codecs.open(new, 'wb', encoding='utf-8') as f:
            # Write readable unicode and no Python directives.
            yaml.dump(content, f, Dumper=Dumper, allow_unicode=True)

        if os.path.exists(filename):
            mtime = os.path.getmtime(filename)
            if mtime != month.mtime:
                conflict = get_filename('.CONFLICT_BACKUP' + str(mtime))
                logging.debug('Last edit time of %s conflicts with edit time at file load\n'
                              '--> Backing up to %s' % (filename, conflict))
                shutil.copy2(filename, conflict)
            shutil.copy2(filename, old)
        shutil.move(new, filename)
        if os.path.exists(old):
            os.remove(old)

        try:
            # Make file readable and writable only by the owner.
            os.chmod(filename, stat.S_IRUSR | stat.S_IWUSR)
        except OSError:
            pass

        month.edited = False
        month.mtime = os.path.getmtime(filename)
        logging.info('Wrote file %s' % filename)
        return True

    def save_months_to_disk(self, months, journal_dir, exit_imminent=False, saveas=False):
        '''
        Update the journal on disk and return if something had to be written.
        '''
        something_saved = False
        for year_and_month, month in months.items():
            # We always need to save everything when we are "saving as".
            if month.edited or saveas:
                something_saved |= self._save_month_to_disk(month, journal_dir)

        return something_saved

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
                    content = {}
                    #print('  Month', month.name)
                    for day in os.scandir(month.path):
                        #print('    Day', day.name)
                        d = ''
                        with open( day.path, 'r') as f:
                            d=f.read()
                        content[int(day.name[4:-3])] = {'text' : d}
                    mon = Month( int(year.name), int(month.name), content, os.path.getmtime(month.path))
                    months[self.format_year_and_month( int(year.name), int(month.name))] = mon
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

        for element in os.scandir( basedir ):
            with open( element.path ) as f:
                if md_exp.match(element.name):
                    ret[element.name[:-3]] = f.read()
                else:
                    raise(SystemError)
        return ret
