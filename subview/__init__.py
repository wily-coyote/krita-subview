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

from krita import DockWidgetFactory, DockWidgetFactoryBase
from .subview import SubviewWidget

DOCKER_ID = 'subview_docker'
instance = Krita.instance()
dock_widget_factory = DockWidgetFactory(DOCKER_ID,
                                        DockWidgetFactoryBase.DockRight,
                                        SubviewWidget)

instance.addDockWidgetFactory(dock_widget_factory)
