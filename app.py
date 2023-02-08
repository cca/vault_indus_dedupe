import argparse
import json
import os
import shutil

MAIN_FILESTORE_PATH = '/mnt/equelladata01/Institutions/cca2012/Attachments'
ID_FILESTORE_PATH = '/mnt/equelladata/Institutions/cca2012/Attachments/5b07c041-2353-4712-92d0-a71eed9201da'

# copied from our clean_staging project
# https://github.com/cca/equella_clean_staging

# from https://gist.github.com/hanleybrand/5224673
def hash128(str):
    """ return 7-bit hash of string """
    hash = 0
    for char in str:
        hash = (31 * hash + ord(char)) & 0xFFFFFFFF
        hash = ((hash + 0x80000000) & 0xFFFFFFFF) - 0x80000000
        # EQUELLA reduces hashes to values 0 - 127
        hash = hash & 127
    return hash


def get_path(uuid, version=1, filestore='main'):
    """
    given staging area UUID, return its path on the mounted filestore
    path is like /mnt/equelladata01/107/a61aa663-9829-4b9b-bb2c-512d48f46eaf
    NOTE: we actually have 2 filestores so we're just ignoring the secondary one
    for now, which only Industrial Design uses
    """
    PATH_PREFIX = ID_FILESTORE_PATH if filestore.lower() == 'indus' else MAIN_FILESTORE_PATH
    return os.path.join(PATH_PREFIX, str(hash128(uuid)), uuid, str(version))


def compareTwoFileTrees(path1, path2):
    """
    compare two file trees and return a list of files that are different
    """
    files1 = []
    files2 = []
    for root, dirs, files in os.walk(path1):
        for name in files:
            files1.append(name)
    for root, dirs, files in os.walk(path2):
        for name in files:
            files2.append(name)
    return list(set(files1) ^ set(files2))


def check_item(item):
    main_dir = get_path(item['uuid'], item['version'])
    indus_dir = get_path(item['uuid'], item['version'], 'indus')

    if os.path.exists(main_dir) and os.path.exists(indus_dir):
        print('Item %s version %i exists in both filestores' % item['links']['view'])
        diff = compareTwoFileTrees(main_dir, indus_dir)
        if len(diff) > 0:
            print('Found storage differences for item %s' % item['links']['view'])
            print('INDUS path: %s' % indus_dir)
            print('Main path: %s' % main_dir)
            print(diff)
        else:
            # remove the directory from main storage
            print('No differences for item %s' % item['links']['view'])
            if not args.dry_run:
                print('Removing %s' % main_dir)
                shutil.rmtree(main_dir)
    elif os.path.exists(main_dir) and not os.path.exists(indus_dir):
        # happens for pre-2019 item were since purged (e.g. by our retention process)
        print('Item %s only exists in main filestore' % item['links']['view'])
        if not args.dry_run:
            print('Removing %s' % main_dir)
            shutil.rmtree(main_dir)
    elif not os.path.exists(main_dir) and os.path.exists(indus_dir):
        # happens for all post-2019 items
        print('Item %s only exists in indus filestore' % item['links']['view'])
    else:
        # this should never happen, unless item was purged in between creating the data file
        # and running this script
        print('Item %s does not exist in either filestore' % item['links']['view'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Clean up the staging area')
    parser.add_argument('--dry-run', action='store_true', help='Do not actually delete anything')
    parser.add_argument('file', nargs=1, help='The file containing the list of items to clean up')
    args = parser.parse_args()

    if args.dry_run:
        print('Dry run, nothing will be deleted')

    with open(args.file[0], 'r') as f:
        items = json.load(f)

    for item in items:
        check_item(item)
