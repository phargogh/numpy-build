import sys
import tarfile
import os
import urllib2
import time
import shutil
import subprocess
import glob

def download_file(url, local_file):
    print 'downloading ...'
    u = urllib2.urlopen(url)
    localFile = open(local_file, 'w')
    localFile.write(u.read())
    localFile.close()

def download_numpy(version):
    """Download the approprate version of the numpy source from the official
    download mirror.

    version - the version of numpy to download.  Must be a string in the form
        1.1.1

    Returns the absolute path to the downloaded tar.bz2 file."""

    # parse out the version info
    major, minor, release = version_info(version)

    numpy_download_uri = 'https://pypi.python.org/packages/source/n/numpy/'

    local_gzip = 'numpy-%s.tar.gz' % version
    numpy_download_uri += local_gzip
    print numpy_download_uri
    download_file(numpy_download_uri, local_gzip)

    return os.path.abspath(local_gzip)


if __name__ == '__main__':
    start_time = time.time()
    version_info = lambda v: map(lambda x: int(x), v.split('.'))

    # if the user provided an argument and it's a file, use that.
    try:
        source_filepath = sys.argv[1]
    except IndexError:
        source_filepath = ''

    if os.path.exists(source_filepath):
        print 'Building from source archive %s' % source_filepath
        local_gzip = source_filepath
    else:
        numpy_version = '1.9.0'
        local_gzip = download_numpy(numpy_version)

    numpy_dir = local_gzip.replace('.tar.gz', '')
    if os.path.exists(numpy_dir):
        print 'removing %s' % numpy_dir
        shutil.rmtree(numpy_dir)

    print 'extracting', local_gzip
    tfile = tarfile.open(local_gzip, 'r:gz')
    tfile.extractall('.')

    # fetch and build openblas
    dst_openblas_dir = os.path.join(os.getcwd(), 'openblas')
    if os.path.exists(dst_openblas_dir):
        shutil.rmtree(dst_openblas_dir)
    openblas_url = 'http://github.com/xianyi/OpenBLAS/tarball/v0.2.12'
    download_file(openblas_url, 'openblas.tar.gz')
    tfile = tarfile.open('openblas.tar.gz', 'r:gz')
    tfile.extractall('.')
    os.rename(glob.glob('xianyi-*')[0], os.path.basename(dst_openblas_dir))

    # define the openblas source dir
    os.chdir(dst_openblas_dir)
    subprocess.call('make', shell=True)
    subprocess.call('make PREFIX=. install', shell=True)
    os.chdir('..')

    # Now that we've built openblas, write the numpy site.cfg file to configure
    # openblas and build the numpy wheel.
    os.chdir(numpy_dir)
    openblas_lib = os.path.join(dst_openblas_dir, 'lib')
    openblas_inc = os.path.join(dst_openblas_dir, 'include')
    config_string = "[openblas]\nlibrary_dirs = %s\ninclude_dirs = %s\n"
    site_cfg_uri = os.path.join(numpy_dir, 'site.cfg')
    with open(site_cfg_uri, 'w') as site_file:
        site_file.write(config_string)
    subprocess.call('python setup.py bdist_wheel')
    os.chdir('..')

    end_time = time.time()
    print 'All operations took %ss' % ((end_time - start_time))
