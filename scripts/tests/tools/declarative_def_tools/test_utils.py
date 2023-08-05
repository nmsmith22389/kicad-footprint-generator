from scripts.tools.declarative_def_tools import utils

def test_as_list():

    assert(utils.as_list('foo') == ['foo'])
    assert(utils.as_list(['foo']) == ['foo'])
    assert(utils.as_list(42) == [42])
    assert(utils.as_list([]) == [])