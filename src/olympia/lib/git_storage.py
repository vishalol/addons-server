
import io
import os

from django.apps import apps
from django.core.exceptions import ImproperlyConfigured
from django.core.files import storage, File
from django.conf import settings
from django.utils.encoding import filepath_to_uri
from django.utils._os import safe_join

import pygit2

from olympia.lib.git import Repository


REFERENCE_NAME = 'refs/heads/master'
INITIAL_COMMIT_MESSAGE = "Initial commit by Git Storage"
SAVE_MESSAGE = "Saved by Git Storage"
DELETE_MESSAGE = "Deleted by Git Storage"


class GitRepository(object):

    def __init__(self, path):
        self.path = path

        if not os.path.exists(self.path):
            self.create_repository(self.path)

        self.repository = Repository(self.path)
        assert self.repository.is_bare

        self.author_signature = self.repository.default_signature

    def _git_path(self, name):
        path = safe_join(self.location, name)
        path = os.path.normpath(path)
        # Strip off the repo absolute path
        path = path[len(self.location) + 1:]
        return path

    def create_repository(self):
        repository = pygit2.init_repository(self.location, bare=True)

        repository.config['user.name'] = 'Git Storage'
        repository.config['user.email'] = 'git@storage'

        tree_id = repository.TreeBuilder().write()
        repository.create_commit(
            REFERENCE_NAME,
            repository.default_signature,  # Author signature from repository/config [user]
            repository.default_signature,  # Committer signature from repository/config [user]
            INITIAL_COMMIT_MESSAGE,
            tree_id,
            [],
        )

    def _commit(self, message, tree):
        self.repository.create_commit(
            self.repository.head.name,
            self.author_signature,
            self.repository.default_signature,  # Committer signature from repository/config [user]
            message,
            tree,
            [self.repository.head.target],
        )

    def set_author(self, user):
        self.author_signature = pygit2.Signature(user.get_full_name(), user.email, encoding='utf8')

    def _open(self, name, mode='rb'):
        blob = self.repository.open(self._git_path(path))
        # TODO: Does pygit2 offer some lazy loading here?
        # create_blob_fromiobase?
        return File(io.BytesIO(blob.data), name=name)

    def _save(self, name, content):
        path = self._git_path(name)

        if hasattr(content, 'temporary_file_path'):
            blob_id = self.repository.create_blob_fromdisk(content.temporary_file_path())
            content.close()
        else:
            blob_id = self.repository.create_blob(content.read())

        index = self.repository.index
        index.add(pygit2.IndexEntry(path, blob_id, pygit2.GIT_FILEMODE_BLOB))
        tree_id = index.write_tree()
        self._commit(SAVE_MESSAGE, tree_id)
        return name

    def get_available_name(self, name, max_length=None):
        return self._git_path(name)

    def path(self, name):
        raise NotImplementedError()

    def delete(self, name):
        path = self._git_path(name)
        index = self.repository.index
        index.remove(path)
        tree_id = index.write_tree()
        self._commit(DELETE_MESSAGE, tree_id)

    def exists(self, name):
        path = self._git_path(name)
        return path in self.repository.tree

    def listdir(self, path):
        path = self._git_path(path)
        tree = self.repository.open(path)
        trees, blobs = [], []
        for entry in tree:
            if entry.type == "blob":
                blobs.append(entry)
            elif entry.type == "tree":
                trees.append(entry)
        return trees, blobs

    def size(self, name):
        path = self._git_path(name)
        blob = self.repository.open(path)
        return blob.size
