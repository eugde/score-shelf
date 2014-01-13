import os,shutil


class LinkingHandler():
    """
    A class which handles the management of paths and importing/exporting of data.
    """

    def __init__(self):
        self.root = os.getcwd()
        self.data_dir = os.path.join(self.root, "data")
        self.data_tree = self.get_walk()

        self.create_dir(self.data_dir)

    def create_dir(self, path):
        if os.path.exists(path):
            print("{} already exists.".format(path))
        else:
            os.mkdir(path)
            print("{} created".format(path))

    def remove_dir(self,path):
        def handle_delerror(function, errpath, excinfo):
            #This function is used as quasi-lambda for the rmtree function.
            print("{} couldn't be executed correctly at {}: {}".format(function,errpath,excinfo))
        shutil.rmtree(path, onerror=handle_delerror)

    def rename_dir(self, src, dst):
        try:
            os.rename(src, dst)
        except os.error as e:
            print(e.args[0])

    def gen_rel_link(self, tail, root=None):
        if not root:
            root = self.root
        return os.path.join(root, tail)

    def get_walk(self, root = None):
        if not root:
            root = self.data_dir
        return os.walk(root)

    def archive_data(self, name=None, format="zip"):
        if not name:
            name = self.data_dir+"_bak"
        shutil.make_archive(name,format, self.data_dir)