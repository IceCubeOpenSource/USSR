# Simulation management class adapted from https://github.com/desihub/specsim.
# The specsim project is distributed under a 3-clause BSD style license:
#
# Copyright (c) 2015, Specsim Developers <dkirkby@uci.edu>
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
# * Neither the name of the Specsim Team nor the names of its contributors may
#   be used to endorse or promote products derived from this software without
#   specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
"""Manage simulation configuration data.
"""

import yaml

class Node(object):
    """A single node of a configuration data structure.
    """
    def __init__(self, value, path=[]):
        self._assign('_value', value)
        self._assign('_path', path)


    def keys(self):
        return self._value.keys()


    def _assign(self, name, value):
        # Bypass our __setattr__
        super(Node, self).__setattr__(name, value)


    def __str__(self):
        return '.'.join(self._path)


    def __getattr__(self, name):
        # This method is only called when self.name fails.
        child_path = self._path[:]
        child_path.append(name)
        if name in self._value:
            child_value = self._value[name]
            if isinstance(child_value, dict):
                return Node(child_value, child_path)
            else:
                # Return the actual value for leaf nodes.
                return child_value
        else:
            raise AttributeError(
                'No such config node: {0}'.format('.'.join(child_path)))

    def __setattr__(self, name, value):
        # This method is always triggered by self.name = ...
        child_path = self._path[:]
        child_path.append(name)
        if name in self._value:
            child_value = self._value[name]
            if isinstance(child_value, dict):
                raise AttributeError(
                    'Cannot assign to non-leaf config node: {0}'
                    .format('.'.join(child_path)))
            else:
                self._value[name] = value
        else:
            raise AttributeError(
                'No such config node: {0}'.format('.'.join(child_path)))


class Configuration(Node):
    """Configuration parameters container and utilities.

    This class specifies the required top-level keys and delegates the
    interpretation and validation of their values to other functions.

    Parameters
    ----------
    config : dict
        Dictionary of configuration parameters, normally obtained by parsing
        a YAML file with :func:`load`.

    Raises
    ------
    ValueError
        Missing required top-level configuration key.

    Attributes
    ----------
    wavelength : astropy.units.Quantity
        Array of linearly increasing wavelength values used for all simulation
        calculations.  Determined by the wavelength_grid configuration
        parameters.
    abs_base_path : str
        Absolute base path used for loading tabulated data.  Determined by
        the basepath configuration parameter.
    """
    def __init__(self, config):

        Node.__init__(self, config)
        self.update()


    def update(self):
        """Update this configuration.

        Updates the wavelength and abs_base_path attributes based on
        the current settings of the wavelength_grid and base_path nodes.
        """
        # Initialize our wavelength grid.
        grid = self.wavelength_grid
        nwave = 1 + int(math.floor(
            (grid.max - grid.min) / grid.step))
        if nwave <= 0:
            raise ValueError('Invalid wavelength grid.')
        wave_unit = astropy.units.Unit(grid.unit)
        wave = (grid.min + grid.step * np.arange(nwave)) * wave_unit
        self._assign('wavelength', wave)

        # Use environment variables to interpolate {NAME} in the base path.
        base_path = self.base_path
        if base_path == '<PACKAGE_DATA>':
            self._assign(
                'abs_base_path', astropy.utils.data._find_pkg_data_path('data'))
        else:
            try:
                self._assign('abs_base_path', base_path.format(**os.environ))
            except KeyError as e:
                raise ValueError('Environment variable not set: {0}.'.format(e))
