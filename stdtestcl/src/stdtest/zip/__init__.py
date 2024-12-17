
import os

def zipx(file: str):
    match os.path.splitext(file)[-1]:
        case '.cpp':
            from .cpp import zipcpp
            return open(zipcpp(file)).read()
        case _:
            return open(file).read()
    