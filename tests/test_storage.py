import os
import os.path

import pytest
# See also
# - https://pypi.org/project/pytest-mock/
# - https://docs.python.org/3/library/unittest.mock.html#unittest.mock.MagicMock

from tempfile import TemporaryDirectory

from rednotebook.data import Month
from rednotebook.data import Day
from rednotebook.storage import FsStorage
from rednotebook.storage import StorageSeparateFiles

# Tests for save and load roundtrips

def test_roundtrip():
    sample_text1 = "This is some sample text"
    sample_text2 = "This is some more sample text"
    sample_months = {
        '2018-07': Month(2018, 7, {28: {'text': sample_text1}}),
        '2018-06': Month(2018, 6, {8: {'text': sample_text2}}),
    }
    storage=FsStorage()
    with TemporaryDirectory() as td:
        storage.save_months_to_disk(sample_months, td, saveas=True)
        loaded = storage.load_all_months_from_disk(td)

    assert isinstance(loaded, dict)
    assert set(loaded) == {'2018-07', '2018-06'}
    assert loaded['2018-07'].days[28].text == sample_text1
    assert loaded['2018-06'].days[8].text == sample_text2

def test_mtime_roundtrip(mocker):
    mocker.patch('os.path.getmtime', side_effect = [80,81,82,83])
    days1 = { 1 : {'text' : 'Monday'}, 2: {'text' : 'Tuesday'}}
    days2 = { 1 : {'text' : 'Monday'}, 2: {'text' : 'Tuesday'}}
    sample_months = {
        '2018-07': Month(2018, 7, days1),
        '2018-06': Month(2018, 6, days2),
    }
    storage=FsStorage()
    with TemporaryDirectory() as td:
        storage.save_months_to_disk(sample_months, td, saveas=True)
        loaded = storage.load_all_months_from_disk(td)

    assert isinstance(loaded, dict)
    assert set(loaded) == {'2018-07', '2018-06'}
    assert loaded['2018-06'].days[2].text == 'Tuesday'
    assert loaded['2018-07'].days[1].text == 'Monday'
    assert loaded['2018-06'].mtime == 82
    assert loaded['2018-07'].mtime == 83

def test_plain_separate():
    some = "something"
    something = "something completely different"
    sample_months = {
        '2018-01': Month(2018, 1, {5: {'text': some}, 6: {'text': something}}),
        '2018-02': Month(2018, 2, {5: {'text': some}, 6: {'text': something}}),
        '2018-03': Month(2018, 3, {5: {'text': some}, 6: {'text': something}}),
    }
    sample_months['2018-01'].edited=True
    sample_months['2018-02'].edited=True
    sample_months['2018-03'].edited=True
    storage=StorageSeparateFiles()
    with TemporaryDirectory() as td:
        ret = storage.save_months_to_disk(sample_months, td, saveas=True)
        loaded = storage.load_all_months_from_disk(td)

    assert isinstance(loaded, dict)
    assert '2018-01' in loaded.keys()
    assert '2018-02' in loaded.keys()
    assert '2018-03' in loaded.keys()
    for m in ('2018-01', '2018-02', '2018-03'):
        assert loaded[m].days[5].text == some
        assert loaded[m].days[6].text == something
    assert ret ==  True

def test_save_months_to_disk_no_change():
    some = "something"
    something = "something completely different"
    sample_months = {
        '2018-01': Month(2018, 1, {5: {'text': some}, 6: {'text': something}}),
    }
    storage=StorageSeparateFiles()
    with TemporaryDirectory() as td:
        ret = storage.save_months_to_disk(sample_months, td, saveas=False)
    assert ret ==  False

def test_multiline_stuff():
    multiline = "\n things\n\n other things\n"
    sample_months = {
        '2018-01': Month(2018, 1, {5: {'text': multiline}}) }
    sample_months['2018-01'].edited=True
    storage=StorageSeparateFiles()
    with TemporaryDirectory() as td:
        storage.save_months_to_disk(sample_months, td, saveas=True)
        loaded = storage.load_all_months_from_disk(td)
    assert loaded['2018-01'].days[5].text == multiline

# Tests for save feature

def test_avoid_empty_separated_entry():
    content = ''
    sample_months = {
        '2018-01': Month(2018, 1, {7: {'text': content}}) }
    storage=StorageSeparateFiles()
    with TemporaryDirectory() as td:
        ret = storage.save_months_to_disk(sample_months, td, saveas=True)
        assert not os.path.exists(os.path.join(td, '2018/01/day-07.md'))
    assert ret == False

def test_save_months_to_disk_open_error(mocker):
    mocker.patch('builtins.open', side_effect = OSError)
    content = 'content'
    sample_months = {
        '2018-01': Month(2018, 1, {7: {'text': content}}) }
    sample_months['2018-01'].edited=True
    storage=StorageSeparateFiles()
    with TemporaryDirectory() as td:
        with pytest.raises(OSError):
            storage.save_months_to_disk(sample_months, td, saveas=True)

