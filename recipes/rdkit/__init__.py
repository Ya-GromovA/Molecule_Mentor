from pythonforandroid.recipe import PythonRecipe

class RDKitRecipe(PythonRecipe):
    version = '2023.03.3'
    url = 'https://github.com/rdkit/rdkit/archive/refs/tags/Release_2023_03_3.tar.gz'
    depends = ['python3', 'numpy', 'setuptools']
    call_hostpython_via_targetpython = False
    install_in_hostpython = True

    def get_recipe_env(self, arch=None, with_flags_in_cc=True):
        env = super().get_recipe_env(arch, with_flags_in_cc)
        env['CFLAGS'] += ' -fcommon'
        return env

recipe = RDKitRecipe()
