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

""" Repository tree.

    Currently it supports only selecting one item. That is, the current item is always the 
    selected item. 
    
    The difference between the current item and the selected item(s) is as follows:
    (from: http://doc.qt.digia.com/4.6/model-view-selection.html)
    
    In a view, there is always a current item and a selected item - two independent states. 
    An item can be the current item and selected at the same time. The view is responsible for 
    ensuring that there is always a current item as keyboard navigation, for example, requires 
    a current item.
            
    Current Item:
        There can only be one current item.    
        The current item will be changed with key navigation or mouse button clicks.    
        The current item will be edited if the edit key, F2, is pressed or the item is 
            double-clicked (provided that editing is enabled).    
        The current item is indicated by the focus rectangle.    

    Selected Items:
        There can be multiple selected items.
        The selected state of items is set or unset, depending on several pre-defined modes 
            (e.g., single selection, multiple selection, etc.) when the user interacts with the 
            items.
        The current item can be used together with an anchor to specify a range that should be 
            selected or deselected (or a combination of the two).
        The selected items are indicated with the selection rectangle.
"""
from __future__ import print_function

import logging
from libargos.qt import QtGui, QtCore, QtSlot
from libargos.qt.togglecolumn import ToggleColumnTreeView

from libargos.repo.repotreemodel import RepoTreeModel
from libargos.repo.filesytemrti import detectRtiFromFileName


logger = logging.getLogger(__name__)

# Qt classes have many ancestors
#pylint: disable=R0901

class RepoTreeView(ToggleColumnTreeView):
    """ Tree widget for browsing the data repository.
    """
    def __init__(self, repoTreeModel):
        """ Constructor
        """
        super(RepoTreeView, self).__init__()
        self.setModel(repoTreeModel)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.setHorizontalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.setAnimated(True)
        self.setAllColumnsShowFocus(True) 

        treeHeader = self.header()
        treeHeader.setMovable(True)
        treeHeader.setStretchLastSection(False)  
        treeHeader.resizeSection(RepoTreeModel.COL_NODE_NAME, 300)
        treeHeader.resizeSection(RepoTreeModel.COL_FILE_NAME, 500)
        headerNames = self.model().horizontalHeaders
        enabled = dict((name, True) for name in headerNames)
        enabled[headerNames[0]] = False # Fist column cannot be unchecked
        self.addHeaderContextMenu(enabled=enabled, checkable={})

        
    def loadRepoTreeItem(self, repoTreeItem, expand=False, 
                         position=None, parentIndex=QtCore.QModelIndex()):
        """ Loads a tree item in the repository and expands it.
            If position is None the child will be appended as the last child of the parent.
            Returns the index of the newly inserted RTI.
        """
        assert repoTreeItem.parentItem is None, "repoTreeItem {!r}".format(repoTreeItem)
        storeRootIndex = self.model().insertItem(repoTreeItem, position=position, 
                                                 parentIndex=parentIndex)
        self.setExpanded(storeRootIndex, expand)
        return storeRootIndex


    def loadFile(self, fileName, expand=False, rtiClass=None):
        """ Loads a file in the repository. Autodetects the RTI type if needed.
            Returns the index of the newly inserted RTI
        """
        if rtiClass is None:
            rtiClass = detectRtiFromFileName(fileName)
        repoTreeItem = rtiClass.createFromFileName(fileName)
        return self.loadRepoTreeItem(repoTreeItem, expand=expand)
    
    
    def setCurrentIndex(self, currentIndex):
        """ Sets the current item to be the item at currentIndex.
            Also select the row as to give consistent user feedback.
        """
        selectionModel = self.selectionModel()
        selectionFlags = (QtGui.QItemSelectionModel.ClearAndSelect | 
                          QtGui.QItemSelectionModel.Rows)
        selectionModel.setCurrentIndex(currentIndex, selectionFlags)  


    def _getCurrentIndex(self): # TODO: public?
        """ Returns the index of column 0 of the current item in the repository. 
            See also the notes at the top of this module on current item vs selected item(s).
        """
        selectionModel = self.selectionModel()
        #assert selectionModel.hasSelection(), "No selection"        
        curIndex = selectionModel.currentIndex()
        col0Index = curIndex.sibling(curIndex.row(), 0)
        return col0Index


    def _getCurrentItem(self):
        """ Find the current repo tree item (and the current index while we're at it)
            Returns a tuple with the current item, and its index.
            See also the notes at the top of this module on current item vs selected item(s).
        """
        currentIndex = self._getCurrentIndex()
        currentItem = self.model().getItem(currentIndex)
        return currentItem, currentIndex

    
    @QtSlot()
    def openCurrentItem(self):
        """ Opens the current item in the repository.
        """
        logger.debug("openCurrentItem")
        currentItem, currentIndex = self._getCurrentItem()
        currentItem.open()
        self.expand(currentIndex) # to visit the children and thus show the 'open' icons
         
        
    @QtSlot()
    def closeCurrentItem(self):
        """ Closes the current item in the repository. 
            All its children will be unfetched and closed.
        """
        logger.debug("closeCurrentItem")
        currentItem, currentIndex = self._getCurrentItem()
        
        # First we remove all the children, this will close them as well.
        self.model().removeAllChildrenAtIndex(currentIndex)
        currentItem.close()
        self.collapse(currentIndex) # otherwise the children will be fetched immediately

        
    @QtSlot()
    def removeCurrentFile(self):
        """ Finds the root of of the current item, which represents a file, 
            and removes it from the list.
        """
        logger.debug("removeCurrentFile")
        currentIndex = self._getCurrentIndex()
        topLevelIndex = self.model().findTopLevelItemIndex(currentIndex)
        self.model().deleteItemByIndex(topLevelIndex) # this will close the items resources.
        
        
    @QtSlot()
    def reloadFileOfCurrentItem(self):
        """ Finds the repo tree item that holds the file of the current item and reloads it.
            Reloading is done by removing the repo tree item and inserting a new one.
        """
        logger.debug("reloadFileOfCurrentItem")
        currentIndex = self._getCurrentIndex()
        fileRtiIndex = self.model().findFileRtiIndex(currentIndex)
        fileRtiParentIndex = fileRtiIndex.parent()
        fileRti = self.model().getItem(fileRtiIndex)
        fileName = fileRti.fileName
        rtiClass = type(fileRti)
        position = fileRti.childNumber()
        
        # Delete old RTI
        self.model().deleteItemByIndex(fileRtiIndex) # this will close the items resources.
        
        # Insert a new one instead.
        newRti = rtiClass.createFromFileName(fileName)
        newRtiIndex = self.loadRepoTreeItem(newRti, expand=True, position=position,  
                                            parentIndex=fileRtiParentIndex)
        self.setCurrentIndex(newRtiIndex)
        return newRtiIndex
     
