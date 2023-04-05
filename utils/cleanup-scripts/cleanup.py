#!/usr/bin/python3
#
# Copyright (C) 2023 Red Hat, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import sys
import pathlib
import argparse
import re
import shutil
from distutils.version import LooseVersion


def get_directories(directory, pattern):
    directories = dict()
    prog = re.compile(pattern)
    currentDirectory = pathlib.Path(directory)
    for currentFile in currentDirectory.iterdir():
      m = prog.match(currentFile.name)
      if currentFile.is_dir() and m:
          if m.group(1) in directories:
              directories[m.group(1)].append("%s" % currentFile)
          else:
              directories[m.group(1)] = ["%s" % currentFile]
    return directories


def garbage_collect(directories, number, run, quiet):
    # Entries to skip from the end of the list
    if number > 0:
        number = number.__neg__()
    for version in directories:
        dir_version = sorted(directories[version], key=LooseVersion)
        if len(dir_version) > 1:
            for to_remove in dir_version[:number]:
                if not quiet:
                    print(to_remove)
                if run:
                    shutil.rmtree(to_remove)


def main():
    default_regex = r'([0-9]+\.[0-9]+\.[0-9]+).*nightly.*'
    parser = argparse.ArgumentParser(description='Garbage collect directories')
    parser.add_argument('directory', metavar='DIR',
            help='Directory to garbage collect')
    parser.add_argument('-p', '--pattern', dest='pattern',
            default=default_regex,
            help='Use Regex PATTERN, must include a group definition or'
                 ' it will fail.  default: %s' % default_regex,
            metavar="PATTERN")
    parser.add_argument('-n', '--number', dest='number',
            default=1, type=int,
            help='The NUMBER of entries to keep, default: 1')
    parser.add_argument('-r', '--run',
            action='store_true', dest='run', default=False,
            help='Specify this to actually do the garbage collection,'
                 ' otherwise it will just print what it will remove')
    parser.add_argument('-q', '--quiet',
            action='store_true', dest='quiet', default=False,
            help='Be Quiet')

    args = parser.parse_args()


    directories = get_directories(args.directory, args.pattern)
    garbage_collect(directories, args.number, args.run, args.quiet)

if __name__ == '__main__':
    sys.exit(main())

