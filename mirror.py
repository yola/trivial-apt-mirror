#!/usr/bin/env python

import argparse
import gzip
import hashlib
import os
import sys

import debian.deb822
import requests


class Mirror(object):
    def __init__(self, host, root, suite, hash, destination):
        self.host = host
        self.root = root
        self.suite = suite
        self.hash = hash
        self.destination = destination

    def full_mirror(self):
        self.m_release()
        self.m_release_contents()
        self.m_package_contents()

    def _get(self, *path):
        url = 'http://%s/%s/%s' % (self.host, self.root, '/'.join(path))
        print url,
        return requests.get(url, stream=True)

    def _local(self, *path, **kwargs):
        mode = kwargs.pop('mode', 'r')
        assert not kwargs

        path = os.path.join(self.destination, *path)
        dir_ = os.path.dirname(path)
        if not os.path.exists(dir_):
            os.makedirs(dir_)
        return open(path, mode)

    def _mirror(self, *path, **kwargs):
        hash = kwargs.pop('hash', None)
        if hash:
            hasher = hashlib.new(self.hash)

        if hash and os.path.exists(os.path.join(self.destination, *path)):
            with self._local(*path) as f:
                while True:
                    block = f.read(1024)
                    if not block:
                        break
                    hasher.update(block)
            if hasher.hexdigest() == hash:
                return
            hasher = hashlib.new(self.hash)

        r = self._get(*path)
        if r.status_code != 200:
            raise Exception('Got a %s' % r.status_code)

        with self._local(*path, mode='w') as f:
            while True:
                block = r.raw.read(1024)
                if not block:
                    break
                f.write(block)
                sys.stdout.write('.')
                sys.stdout.flush()
                if hash:
                    hasher.update(block)
            sys.stdout.write('\n')
            sys.stdout.flush()
            if hash:
                assert hasher.hexdigest() == hash

    def m_release(self):
        self._mirror(self.suite, 'Release')
        self._mirror(self.suite, 'Release.gpg')

    def m_release_contents(self):
        with self._local(self.suite, 'Release') as f:
            r = debian.deb822.Release(f)

        packages_hash = None

        for item in r['sha1']:
            if item['name'] == 'Release':
                continue
            if item['name'] == 'Packages':
                packages_hash = item[self.hash]
                continue
            self._mirror(self.suite, item['name'], hash=item[self.hash])

        # Content negotiation in our source is a pain
        hasher = hashlib.new(self.hash)
        with self._local(self.suite, 'Packages.gz') as f1:
            gzf = gzip.GzipFile(fileobj=f1)
            with self._local(self.suite, 'Packages', mode='w') as f2:
                while True:
                    block = gzf.read(1024)
                    if not block:
                        break
                    f2.write(block)
                    hasher.update(block)
            assert hasher.hexdigest() == packages_hash

    def m_package_contents(self):
        with self._local(self.suite, 'Packages') as f:
            p = debian.deb822.Packages.iter_paragraphs(f)
            p = list(p)
        for package in p:
            self._mirror(package['filename'], hash=package[self.hash])


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--host', '-H',
                   help='Source host name')
    p.add_argument('--root', '-r',
                   default='debian',
                   help='Mirror base directory')
    p.add_argument('--suite', '-suite',
                   default='binary',
                   help='Suite within the base directory')
    p.add_argument('--destination', '-d',
                   help='Destination directory')
    p.add_argument('--hash',
                   default='sha1',
                   help='Hash algorithm to use from metadata files')
    args = p.parse_args()

    mirror = Mirror(args.host, args.root, args.suite, args.hash,
                    args.destination)
    mirror.full_mirror()


if __name__ == '__main__':
    main()
