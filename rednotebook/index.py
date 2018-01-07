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

import collections


class Index:
    def __init__(self):
        self._word_to_dates = collections.defaultdict(set)

    def add(self, date, words):
        for word in set(word.lower() for word in words):
            self._word_to_dates[word].add(date)

    def remove(self, date, words):
        for word in set(word.lower() for word in words):
            try:
                self._word_to_dates[word].remove(date)
            except:
                pass # The date is not in the list -> ignore
            if not self._word_to_dates[word]:
                del self._word_to_dates[word]

    def find(self, word):
        # Pass a copy to the caller.
        return set(self._word_to_dates[word.lower()])

    def clear(self):
        self._word_to_dates.clear()
