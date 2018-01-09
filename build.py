import git
import nbconvert
import nbformat
from nbconvert.preprocessors import ExecutePreprocessor
import os
from nbconvert.preprocessors.execute import CellExecutionError
import logging

BUILD_DIR = '../build'

logger = logging.getLogger('kb_builder')
logger.setLevel(logging.INFO)
logger.addHandler(logging.FileHandler(os.path.join(BUILD_DIR, 'logs', 'log.txt'), mode='a'))
logger.addHandler(logging.StreamHandler())



def get_file_modified_times():
    ipynb_files = {}
    for root, subdirs, files in os.walk('.'):
        if not '.ipynb_checkpoints' in root:
            for f in files:
                if f[-5:] == 'ipynb':
                    path = os.path.join(root, f)
                    statbuf = os.stat(path)
                    ipynb_files[(root, f)] = statbuf.st_mtime
    return ipynb_files

def check_diff(f1, f2):
    removed = set(f1.keys()) - set(f2.keys())
    added = set(f2.keys()) - set(f1.keys())
    intersection = f1.keys() & f2.keys()



    modified = []
    for i in intersection:
        if f1[i] != f2[i]:
            modified.append(i)

    if len(removed) > 0:
        logger.info('Removing {} notebooks'.format(len(removed)))
    if len(added) > 0:
        logger.info('Adding {} notebooks'.format(len(added)))
    if len(modified) > 0:
        logger.info('Modifying {} notebooks'.format(len(modified)))

    for path, file in added:
        execute_notebook(path, file)

    for path, file in modified:
        execute_notebook(path, file)

    for path, file in removed:
        remove_built_notebook(path, file)


def remove_built_notebook(path, file):
    file_path = os.path.join(BUILD_DIR, path, file)
    logger.info('Removing {}'.format(file_path))
    os.remove(file_path)

def execute_notebook(path, file):
    file_path = os.path.join(path, file)
    build_path = os.path.join(BUILD_DIR, path, file)
    if not os.path.exists(build_path):
        os.mkdir(build_path)

    with open(file_path) as f:
        nb = nbformat.read(f, as_version=4)

    ep = ExecutePreprocessor(timeout=None)
    try:
        logger.info('Executing {}'.format(file_path))
        out = ep.preprocess(nb, {'metadata': {'path': path}})
    except CellExecutionError:
        out = None
        msg = 'Error executing the notebook "%s".\n\n' % file_path
        msg += 'See notebook "%s" for the traceback.' % build_path
        logger.error(msg)
        raise
    finally:
        logger.info('Writing to {}'.format(build_path))
        with open(build_path, mode='wt') as f:
            nbformat.write(nb, f)


f1 = get_file_modified_times()
g = git.cmd.Git('.')

g.pull()
f2 = get_file_modified_times()

check_diff(f1, f2)
