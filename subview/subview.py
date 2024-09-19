#!/usr/bin/env python3
# This file is part of Subview.
#
# Subview is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# Subview is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# Subview. If not, see <https://www.gnu.org/licenses/>.

import PyQt5.QtWidgets as QtWidgets
import PyQt5.QtCore as QtCore
import PyQt5.QtGui as QtGui
import PyQt5.Qt as Qt
import krita as krita
import math as math
from os.path import dirname

DOCKER_TITLE = 'Subview'

class Subview(QtWidgets.QGraphicsView):
	transformUpdated = Qt.pyqtSignal()

	def __init__(self, scene, parent, pixmapItem):
		super().__init__(scene, parent)
		self.setAcceptDrops(True)
		self.pixmapItem = pixmapItem
		self.zoom = 0.0
		self.oldZoom = 0.0
		self.angle = 0.0
		self.oldAngle = 0.0
		self.point = None
		self.mirrored = False
		pass

	def resetView(self):
		if self.pixmapItem.pixmap().isNull():
			self.updateTransform()
			return
		size = self.pixmapItem.pixmap().size()
		maxLength = max(size.width(), size.height())
		self.setSceneRect(-maxLength, -maxLength, maxLength*2+size.width(), maxLength*2+size.height())
		self.centerOn(size.width()/2, size.height()/2)
		self.zoom = self.size().height() / size.height()
		self.angle = 0
		self.updateTransform()

	def updateTransform(self, emit=True):
		if self.pixmapItem.pixmap().isNull():
			self.resetTransform()
			return
		self.zoom = min(max( self.minZoom(), self.zoom), 32.0)
		self.angle = self.angle % 360
		self.resetTransform()
		self.scale(self.zoom, self.zoom)
		self.rotate(self.angle)
		if self.mirrored is True:
			self.scale(-1.0, 1.0)
		if emit is True:
			self.transformUpdated.emit()

	def minZoom(self):
		size = self.pixmapItem.pixmap().size()
		return (self.size().height() / size.height())*.15

	def dragEnterEvent(self, event):
		return self.parent().dragEnterEvent(event)

	def dropEvent(self, event):
		return self.parent().dropEvent(event)

	def mousePressEvent(self, event):
		self.oldZoom = self.zoom;
		self.oldAngle = self.angle;
		self.point = event.pos()
		if event.button() == QtCore.Qt.MiddleButton:
			# pretend we pressed left
			super().mousePressEvent(QtGui.QMouseEvent(
				event.type(),
				event.pos(),
				QtCore.Qt.LeftButton,
				QtCore.Qt.LeftButton,
				event.modifiers()
			));
		else:
			super().mousePressEvent(event);
		pass

	def mouseReleaseEvent(self, event):
		if event.button() == QtCore.Qt.MiddleButton:
			# pretend we released left
			super().mouseReleaseEvent(QtGui.QMouseEvent(
				event.type(),
				event.pos(),
				QtCore.Qt.LeftButton,
				QtCore.Qt.LeftButton,
				event.modifiers()
			));
		else:
			super().mouseReleaseEvent(event);
		pass

	def mouseMoveEvent(self, event):
		if event.modifiers() & QtCore.Qt.ControlModifier:
			self.oldAngle = self.angle;
			delta = self.point - event.pos()
			self.zoom = self.oldZoom + (delta.y() / 100) * self.oldZoom
			self.updateTransform()
			pass
		elif event.modifiers() & QtCore.Qt.ShiftModifier:
			self.oldZoom = self.zoom;
			center = QtCore.QPoint(self.size().width()//2, self.size().height()//2)
			delta = center - event.pos()
			theta = math.atan2(delta.y(), delta.x())
			delta = center - self.point
			theta = theta - math.atan2(delta.y(), delta.x())
			self.angle = self.oldAngle + math.degrees(theta)
			self.updateTransform()
			pass
		else:
			self.oldAngle = self.angle;
			self.oldZoom = self.zoom;
			super().mouseMoveEvent(event);
			pass

	def resizeEvent(self, event):
		self.updateTransform()

	def wheelEvent(self, event):
		numDegrees = event.angleDelta();
		if not numDegrees.isNull():
			self.zoom = self.zoom + (numDegrees.y() / 750) * self.zoom;
		self.updateTransform()
		event.accept();

class SubviewWidget(krita.DockWidget):
	zoomPresets = [
		25,
		33.33,
		50,
		66.66,
		75,
		100,
		200,
		300,
		400,
		600,
		800,
		1000,
		1200,
		1600,
		2000,
		2400,
		2800,
		3200,
	]

	def __init__(self):
		super().__init__()
		lastfile = Krita.readSetting("subview_docker", "lastfile", None)
		self.setWindowTitle(DOCKER_TITLE)
		self.setAcceptDrops(True)

		self.widget = QtWidgets.QWidget()

		self.layout = QtWidgets.QVBoxLayout(self)
		self.buttons = QtWidgets.QHBoxLayout(self)
		self.zoom = QtWidgets.QHBoxLayout(self)

		self.scene = QtWidgets.QGraphicsScene(self)
		self.pixmap = Qt.QPixmap()
		self.pixmapItem = self.scene.addPixmap(self.pixmap)
		self.pixmapItem.setTransformationMode(QtCore.Qt.SmoothTransformation)
		self.view = Subview(self.scene, self, self.pixmapItem)
		self.view.setDragMode(QtWidgets.QGraphicsView.NoDrag)
		self.view.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
		self.view.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
		self.view.setRenderHints(QtGui.QPainter.Antialiasing | QtGui.QPainter.SmoothPixmapTransform)
		self.view.transformUpdated.connect(self.transformUpdated)

		self.openButton = QtWidgets.QPushButton(self)
		self.openButton.setIcon(Krita.instance().icon("document-open"))
		self.openButton.pressed.connect(self.openFileDialog)
		self.openButton.setToolTip("Open image")

		self.resetButton = QtWidgets.QPushButton(self)
		self.resetButton.setIcon(Krita.instance().icon("view-refresh"))
		self.resetButton.pressed.connect(self.view.resetView)
		self.resetButton.setToolTip("Fit to view")

		self.mirrorButton = QtWidgets.QPushButton(self)
		self.mirrorButton.setIcon(Krita.instance().icon("mirror-view"))
		self.mirrorButton.toggled.connect(self.mirrorView)
		self.mirrorButton.setCheckable(True)
		self.mirrorButton.setToolTip("Mirror")

		self.closeButton = QtWidgets.QPushButton(self)
		self.closeButton.setIcon(Krita.instance().icon("dialog-cancel"))
		self.closeButton.pressed.connect(self.closeImage)
		self.closeButton.setToolTip("Close image")

		self.angleSpin = QtWidgets.QDoubleSpinBox(self)
		self.angleSpin.setToolTip("Angle")
		self.angleSpin.setWrapping(True)
		self.angleSpin.setMinimum(0) # TODO: [-180, 180] range
		self.angleSpin.setMaximum(360)
		self.angleSpin.setSingleStep(1.0)
		self.angleSpin.setSuffix("°")
		self.angleSpin.valueChanged.connect(self.angleSpun)

		self.buttons.addWidget(self.openButton, 0)
		self.buttons.addWidget(self.resetButton, 0)
		self.buttons.addWidget(self.mirrorButton, 0)
		self.buttons.addWidget(self.angleSpin, 0)
		self.buttons.addStretch(1)
		self.buttons.addWidget(self.closeButton, 0)

		self.zoomCombo = QtWidgets.QComboBox(self)
		self.zoomCombo.addItems(["%.2d%%" % x for x in self.zoomPresets])
		self.zoomCombo.currentIndexChanged.connect(self.comboChanged)

		self.zoomSlider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self)
		self.zoomSlider.setMinimum(0)
		self.zoomSlider.setMaximum(16000)
		self.zoomSlider.valueChanged.connect(self.sliderChanged)
		self.zoomSlider.setToolTip("Zoom")

		self.zoom.addWidget(self.zoomCombo, 0)
		self.zoom.addWidget(self.zoomSlider, 1)

		self.layout.addWidget(self.view, 1)
		self.layout.addLayout(self.buttons, 0)
		self.layout.addLayout(self.zoom, 0)

		self.layout.setStretch(0, 1)
		self.layout.setStretch(1, 0)

		self.enableControls(False)
		self.widget.setLayout(self.layout)
		self.setWidget(self.widget)

		if lastfile is not None:
			self.openImage(lastfile)
			self.view.resetView()

		pass

	def angleSpun(self, value):
		self.view.angle = value
		self.view.updateTransform(emit=False)

	def mirrorView(self, checked):
		self.view.mirrored = checked
		self.view.updateTransform()

	def comboChanged(self, idx):
		if idx >= 0 and idx < len(self.zoomPresets):
			self.view.zoom = self.zoomPresets[idx]/100.0
			self.view.updateTransform()

	def sliderChanged(self, newval):
		self.view.zoom = self.valueSliderToZoom(newval)
		self.view.updateTransform(emit=False)

	@Qt.pyqtSlot()
	def transformUpdated(self):
		self.zoomSlider.setValue(int(self.valueZoomToSlider(self.view.zoom)))
		self.angleSpin.setValue(self.view.angle)

	def valueSliderToZoom(self, x):
		# min .125, max 32
		minZoom = self.view.minZoom()
		return math.pow(32/minZoom, x/16000.0)*minZoom

	def valueZoomToSlider(self, x):
		# thanks wfa
		minZoom = self.view.minZoom()
		return (16000.0*math.log(x/minZoom)) / math.log(32/minZoom)

	def dragEnterEvent(self, event):
		if event.mimeData().hasUrls():
			event.acceptProposedAction()
		pass

	def dropEvent(self, event):
		urls = event.mimeData().urls()
		if len(urls) > 0:
			path = urls[0]
			if path.isLocalFile():
				self.openImage(path.toLocalFile());
				event.acceptProposedAction()
		pass

	def enableControls(self, enabled):
		self.resetButton.setEnabled(enabled)
		self.closeButton.setEnabled(enabled)
		self.zoomCombo.setEnabled(enabled)
		self.zoomSlider.setEnabled(enabled)
		if enabled is True:
			self.view.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
		else:
			self.view.setDragMode(QtWidgets.QGraphicsView.NoDrag)

	def closeImage(self):
		self.openImage("")

	def openImage(self, path):
		self.pixmap = Qt.QPixmap(path)
		self.pixmapItem.setPixmap(self.pixmap)
		self.enableControls(not self.pixmap.isNull())
		Krita.writeSetting("subview_docker", "lastfile", path)
		self.view.resetView()

	def openFileDialog(self):
		lastfile = Krita.readSetting("subview_docker", "lastfile", None)
		dlg = QtWidgets.QFileDialog(self, "Open an image file", "", "")
		dlg.setFileMode(QtWidgets.QFileDialog.ExistingFile)
		dlg.setAcceptMode(QtWidgets.QFileDialog.AcceptOpen)
		if lastfile is not None:
			dlg.setDirectory(dirname(lastfile))
		if dlg.exec():
			path = dlg.selectedFiles()[0];
			self.openImage(path);

	# notifies when views are added or removed
	# 'pass' means do not do anything
	def canvasChanged(self, canvas):
		pass

