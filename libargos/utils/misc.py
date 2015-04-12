# -*- coding: utf-8 -*-

# This file is part of Argos.
# 
# Argos is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# Argos is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with Argos. If not, see <http://www.gnu.org/licenses/>.

""" Miscellaneous routines.
"""
import logging, sys
logger = logging.getLogger(__name__)
    

class NotSpecified(object):
    """ Class for NOT_SPECIFIED constant.
        Is used so that a parameter can have a default value other than None.
    """
    pass
    
NOT_SPECIFIED = NotSpecified()
    
    
    
def python_major_version():
    """ Returns 2 or 3 for Python 2.x or 3.x respectively
    """
    return sys.version_info[0]

def python2():
    """ Returns True if we are running python 2
    """
    major_version = sys.version_info[0]
    assert major_version == 2 or major_version == 3, "major_version = {!r}".format(major_version)
    return major_version == 2
    

def remove_process_serial_number(arg_list):
    """ Creates a copy of a list (typically sys.argv) where the strings that
        start with '-psn_0_' are removed.
        
        These are the process serial number used by the OS-X open command
        to bring applications to the front. They clash with argparse.
        See: http://hintsforums.macworld.com/showthread.php?t=11978
    """
    return [arg for arg in arg_list if not arg.startswith("-psn_0_")]


def prepend_point_to_extension(extension):
    """ Prepends a point to the extension of it doesn't already start with it
    """
    if extension.startswith('.'):
        return extension
    else:
        return '.' + extension

    

def string_to_identifier(s):
    """ Takes a string and makes it suitable for use as an identifier
    
        Translates to lower case
        Replaces spaces by underscores.
        Removes whitespace and punctuation.
    """
    import re
    s = s.lower()
    s = re.sub(r"\s+", "_", s) # replace whitespace with underscores
    s = re.sub(r"-", "_", s) # replace hyphens with underscores
    s = re.sub(r"[^A-Za-z0-9_]", "", s) # remove everything that's not a character, a digit or a _
    return s
    
    
if __name__ == "__main__":
    print (string_to_identifier("Pea\nsdf-43q45,.!@#%&@&@@24n  pijn  Kenter, hallo$"))
    
    
    
    