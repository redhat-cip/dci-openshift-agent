#!/usr/bin/env python
# -*- encoding: utf-8 -*-
#
# Copyright 2017-2018 Red Hat, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import os
import sys

import docker
import requests
import subprocess
import yaml

client = docker.from_env()

DCI_REGISTRY = os.getenv('DCI_REGISTRY', 'registry.distributed-ci.io')
DCI_REGISTRY_USER = os.getenv('DCI_REGISTRY_USER')
DCI_REGISTRY_PASSWORD = os.getenv('DCI_REGISTRY_PASSWORD')


def login(username, password, registry):
    print('login onto %s' % registry)
    client.login(username=username, password=password, email='', registry=registry, reauth=True)


def pull_image(image):
    print('docker pull {origin_registry}/{project}/{name}:{tag}'.format(**image))
    client.pull('{origin_registry}/{project}/{name}'.format(**image), tag=image['tag'])


def tag_image(image, tag):
    docker_image_id = client.inspect_image('{origin_registry}/{project}/{name}:{tag}'.format(**image))['Id']
    print('docker tag {} {dest_registry}/{project}/{name}:{}'.format(docker_image_id, tag, **image))
    client.tag(docker_image_id, tag=tag, repository='{dest_registry}/{project}/{name}'.format(**image))


def push_image(image, tag):
    print('docker push {dest_registry}/{project}/{name} {}'.format(tag, **image))
    client.push('{dest_registry}/{project}/{name}'.format(**image), tag=tag)

def list_existing_tags(image):
    r = requests.get('http://{dest_registry}/v2/{project}/{name}/tags/list'.format(**image))
    if r.status_code == 404:
        return []
    elif r.status_code == 200 and r.json():
        return r.json().get('tags') or []
    else:
        raise Exception(r.text)

# If we remove all the tag of the existing image, we won't be able to actuallly
# delete it from the registry. As a result, the registry size will grow up indefinitely.
# Any tag can potentially be already used by an image and by the last "string"
# attached to it. So before we apply a tag, we delete any potential existing tag.
# See: https://github.com/docker/distribution/issues/1844
def delete_existing_tag_from_registry(image, tag):
    api_base = 'http://{dest_registry}/v2/{project}/{name}'.format(**image)

    url = api_base + '/manifests/' + tag
    r = requests.get(url, headers={'Accept': 'application/vnd.docker.distribution.manifest.v2+json'})
    if r.status_code == 404:
        return
    refhash = r.headers['docker-content-digest']
    if not refhash:
        return
    print(api_base + '/manifests/' + refhash)
    r = requests.delete(api_base + '/manifests/' + refhash)
    if r.status_code != 202:
        # 405 code probably means storage.delete.enabled is False.
        raise Exception(r.text)

def sync_image(image):
    pull_image(image)
    for tag in ('latest', image['tag']):
        tag_image(image, tag)
        delete_existing_tag_from_registry(image, tag)
        push_image(image, tag)

def purge_image_from_local_docker(image):
    for image in client.images('{origin_registry}/{project}/{name}'.format(**image)):
        client.remove_image(image['Id'], force=True)


def call_registry_gc():
    print('Calling the registry garbage collector')
    subprocess.check_call([
        '/usr/bin/registry',
        'garbage-collect',
        '/etc/docker-distribution/registry/config.yml'])


def main():
    if len(sys.argv) <= 1:
        print('\nError: images_list.yaml path required\nusage: %s ./images_list.yaml' % sys.argv[0])
        sys.exit(1)

    if DCI_REGISTRY_USER and DCI_REGISTRY_PASSWORD:
        login(DCI_REGISTRY_USER, DCI_REGISTRY_PASSWORD, DCI_REGISTRY)

    docker_distribution_config = yaml.load(open('/etc/docker-distribution/registry/config.yml', 'r'))

    images_to_purge = []
    with open(sys.argv[1], 'r') as stream:
        try:
            images = yaml.load(stream)
        except yaml.YAMLError as exc:
            print(exc)

        for image in images:
            origin, tag = image.split(':')
            origin_registry, project, name = origin.split('/')
            image = {
                'name': name,
                'project': project,
                'tag': tag,
                'origin_registry': origin_registry,
                'dest_registry': docker_distribution_config['http']['addr']
            }
            existing_tags = list_existing_tags(image)
            if image['tag'] in existing_tags:
                print('Image {}:{} is already on the registry'.format(name, tag))
            else:
                sync_image(image)
            images_to_purge.append(image)
    for image in images_to_purge:
        purge_image_from_local_docker(image)
    call_registry_gc()

if __name__ == '__main__':
    main()
