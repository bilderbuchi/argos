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

""" Configuration tree. Can be used to manipulate the configuration of an inspector.

"""
from __future__ import print_function

import logging
from libargos.qt import Qt, QtCore, QtGui, QtSlot, widgetSubCheckBoxRect
from libargos.widgets.argostreeview import ArgosTreeView
from libargos.widgets.constants import RIGHT_DOCK_WIDTH
from libargos.config.configtreemodel import ConfigTreeModel
from libargos.config.basecti import InvalidInputError, CtiEditor

logger = logging.getLogger(__name__)

# Qt classes have many ancestors
#pylint: disable=R0901


class ConfigItemDelegate(QtGui.QStyledItemDelegate):
    """ Provides editing facilities for config tree items.
        Creates an editor based on the underlying config tree item at an index.
        
        We don't use a QItemEditorFactory since that is typically registered for a type of 
        QVariant. We then would have to make a new UserType QVariant for (each?) CTI.
        This is cumbersome and possibly unPyQTtonic :-)
    """
    def __init__(self, parent=None):
        super(ConfigItemDelegate, self).__init__(parent=parent)
        
        self.commitData.connect(self._onCommitData) # just for debugging.
        
    
    def paint(self, painter, option, index):

        painted = False
                
        if index.column() == ConfigTreeModel.COL_VALUE:

            # We take the value via the model to be consistent with setModelData
            value = index.model().data(index, Qt.EditRole) 
            cti = index.model().getItem(index)
            painted = cti.paintDisplayValue(painter, option, value)
        
        if not painted:
            super(ConfigItemDelegate, self).paint(painter, option, index)
        
    
    def createEditor(self, parent, option, index):
        """ Returns the widget used to change data from the model and can be reimplemented to 
            customize editing behavior.
            
            Reimplemented from QStyledItemDelegate.
        """
        logger.debug("ConfigItemDelegate.createEditor, parent: {!r}".format(parent.objectName()))
        assert index.isValid(), "sanity check failed: invalid index"
        
        cti = index.model().getItem(index)
        editor = cti.createEditor(self, parent, option)
        return editor
    

    def finalizeEditor(self, editor):
        """ Calls editor.finalize() if the editor is a CtiEditor, otherwise does nothing.    
        
            I know checking the object type is bad practice but this allows us to still use regular 
            widgets without having to wrap them in CtiEditors. Perhaps in the future we only will 
            use CtiEditors.
            
            Not part of the QAbstractItemView interface but added to be able to free resources.
            
            Note that, unlike the other methods of this class, finalizeEditor does not have an
            index parameter. We cannot derive this since indexForEditor is a private method in Qt.
            Therefore a CtiEditor maintains a reference to its config tree item and so cti.finalize
            can be called.
        """
        if isinstance(editor, CtiEditor):
            editor.finalize()
        else:
            logger.debug("Editor not a CtiEditor. No finalized() called.")

    # TODO: enforce the use of CtiEditors? In that case the setEditorData and setModelData calls
    # can call ctiEditor.setData and ctiEditor.getData. This would be consistent with finalizing.

    def setEditorData(self, editor, index):
        """ Provides the widget with data to manipulate.
            Calls the setEditorValue of the config tree item at the index. 
        
            :type editor: QWidget
            :type index: QModelIndex
            
            Reimplemented from QStyledItemDelegate.
        """
        # We take the config value via the model to be consistent with setModelData
        data = index.model().data(index, Qt.EditRole)
        cti = index.model().getItem(index)
        cti.setEditorValue(editor, data)
        

    def setModelData(self, editor, model, index):
        """ Gets data from the editor widget and stores it in the specified model at the item index.
            Does this by calling getEditorValue of the config tree item at the index.
            
            :type editor: QWidget
            :type model: ConfigTreeModel
            :type index: QModelIndex
            
            Reimplemented from QStyledItemDelegate.
        """
        logger.debug("ConfigItemDelegate.setModelData: editor {}".format(editor))
        cti = model.getItem(index)
        try:
            data = cti.getEditorValue(editor)
        except InvalidInputError as ex:
            logger.warn(ex)
        else:
            # The value is set via the model so that signals are emitted
            model.setData(index, data, Qt.EditRole)


    def updateEditorGeometry(self, editor, option, index):
        """ Ensures that the editor is displayed correctly with respect to the item view.
        """
        cti = index.model().getItem(index)
        if cti.checkState is None:
            displayRect = option.rect
        else:
            checkBoxRect = widgetSubCheckBoxRect(editor, option)
            offset = checkBoxRect.x() + checkBoxRect.width()
            displayRect = option.rect
            displayRect.adjust(offset, 0, 0, 0)

        editor.setGeometry(displayRect)
    
    
    def _onCommitData(self, editor):
        """ Logs when commitData signal is emitted. For debugging purposes """
        logger.debug("commitData signal emitted")
    
    
    @QtSlot()
    def commitAndCloseEditor(self, *args, **kwargs): # TODO: args?
        """ Calls the signals to commit the data and close the editor
        """
        #logger.debug("commitAndCloseEditor: {} {}".format(args, kwargs))
        editor = self.sender() # TODO somehow make parameter?
        self.commitData.emit(editor)
        self.closeEditor.emit(editor, QtGui.QAbstractItemDelegate.NoHint)        



