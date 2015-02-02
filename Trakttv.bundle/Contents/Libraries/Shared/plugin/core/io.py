import os


class FileIO(object):
    @staticmethod
    def exists(path):
        return os.path.exists(path)

    @staticmethod
    def delete(path):
        os.remove(path)

    @staticmethod
    def read(path):
        fp = open(path, 'r')

        # Read from file
        data = fp.read()

        # Close file
        fp.close()

        return data

    @staticmethod
    def write(path, data):
        fp = open(path, 'w')

        # Write to file
        fp.write(data)

        # Close file
        fp.close()
