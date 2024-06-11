import re
import warnings
import os
import inspect


def regressionFilename(ext: str = ".txt", *, dir: str = "results", stacklvl: int = 0):

    current_frame = inspect.stack()[stacklvl]
    parent_module = inspect.getmodule(current_frame[0]).__name__.rsplit('.', maxsplit=1)[0]

    caller_frame = inspect.stack()[stacklvl + 1]

    function = caller_frame.function
    module = inspect.getmodule(caller_frame[0]).__name__
    if (module.startswith(parent_module + '.')):
        module = module[len(parent_module) + 1:]

    moddirname = os.path.split(inspect.getmodule(caller_frame[0]).__file__)[0]
    if (os.path.isabs(dir)):
        dirname = dir
    else:
        dirname = os.path.join(moddirname, dir)
    if (not os.path.isdir(dirname)):
        os.mkdir(dirname)

    return os.path.join(dirname, f"{module}.{function}{ext}")


def compareWithRegressionFile(value: str, *, ext: str = '.txt', dir: str = "results", tol: float = 0):
    if (ext[0] not in '._'):
        ext = '.' + ext
    filename = regressionFilename(ext, dir=dir, stacklvl=1)
    try:
        with open(filename) as file:
            reference = "".join(file.readlines())
    except Exception as e:
        warnings.warn(
            "regression result file '%s' could not be read (%s)" % (filename, e),
            RuntimeWarning
        )
        reference = ""
    if (value != reference):
        regex = re.compile(r"([^\d\-]+)(-?\d*\.\d+)?")
        line_num = 0
        almost_equal = True
        for current, reference in zip(value.splitlines(keepends=False), reference.splitlines(keepends=False)):
            line_num += 1
            if (current != reference):
                # try to extract floats from the line and compare them with almostEqual
                found = regex.findall(current)
                expected = regex.findall(reference)
                lines_match = True
                if (len(found) != len(expected)):
                    lines_match = False
                else:
                    for e, f in zip(expected, found):
                        expected_text, expected_float = e
                        found_text, found_float = e
                        if (expected_text != found_text):
                            lines_match = False
                        elif (expected_float != found_float):
                            try:
                                lines_match = abs(float(expected_float) - float(found_float)) < tol
                            except ValueError:
                                lines_match = False
                if (not lines_match):
                    print("")
                    print("mismatch in %s line %d:" % (filename, line_num))
                    print("    expected: '%s'" % reference)
                    print("    found:    '%s'" % current)
                    almost_equal = False
        with open(regressionFilename("_new" + ext, dir=dir, stacklvl=1), "w") as result_file:
            result_file.write(value)
        return almost_equal
    else:
        return True
