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

"""
virtualhelixitem.py

Created by Shawn on 2010-06-15.
"""

from views import styles
from model.virtualhelix import VirtualHelix
from model.enum import Parity, StrandType

import util
# import Qt stuff into the module namespace with PySide, PyQt4 independence
util.qtWrapImport('QtCore', globals(), ['Qt', 'QEvent', 'QString', 'QRectF',\
                                        'QPointF'])
util.qtWrapImport('QtGui', globals(), ['QGraphicsEllipseItem', \
                                'QGraphicsSimpleTextItem', 'QBrush', 'QPen'])

class VirtualHelixItem(QGraphicsEllipseItem):
    """
    The VirtualHelixItem is an individual circle that gets drawn in the SliceView
    as a child of the PartItem. Taken as a group, many SliceHelix
    instances make up the crossection of the DNAPart. Clicking on a SliceHelix
    adds a VirtualHelix to the DNAPart. The SliceHelix then changes appearence
    and paints its corresponding VirtualHelix number.
    """
    # set up default, hover, and active drawing styles
    useBrush = QBrush(styles.orangefill)
    usePen = QPen(styles.orangestroke, styles.SLICE_HELIX_STROKE_WIDTH)
    radius = styles.SLICE_HELIX_RADIUS
    outOfSlicePen = QPen(styles.lightorangestroke,\
                         styles.SLICE_HELIX_STROKE_WIDTH)
    outOfSliceBrush = QBrush(styles.lightorangefill)
    rect = QRectF(0, 0, 2 * radius, 2 * radius)
    font = styles.SLICE_NUM_FONT

    def __init__(self, virtualHelix, helixItem):
        """
        helixItem is a HelixItem that will act as a QGraphicsItem parent
        """
        super(VirtualHelixItem, self).__init__(parent=helixItem)
        self._virtualHelix = virtualHelix
        self._helixItem = helixItem
        self.hide()
        # drawing related
        self.focusRing = None
        self.beingHoveredOver = False
        self.setAcceptsHoverEvents(True)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setZValue(styles.ZSLICEHELIX)
        self.lastMousePressAddedBases = False
        self.setRect(self._rect)
        
        # handle the label specific stuff
        self._label = self.createLabel()
        self.setNumber()
        
        self.show()
    # end def
    
    ### SIGNALS ###

    ### SLOTS ###
    def numberChangedSlot(self, virtualHelix):
        """
        receives a signal containing a virtualHelix and the oldNumber 
        as a safety check
        """
        self.setNumber()
    # end def
    
    def removedSlot(self, virtualHelix):
        self._virtualHelix = None
        self._helixItem = None
        self.scene().removeItem(self)
    # end def
    
    ###
    
    def createLabel(self):
        label = QGraphicsSimpleTextItem("%d" % self._virtualHelix.number())
        label.setFont(self.font)
        label.setParentItem(self)
        return label
    # end def
    
    def setNumber(self):
        """docstring for setNumber"""
        vh = self._virtualHelix
        num = vh.number()
        label = self._label
        radius = self._radius
        
        label.setText("%d" % num)
        y_val = self.radius / 3
        if num < 10:
            label.setPos(radius / 1.5, y_val)
        elif num < 100:
            label.setPos(radius / 3, y_val)
        else: # _number >= 100
            label.setPos(0, y_val)
        posx = label.boundingRect().width()/2
        posy = label.boundingRect().height()/2
        label.setPos(radius-posx, radius-posy)
    # end def
    
    def destroyLabel(self):
        label = self._label
        label.scene().removeItem(label)
    # end def
    
    def part(self):
        return self._helixItem.part()

    def virtualHelix(self):
        return self._virtualHelix

    def number(self):
        return self.virtualHelix().number()

    # def isSelected(self):
    #     return self.focusRing != None
    # 
    # def setSelected(self, select):
    #     if select and not self.focusRing:
    #         self.focusRing = SliceHelix.FocusRingPainter(self.parentItem())
    #         self.focusRing.setPos(self.pos())
    #         self.focusRing.setZValue(styles.ZFOCUSRING)
    #     if not select and self.focusRing:
    #         self.focusRing.scene().removeItem(self.focusRing)
    #         self.focusRing = None
    # # end def
    
    # def selectAllBehavior(self):
    #     # If the selection is configured to always select
    #     # everything, we don't draw a focus ring around everything,
    #     # instead we only draw a focus ring around the hovered obj.
    #     if self.part() == None:
    #         return False
    #     else:
    #         return self.part().selectAllBehavior()
    # # end def

    ############################ Painting ############################
    class FocusRingPainter(QGraphicsItem):
        def paint(self, painter, option, widget=None):
            painter.setPen(SliceHelix.hovPen)
            painter.drawEllipse(SliceHelix.rect)

        def boundingRect(self):
            return SliceHelix.rect.adjusted(-1, -1, 2, 2)

    def paint(self, painter, option, widget=None):
        vh = self.virtualHelix()
        if vh:
            if vh.hasBaseAt(StrandType.Scaffold, self.part().activeSlice()):
                painter.setBrush(self.useBrush)
                painter.setPen(self.usePen)
            else:
                painter.setBrush(self.outOfSliceBrush)
                painter.setPen(self.outOfSlicePen)
            painter.drawEllipse(self.rect)
            num = QString(str(self.virtualHelix().number()))
            painter.setPen(Qt.SolidLine)
            painter.setBrush(Qt.NoBrush)
            painter.setFont(styles.SLICE_NUM_FONT)
            painter.drawText(0, 0, 2 * self.radius, 2 * self.radius,\
                             Qt.AlignHCenter + Qt.AlignVCenter, num)
        else:  # We are virtualhelix-less
            pass
            painter.setBrush(self.defBrush)
            painter.setPen(self.defPen)
            painter.drawEllipse(self.rect)
        if self.beingHoveredOver:
            painter.setPen(self.hovPen)
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(self.rect)

    ############################ User Interaction ############################
    def sceneEvent(self, event):
        """Included for unit testing in order to grab events that are sent
        via QGraphicsScene.sendEvent()."""
        # if self._parent.sliceController.testRecorder:
        #     coord = (self._row, self._col)
        #     self._parent.sliceController.testRecorder.sliceSceneEvent(event, coord)
        if event.type() == QEvent.MouseButtonPress:
            self.mousePressEvent(event)
            return True
        elif event.type() == QEvent.MouseButtonRelease:
            self.mouseReleaseEvent(event)
            return True
        elif event.type() == QEvent.MouseMove:
            self.mouseMoveEvent(event)
            return True
        QGraphicsItem.sceneEvent(self, event)
        return False

    def hoverEnterEvent(self, event):
        """
        If the selection is configured to always select
        everything, we don't draw a focus ring around everything,
        instead we only draw a focus ring around the hovered obj.
        """
        # if self.selectAllBehavior():
        #     self.setSelected(True)
        # forward the event to the helixItem as well
        self.helixItem.hoverEnterEvent(event)
    # end def

    def hoverLeaveEvent(self, event):
        # if self.selectAllBehavior():
        #     self.setSelected(False)
        self.helixItem.hoverEnterEvent(event)
    # end def

    # def mousePressEvent(self, event):
    #     action = self.decideAction(event.modifiers())
    #     action(self)
    #     self.dragSessionAction = action
    # 
    # def mouseMoveEvent(self, event):
    #     parent = self._helixItem
    #     posInParent = parent.mapFromItem(self, QPointF(event.pos()))
    #     # Qt doesn't have any way to ask for graphicsitem(s) at a
    #     # particular position but it *can* do intersections, so we
    #     # just use those instead
    #     parent.probe.setPos(posInParent)
    #     for ci in parent.probe.collidingItems():
    #         if isinstance(ci, SliceHelix):
    #             self.dragSessionAction(ci)
    # # end def

    # def mouseReleaseEvent(self, event):
    #     self.part().needsFittingToView.emit()

    # def decideAction(self, modifiers):
    #     """ On mouse press, an action (add scaffold at the active slice, add
    #     segment at the active slice, or create virtualhelix if missing) is
    #     decided upon and will be applied to all other slices happened across by
    #     mouseMoveEvent. The action is returned from this method in the form of a
    #     callable function."""
    #     vh = self.virtualHelix()
    #     if vh == None: return SliceHelix.addVHIfMissing
    #     idx = self.part().activeSlice()
    #     if modifiers & Qt.ShiftModifier:
    #         if vh.stap().get(idx) == None:
    #             return SliceHelix.addStapAtActiveSliceIfMissing
    #         else:
    #             return SliceHelix.nop
    #     if vh.scaf().get(idx) == None:
    #         return SliceHelix.addScafAtActiveSliceIfMissing
    #     return SliceHelix.nop
    # 
    # def nop(self):
    #     pass
