# The MIT License
#
# Copyright (c) 2011 Wyss Institute at Harvard University
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
# http://www.opensource.org/licenses/mit-license.php

import util, sys
util.qtWrapImport('QtCore', globals(), ['QObject'])
from model.normalstrand import NormalStrand
from operation import Operation
from model.vbase import VBase

class PencilToolOperation(Operation):
    """ Handles interactive strand creation / destruction in the manner of the
    pencil tool """
    logger = None
    def __init__(self, startVBase, undoStack):
        """ Begin a session of pencil-tool interaction """
        Operation.__init__(self, undoStack)
        self.newStrand = NormalStrand(startVBase, startVBase)
        self.startVBase = startVBase
        self.lastDestVBase = startVBase
        self.newStrandInVfbPool = False
        self.updateOperationWithDestination(startVBase)
        if self.logger:
            self.logger.write('PencilToolOperation.init(%s)\n'%startVBase)

    def updateOperationWithDestination(self, newDestVBase):
        """ Looks at self.startVBase and newDestVBase then calls the appropriate
        actionWhatever method on self. """
        if isinstance(newDestVBase, (int, long)):
            newDestVBase = VBase(self.startVBase.vStrand, newDestVBase)
        if newDestVBase == self.lastDestVBase:
            return
        else:
            self.lastDestVBase = newDestVBase
        self.rewind()
        dragStartBase, dragEndBase = self.startVBase, newDestVBase
        dragStartExposedEnds = dragStartBase.exposedEnds()
        dragStartStrand = dragStartBase.strand()
        dragEndExposedEnds = dragEndBase.exposedEnds()
        dragEndStrand = dragEndBase.strand()
        vStrand = dragStartBase.vStrand

        if not isinstance(newDestVBase, VBase):
            return

        vStrand.connectStrand(dragStartBase.vIndex, dragEndBase.vIndex, useUndoStack=True, undoStack=self.undoStack)

    def end(self):
        """ Make the changes displayed by the last call to
        updateOperationWithDestination permanent """
        if self.logger:
            self.logger.write('PencilToolOperation.end\n')
        del self.newStrand
        del self.startVBase
        del self.newStrandInVfbPool

    def actionNone(self):
        if self.logger:
            self.logger.write('PencilToolOperation.actionNone\n')

    def actionAddStrand(self, lConnection, startBase, endBase, rConnection):
        if self.logger:
            self.logger.write('PencilToolOperation.actionAddStrand\n')
        newStrand, undoStack = self.newStrand, self.undoStack
        undoStack.beginMacro('actionAddStrand')
        newStrand.changeRange(startBase, endBase, undoStack)
        startBase.vStrand.addStrand(newStrand, useUndoStack=True, undoStack=undoStack)
        newStrand.setConnL(lConnection, useUndoStack=True, undoStack=undoStack)
        newStrand.setConnR(rConnection, useUndoStack=True, undoStack=undoStack)
        undoStack.endMacro()

    def actionJustConnect(self, lStrand, rStrand):
        """ Just connect the right exposed end of lStrand to the left exposed
        end of rStrand """
        if self.logger:
            self.logger.write('PencilToolOperation.actionJustConnect\n')
        lStrand.setConnR(rStrand, useUndoStack=True, undoStack=self.undoStack)

    def actionResizeStrand(self, strand, newL, newR):
        if self.logger:
            self.logger.write('PencilToolOperation.actionResizeStrand\n')
        newL.vStrand.resizeStrandAt(strand.vBaseL, newL, newR, useUndoStack=True, undoStack=self.undoStack)

    def actionClearRange(self, firstIdx, afterLastIdx, keepLeft=True):
        if self.logger:
            self.logger.write('PencilToolOperation.actionClearRange\n')
        self.startVBase.vStrand.clearRange(firstIdx,\
                                           afterLastIdx,\
                                           useUndoStack=True,\
                                           undoStack=self.undoStack,\
                                           keepLeft=keepLeft)