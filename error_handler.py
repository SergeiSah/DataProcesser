from pandas.errors import EmptyDataError


def try_read(read_function):

    def handle_problems(file_path, *args, **kwargs):
        file_name = file_path.split('/')[-1]

        try:
            return read_function(file_path, *args, **kwargs)
        except FileNotFoundError:
            print(f"File '{file_name}' does not exist!")
        except EmptyDataError:
            print(f"File '{file_name}' is empty!")

    return handle_problems