def test_write_file_open_error(mocker):
    mocker.patch('builtins.open', side_effect = OSError)
    content = {'text': 'content'}
    storage=StorageSeparateFiles()
    with TemporaryDirectory() as td:
        with pytest.raises( OSError ):
            storage.write_file(7, Day( Month(2018, 1), 1, content), td)

def test_save_months_to_disk_no_saveas_no_edit(mocker):
    mocker.patch('builtins.open')
    content = 'content'
    sample_months = {
        '2018-01': Month(2018, 1, {7: {'text': content}}) }
    storage=StorageSeparateFiles()
    with TemporaryDirectory() as td:
            ret = storage.save_months_to_disk(sample_months, td, saveas=False)
    open.assert_not_called()
    assert ret == False

def test_save_months_to_disk_no_saveas_two_edits(mocker):
    mock = mocker.patch.object(StorageSeparateFiles, 'write_file')
    mock.side_effect=[True, True, False]
    something = 'content'
    sample_months = {
        '2018-01': Month(2018, 1, { 6: {'text': something}}),
        '2018-02': Month(2018, 2, { 6: {'text': something}}),
        '2018-03': Month(2018, 3, { 6: {'text': something}}),
    }
    sample_months['2018-01'].edited=True
    sample_months['2018-02'].edited=True
    storage=StorageSeparateFiles()
    with TemporaryDirectory() as td:
            ret = storage.save_months_to_disk(sample_months, td, saveas=False)

    calls = [
        mocker.call(mocker.ANY, mocker.ANY, mocker.ANY),
        mocker.call(mocker.ANY, mocker.ANY, mocker.ANY)]
    mock.assert_has_calls( calls )
    assert ret == True

def test_save_months_to_disk_wrong_input_type_month():
    sample_months = None
    td='somewhere'
    storage=StorageSeparateFiles()
    with pytest.raises(SystemError):
        storage.save_months_to_disk(sample_months, td, saveas=True)

def test_save_months_to_disk_wrong_input_dir():
    sample_months = {}
    td='nowhere'
    storage=StorageSeparateFiles()
    with pytest.raises(SystemError):
        storage.save_months_to_disk(sample_months, td, saveas=True)

# Tests for load feature

def test_load_all_months_from_disk_empty():
    storage=StorageSeparateFiles()
    with TemporaryDirectory() as td:
        loaded = storage.load_all_months_from_disk(td)
    assert loaded == {}

def test_load_all_months_from_disk_nonexistent():
    storage=StorageSeparateFiles()
    with TemporaryDirectory() as td:
        with pytest.raises(SystemError):
            storage.load_all_months_from_disk(td + '/nonono')

# Tests for categories

def test_categories():
    with TemporaryDirectory() as dir:
        storage=StorageSeparateFiles()
        tree = { 'ToDo': 'Content'}
        fn = os.path.join(dir, 'Tree', 'ToDo.md')
        storage.save_tree_to_disk( dir, tree)
        assert os.path.isdir( os.path.join( dir, 'Tree'))
        assert os.path.isfile(fn)
        with open(fn) as f:
            assert f.read() == tree['ToDo']

        r = storage.load_tree_from_disk(dir)
        assert isinstance(r, dict)
        assert r['ToDo']=='Content'

def test_multiple_categories():
    with TemporaryDirectory() as dir:
        storage=StorageSeparateFiles()
        tree = { 'ToDo': 'Content', 'ToBuy' : 'Stuff', 'ToHack' : 'KLOC'}
        storage.save_tree_to_disk( dir, tree)
        r = storage.load_tree_from_disk(dir)
        assert isinstance(r, dict)
        assert r['ToDo']=='Content'
        assert r['ToBuy']=='Stuff'
        assert r['ToHack']=='KLOC'

def test_categories_loading():
    with TemporaryDirectory() as dir:
        storage=StorageSeparateFiles()
        os.makedirs(os.path.join( dir, 'Tree'), exist_ok=True)
        with open( os.path.join( dir, 'Tree', 'wtf.md'), 'w') as f:
            f.write('wtf')
        with open( os.path.join( dir, 'Tree', 'ftw.md'), 'w') as f:
            f.write('ftw')

        r = storage.load_tree_from_disk(dir)
        assert isinstance(r, dict)
        assert r['wtf']=='wtf'
        assert r['ftw']=='ftw'

def test_categories_loading_wrong_extension():
    with TemporaryDirectory() as dir:
        storage=StorageSeparateFiles()
        os.makedirs(os.path.join( dir, 'Tree'), exist_ok=True)
        with open( os.path.join( dir, 'Tree', 'wtf.whatver'), 'w') as f:
            f.write('wtf')
        with pytest.raises(SystemError):
            storage.load_tree_from_disk(dir)

def test_no_nested_things_up_to_now():
    tree = { 'ToDo': 'Content', 'Things': { 'Thing1': 'Content1', 'Thing1': 'Content1'}}
    storage = StorageSeparateFiles()
    with TemporaryDirectory() as td:
        with pytest.raises( SystemError ):
            storage.save_tree_to_disk(td, tree)
