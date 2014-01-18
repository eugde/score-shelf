import os,shutil
import constants


class LinkingHandler():
    """
    A class which handles the management of paths and importing/exporting of data.
    """

    def __init__(self):
        self.root = constants.DATA_ROOT_DIRECTORY
        if not os.path.isdir(self.root):
            self.create_dir(self.root)

        self.data_tree = self.get_walk()

    def create_dir(self, path):
        if os.path.exists(path):
            print("{} already exists.".format(path))
        else:
            os.mkdir(path)
            print("{} created".format(path))

    def remove_dir(self, path):
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
            root = self.root
        return os.walk(root)

    def archive_data(self, name=None, format="zip"):
        if not name:
            name = self.root+"_bak"
        shutil.make_archive(name,format, self.data_dir)

if __name__ == "__main__":
    test = LinkingHandler()
    print(test.root)