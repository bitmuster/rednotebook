from tempfile import TemporaryDirectory

from rednotebook.data import Month
from rednotebook.storage import FsStorage

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
