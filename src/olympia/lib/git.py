import pygit2


class BlobWrapper(object):
    """A lazy blob object that only loads data on demand."""
    _blob = None

    def __init__(self, repository, id):
        self._repository = repository
        self.id = id
        self.hex = str(id)
        self.type = pygit2.GIT_OBJ_BLOB

    def _load_blob(self):
        if self._blob is None:
            self._blob = self._repository[self.id]
        return self._blob

    def __getattr__(self, item):
        blob = self._load_blob()
        return getattr(blob, item)


class Repository(pygit2.Repository):

    def __init__(self, *args, **kwargs):
        super(Repository, self).__init__(*args, **kwargs)
        assert self.is_bare
        # Always load the index
        # TODO: do we have to?
        self.index.read_tree(self.tree.id)

    @property
    def commit(self):
        """shortcut to the head commit"""
        return self.head.peel(pygit2.GIT_OBJ_COMMIT)

    @property
    def tree(self):
        """shortcut to the head tree"""
        return self.head.peel(pygit2.GIT_OBJ_TREE)

    def open(self, path):
        """High-level object retriever.
            @param path: object path, relative to the repository root
        """

        # Repository root
        if path in ("", "/"):
            return self.tree

        tree_entry = self.tree[path]

        if tree_entry.type == 'blob':
            return BlobWrapper(self, tree_entry.id)

        return self[tree_entry.id]
