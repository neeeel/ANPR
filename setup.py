from distutils.core import setup
import py2exe.build_exe

#setup(console=['test.py'], options={"py2exe":{"includes":["scipy.sparse.csgraph._validation","scipy.linalg.cython_blas","scipy.linalg.cython_lapack"]}})
setup(data_files=[("tcl",['C:/Python34/tcl/tcl8.6/init.tcl'])],
        console=[{"script":'test.py',"dest_base" : "ANPR v0.1",}],
        options={"py2exe":{"includes":["scipy.sparse.csgraph._validation","scipy.linalg.cython_blas","scipy.linalg.cython_lapack","PIL","numpy","openpyxl"]}})