class ConfigTreeView(ArgosTreeView):
    """ Tree widget for manipulating a tree of configuration options.
    """
    def __init__(self, configTreeModel):
        """ Constructor
        """
        super(ConfigTreeView, self).__init__(configTreeModel)

        self.setSelectionBehavior(QtGui.QAbstractItemView.SelectItems)
        
        treeHeader = self.header()
        treeHeader.resizeSection(ConfigTreeModel.COL_VALUE, RIGHT_DOCK_WIDTH / 2)

        headerNames = self.model().horizontalHeaders
        enabled = dict((name, True) for name in headerNames)
        enabled[headerNames[ConfigTreeModel.COL_NODE_NAME]] = False # Name cannot be unchecked
        enabled[headerNames[ConfigTreeModel.COL_VALUE]] = False # Value cannot be unchecked
        checked = dict((name, False) for name in headerNames)
        checked[headerNames[ConfigTreeModel.COL_NODE_NAME]] = True # Checked by default
        checked[headerNames[ConfigTreeModel.COL_VALUE]] = True # Checked by default
        self.addHeaderContextMenu(checked=checked, enabled=enabled, checkable={})

        self.setItemDelegate(ConfigItemDelegate())
        self.setEditTriggers(QtGui.QAbstractItemView.AllEditTriggers) 

        #self.setEditTriggers(QtGui.QAbstractItemView.DoubleClicked |
        #                     QtGui.QAbstractItemView.EditKeyPressed | 
        #                     QtGui.QAbstractItemView.AnyKeyPressed | 
        #                     QtGui.QAbstractItemView.SelectedClicked)
        
        
    def sizeHint(self):
        """ The recommended size for the widget."""
        return QtCore.QSize(RIGHT_DOCK_WIDTH, 500)
        
    
    @QtSlot(QtGui.QWidget, QtGui.QAbstractItemDelegate)
    def closeEditor(self, editor, hint):
        """ Finalizes, closes and releases the given editor. 
        """
        # It would be nicer if this method was part of ConfigItemDelegate since createEditor also
        # lives there. However, QAbstractItemView.closeEditor is sometimes called directly,
        # without the QAbstractItemDelegate.closeEditor signal begin emitted, e.g when the 
        # currentItem changes. Therefore we cannot connect to the QAbstractItemDelegate.closeEditor
        # signal to a slot in the ConfigItemDelegate.

        configItemDelegate = self.itemDelegate()
        configItemDelegate.finalizeEditor(editor)
        super(ConfigTreeView, self).closeEditor(editor, hint)

        