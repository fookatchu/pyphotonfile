import pytest
import traceback
import os
import shutil

@pytest.fixture()
def temp_folder():
    try:
        os.makedirs('tests\\tempdir\\')
    except OSError:
        pass
    yield 'tests\\tempdir\\'
    try:
        shutil.rmtree('tests\\tempdir\\')
    except:
        traceback.print_exc()
