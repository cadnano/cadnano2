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

from rangeset import RangeSet
import util, sys
from vbase import VBase
from model.normalstrand import NormalStrand
import strand
util.qtWrapImport('QtCore', globals(), ['QObject', 'pyqtSignal'] )

class VStrand(QObject, RangeSet):
    """
    There are two of these per VirtualHelix. They provide the linear coordinate
    system in which VBase.vIndex() live.
    This subclass of RangeSet is designed to hold Segment items as its ranges.
    """
    didAddStrand = pyqtSignal(object)
    logger = None

    def __init__(self, parentVHelix=None):
        QObject.__init__(self)
        RangeSet.__init__(self)
        if parentVHelix != None:
            self._setVHelix(parentVHelix)
        #self.vHelix (set by _setVHelix)
        self.preserveLeftOligoDuringSplit = True
        # VFB = Visual FeedBack
        self.strandsWithActiveVfb = set()

    def __repr__(self):
        accesorToGetSelfFromvHelix = "????"
        if self == self.vHelix.scaf(): accesorToGetSelfFromvHelix = "scaf()"
        if self == self.vHelix.stap(): accesorToGetSelfFromvHelix = "stap()"
        return "v[%i].%s"%(self.vHelix.number(), accesorToGetSelfFromvHelix)

    def __call__(self, idx):
        return VBase(self, idx)

    ####################### Public Read API #######################
    # Useful inherited methods:
    #   vstr.get(idx)            get the segment at index idx (or None)
    #   vstr[idx]                same as get
    #   vstr.bounds()            returns a range containing all segments
    #                            this range is tight
    #   vstr.part()              the part containing vstr
    # Properties:
    #   vstr.vHelix

    def vComplement():
        """
        Returns the other VStrand in the VHelix that self is a child of.
        """
        vh = self.vHelix
        scaf, stap = vh.scaf(), vh.stap()
        if self == scaf:
            return stap
        assert(self == stap)
        return scaf

    def part(self):
        return self.vHelix.part()

    def isScaf(self):
        return self == self.vHelix.scaf()

    def isStap(self):
        return self == self.vHelix.stap()

    def drawn5To3(self):
        return self.vHelix.strandDrawn5To3(self)

    def model1String(self, *x):
        """ The 'old' model represented virtual strands and the connections
        between virtual bases on those strands with a string of the form
        illustrated below):
            "_,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,> <,> <,_ _,_"
        This example represents a three base strand on a 13 base vStrand.
        This method returns an identical representation of the receiver, where
        the first vBase printed is at vStrandStartIdx and the last is at
        vStrandAfterLastIdx-1. """
        if len(x) > 0:
            vStrandStartIdx, vStrandAfterLastIdx = x
        else:
            vStrandStartIdx, vStrandAfterLastIdx = 0, self.vHelix.numBases()
        ri = self._idxOfRangeContaining(vStrandStartIdx,\
                                        returnTupledIdxOfNextRangeOnFail=True)
        ranges = self.ranges
        bases = []
        prvIdxExists = int(self.get(vStrandStartIdx - 1) != None)
        curIdxExists = int(self.get(vStrandStartIdx) != None)
        lut = ('_,_', '_,_', 'ERR', '<,_', '_,_', '_,_', '_,>', '<,>')
        for i in range(vStrandStartIdx, vStrandAfterLastIdx):
            nxtIdxExists = int(self.get(i + 1) != None)
            bases.append(lut[prvIdxExists + 2*curIdxExists + 4*nxtIdxExists])
            prvIdxExists = curIdxExists
            curIdxExists = nxtIdxExists
        return " ".join(bases)

    def exposedEndsAt(self, vBase):
        """
        Returns 'L' or 'R' if a segment exists at vIdx and it
        exposes an unbound endpoint on its 3' or 5' end. Otherwise returns None.
        """
        return vBase.exposedEnds()

    def newStringRep(self):
        i, l = 1, len(self.ranges)
        prevStrand = None
        curStrand = self.ranges[0] if l else None
        strs = []
        while i <= l:  # Note: i is actually the index of nextStrand
            nextStrand = self.ranges[i] if i < l else None
            if prevStrand == curStrand.connL() != None:
                lCon = '<'
            elif curStrand.connL() != None:
                lCon = '<%s|'%curStrand.connL()
            else:
                lCon = '['
            if nextStrand == curStrand.connR() != None:
                rCon = '>'
            elif curStrand.connR() != None:
                rCon = '|%s>'%curStrand.connR()
            else:
                rCon = ']'
            lIdx, rIdx = self.idxs(curStrand)
            strs.append('%s%i|%s|%i%s'%\
                (lCon, lIdx, curStrand.kind, rIdx - 1, rCon))
            i += 1
            prevStrand, curStrand = curStrand, nextStrand
        return ''.join(strs)

    ####################### Public Write API #######################

    def addStrand(self, strand, useUndoStack=True, undoStack=None):
        # A strand is a rangeItem
        self.addRange(strand, useUndoStack, undoStack)

    def clearRange(self, firstIndex, afterLastIndex, useUndoStack=True, undoStack=None, keepLeft=True):
        self.removeRange(self, firstIndex, afterLastIndex, useUndoStack, undoStack, keepLeft=keepLeft)

    def resizeStrandAt(self, idxInStrand, newFirstBase, newLastBase, useUndoStack=True, undoStack=None):
        if isinstance(idxInStrand, VBase):
            idxInStrand = idxInStrand.vIndex
        if isinstance(newFirstBase, VBase):
            newFirstBase = newFirstBase.vIndex
        if isinstance(newLastBase, VBase):
            newLastBase = newLastBase.vIndex
        self.resizeRangeAtIdx(idxInStrand, newFirstBase,\
                              newLastBase + 1,\
                              useUndoStack, undoStack)

    def connectStrand(self, firstIdx, lastIdx, useUndoStack=True, undoStack=None):
        if useUndoStack and undoStack == None:
            undoStack = self.undoStack()
        if self.logger:
            self.logger.write('connectStrand(%i, %i) undoStack=%s\n'%\
                                      (firstIdx, lastIdx, undoStack))
        if undoStack:
            undoStack.beginMacro('connectStrand')
        if firstIdx == lastIdx:
            undoStack.endMacro()
            return
        elif firstIdx < lastIdx:
            lIdx, rIdx = firstIdx, lastIdx
            leftHasPrivelage = True
        elif lastIdx < firstIdx:
            lIdx, rIdx = lastIdx, firstIdx
            leftHasPrivelage = False

        lStrand = self.get(lIdx)
        rStrand = self.get(rIdx)
        lIsEnd = 'R' in VBase(self, lIdx).exposedEnds()
        rIsEnd = 'L' in VBase(self, rIdx).exposedEnds()
        lIsNormalStrand = isinstance(lStrand, NormalStrand)
        rIsNormalStrand = isinstance(rStrand, NormalStrand)
        if leftHasPrivelage:
            if self.logger: self.logger.write('\tleftPrivelage>')
            if lStrand == rStrand != None:
                if self.logger: self.logger.write('0drag\n')
                pass
            elif lIsNormalStrand and rIsNormalStrand:
                if self.logger: self.logger.write('lIsNorm&rIsNorm\n')
                rConnR = rStrand.connR()
                self.resizeStrandAt(lIdx, lStrand.vBaseL, rStrand.vBaseR, useUndoStack, undoStack)
                lStrand.setConnR(rConnR, useUndoStack, undoStack)
            elif lIdx + 1 == rIdx and lIsEnd and rIsEnd:
                if self.logger: self.logger.write('connect_adjacent_endpts\n')
                lStrand.setConnR(rStrand, useUndoStack, undoStack)
            elif lIsNormalStrand and rIsEnd:
                if self.logger: self.logger.write('lIsNorm&rIsEnd\n')
                self.resizeStrandAt(lIdx, lStrand.vBaseL, rIdx - 1, useUndoStack, undoStack)
                lStrand.setConnR(rStrand, useUndoStack, undoStack)
            elif rIsNormalStrand and lIsEnd:
                if self.logger: self.logger.write('rIsNorm&lIsEnd\n')
                self.resizeStrandAt(rIdx, lIdx + 1, rStrand.vBaseR, useUndoStack, undoStack)
                lStrand.setConnR(rStrand, useUndoStack, undoStack)
            elif lIsNormalStrand:
                if self.logger: self.logger.write('lIsNorm\n')
                self.resizeStrandAt(lIdx, lStrand.vBaseL, rIdx, useUndoStack, undoStack)
            elif rIsNormalStrand:
                if self.logger: self.logger.write('rIsNorm\n')
                self.resizeStrandAt(rIdx, lIdx, rStrand.vBaseR, useUndoStack, undoStack)
            else:
                if self.logger: self.logger.write('catchall\n')
                newStrand = NormalStrand(VBase(self, lIdx), VBase(self, rIdx))
                self.addStrand(newStrand)
        elif not leftHasPrivelage:
            if self.logger: self.logger.write('\trightPrivelage>')
            if lStrand == rStrand != None:
                if self.logger: self.logger.write('0drag\n')
                pass
            elif lIsNormalStrand and rIsNormalStrand:
                if self.logger: self.logger.write('lIsNorm&rIsNorm\n')
                lConnL = lStrand.connL()
                self.resizeStrandAt(rIdx, lStrand.vBaseL, rStrand.vBaseR, useUndoStack, undoStack)
                rStrand.setConnL(lConnL, useUndoStack, undoStack)
            elif lIdx + 1 == rIdx and lIsEnd and rIsEnd:
                if self.logger: self.logger.write('connect_adjacent_endpts\n')
                rStrand.setConnL(lStrand, useUndoStack, undoStack)
            elif rIsNormalStrand and lIsEnd:
                if self.logger: self.logger.write('rIsNorm&lIsEnd\n')
                self.resizeStrandAt(rIdx, lIdx + 1, rStrand.vBaseR, useUndoStack, undoStack)
                rStrand.setConnL(lStrand, useUndoStack, undoStack)
            elif lIsNormalStrand and rIsEnd:
                if self.logger: self.logger.write('lIsNorm&rIsEnd\n')
                self.resizeStrandAt(lIdx, lStrand.vBaseL, rIdx - 1, useUndoStack, undoStack)
                rStrand.setConnL(lStrand, useUndoStack, undoStack)
            elif rIsNormalStrand:
                if self.logger: self.logger.write('rIsNorm\n')
                self.resizeStrandAt(rIdx, lIdx, rStrand.vBaseR, useUndoStack, undoStack)
            elif lIsNormalStrand:
                if self.logger: self.logger.write('lIsNorm\n')
                self.resizeStrandAt(lIdx, lStrand.vBaseL, rIdx, useUndoStack, undoStack)
            else:
                if self.logger: self.logger.write('catchall\n')
                newStrand = NormalStrand(VBase(self, lIdx), VBase(self, rIdx))
                self.addStrand(newStrand, useUndoStack=useUndoStack, undoStack=undoStack)
        # End if leftHasPrivelage
        if self.logger:
            self.logger.write('\t%s\n'%self.newStringRep())
        if undoStack:
            undoStack.endMacro()

    ####################### Protected Framework Methods ##############
    # Note: the rangeItems of a VStrand are strands

    def idxs(self, rangeItem):
        """
        Returns (firstIdx, afterLastIdx) simplified representation of the
        rangeItem passed in.
        """
        return rangeItem.idxsOnStrand(self)

    def canMergeTouchingRangeItems(self, rangeItemA, rangeItemB):
        return rangeItemA.canMergeWithTouchingStrand(rangeItemB)
         
    def mergeRangeItems(self, rangeItemA, rangeItemB, undoStack):
        return rangeItemA.mergeWith(rangeItemB, undoStack)

    def changeRangeForItem(self, rangeItem, newStartIdx, newAfterLastIdx, undoStack):
        return rangeItem.changeRange(newStartIdx, newAfterLastIdx - 1, undoStack)

    def splitRangeItem(self, rangeItem, splitStart, splitAfterLast, keepLeft, undoStack):
        return rangeItem.split(splitStart,\
                               splitAfterLast,\
                               keepLeft,\
                               undoStack)

    def willRemoveRangeItem(self, strand):
        strand.willBeRemoved.emit(strand)
        if strand.logger != None:
            strand.logger.write("+%i.remove() %s\n"%(strand.traceID,\
                                                   repr(strand)))

    def didInsertRangeItem(self, strand):
        self.didAddStrand.emit(strand)
        if strand.logger != None:
            strand.logger.write("+%i.insert() %s\n"%(strand.traceID,\
                                                   repr(strand)))

    def boundsChanged(self):
        pass

    def undoStack(self):
        return self.vHelix.undoStack()

    ####################### Private Write API #######################
    def _setVHelix(self, newVH):
        """
        Should be called only by a VHelix adopting a VStrand as its child.
        """
        self.vHelix = newVH