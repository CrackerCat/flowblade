"""
    Flowblade Movie Editor is a nonlinear video editor.
    Copyright 2012 Janne Liljeblad.

    This file is part of Flowblade Movie Editor <http://code.google.com/p/flowblade>.

    Flowblade Movie Editor is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    Flowblade Movie Editor is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Flowblade Movie Editor.  If not, see <http://www.gnu.org/licenses/>.
"""
from gi.repository import Gtk, Gdk
import cairo

import cairoarea
import guiutils
import dialogutils
import gui
import respaths

SELECTED_BG = (0.1, 0.31, 0.58,1.0)

PANEL_MEDIA = 0
PANEL_FILTERS = 1
PANEL_COMPOSITORS = 2
PANEL_RANGE_LOG = 3
PANEL_RENDERING = 4
PANEL_JOBS = 5
PANEL_PROJECT = 6
PANEL_PROJECT_SMALL_SCREEN = 7
PANEL_MEDIA_AND_BINS_SMALL_SCREEN = 8

CONTAINER_T1 = 0
CONTAINER_T2 = 1
CONTAINER_B1 = 2

TOP_ROW = 0
BOTTOM_ROW = 1

TOP_ROW_LAYOUT_DEFAULT_THREE = 0
TOP_ROW_LAYOUT_MONITOR_CENTER_THREE = 1
TOP_ROW_LAYOUT_TWO_ONLY = 2
BOTTOM_ROW_LAYOUT_TLINE_ONLY = 3
BOTTOM_ROW_LAYOUT_PANEL_LEFT = 4
BOTTOM_ROW_LAYOUT_PANEL_RIGHT = 5

LAYOUT_IMAGES = {   TOP_ROW_LAYOUT_DEFAULT_THREE:"layout_t_default",
                    TOP_ROW_LAYOUT_MONITOR_CENTER_THREE:"layout_t_monitor_center",
                    TOP_ROW_LAYOUT_TWO_ONLY:"layout_t_two_only",
                    BOTTOM_ROW_LAYOUT_TLINE_ONLY:"layout_b_tline_only",
                    BOTTOM_ROW_LAYOUT_PANEL_LEFT:"layout_b_panel_left",
                    BOTTOM_ROW_LAYOUT_PANEL_RIGHT:"layout_b_panel_right"}

LAYOUT_ITEM_WIDTH = 150
LAYOUT_ITEM_HEIGHT = 100

# These are set on dialog launch when trnaslations quaranteed to be initialized.
PANELS_DATA = None
CONTAINERS_NAMES = {CONTAINER_T1: "T1",
                    CONTAINER_T2: "T2",
                    CONTAINER_B1: "B1" }

# --------------------------------------------------------------- DIALOG GUI
def show_configuration_dialog():
    global PANELS_DATA
    PANELS_DATA = { PANEL_MEDIA: (True, _("Media Panel")),
                    PANEL_FILTERS: (True,_("Filters Panel")),
                    PANEL_COMPOSITORS: (True,_("Compositors Panel")),
                    PANEL_RANGE_LOG:(True, _("Range Log Panel")),
                    PANEL_RENDERING:(True, _("Render Panel")),
                    PANEL_JOBS: (True,_("Jobs panel")),
                    PANEL_PROJECT: (True, _("Project Panel")),
                    PANEL_PROJECT_SMALL_SCREEN: (True, _("Project Panel Small Screen")),
                    PANEL_MEDIA_AND_BINS_SMALL_SCREEN: (True, _("Media and Binss Panel Small Screen")) }
    
    dialog = Gtk.Dialog(_("Editor Preferences"), None,
                    Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                    (_("Cancel"), Gtk.ResponseType.REJECT,
                    _("OK"), Gtk.ResponseType.ACCEPT))

    panel = _get_edit_panel()

    dialog.connect('response', _configuration_dialog_callback)
    dialog.vbox.pack_start(panel, True, True, 0)
    dialogutils.set_outer_margins(dialog.vbox)
    dialogutils.default_behaviour(dialog)
    dialog.set_transient_for(gui.editor_window.window)
    dialog.show_all()

def _configuration_dialog_callback(dialog, response_id):

    if response_id == Gtk.ResponseType.ACCEPT:
        #editorpersistance.save()
        dialog.destroy()

        return

    dialog.destroy()


def _get_edit_panel():
    
    top_row = LayoutSelectRow(TOP_ROW, selection_changed_callback)
    top_row.add_selection_item(LayoutSelectItem(TOP_ROW_LAYOUT_DEFAULT_THREE))
    top_row.add_selection_item(LayoutSelectItem(TOP_ROW_LAYOUT_MONITOR_CENTER_THREE))
    top_row.add_selection_item(LayoutSelectItem(TOP_ROW_LAYOUT_TWO_ONLY))

    bottom_row = LayoutSelectRow(TOP_ROW, selection_changed_callback)
    bottom_row.add_selection_item(LayoutSelectItem(BOTTOM_ROW_LAYOUT_TLINE_ONLY))
    bottom_row.add_selection_item(LayoutSelectItem(BOTTOM_ROW_LAYOUT_PANEL_LEFT))
    bottom_row.add_selection_item(LayoutSelectItem(BOTTOM_ROW_LAYOUT_PANEL_RIGHT))

    layout_data = LayoutData()
    layout_data.available_containers.append(CONTAINER_T1)
    layout_data.available_containers.append(CONTAINER_B1)

    container_select_panel = Gtk.VBox(False, 2)
    for panel in PANELS_DATA:
        select_row = PanelContainerSelect(panel, layout_data)
        container_select_panel.pack_start(select_row.widget, False, False, 0)
        
    pane = Gtk.VBox(False, 2)
    pane.pack_start(guiutils.bold_label(_("Top Row Layout")), False, False, 0)
    pane.pack_start(top_row.widget, False, False, 0)
    pane.pack_start(guiutils.bold_label(_("Bottom Row Layout")), False, False, 0)
    pane.pack_start(bottom_row.widget, False, False, 0)
    pane.pack_start(container_select_panel, False, False, 0)

    return pane



class LayoutData:
    def __init__(self):
        self.available_containers = []

    def get_available_containers(self):
        return self.available_containers


class LayoutSelectRow:
    def __init__(self, row, selection_changed_callback):
        self.row = row
        self.selection_items = []
        self.selection_changed_callback = selection_changed_callback
        
        self.widget = Gtk.HBox(False, 2)
        
    def add_selection_item(self, item):
        self.selection_items.append(item)
        self.widget.pack_start(item.widget, False, False, 0)
        
        item.set_change_listener(self)
        
    def item_selected(self, layout):
        for item in self.selection_items:
            if item.layout == layout:
                item.selected = True
            else:
                item.selected = False
            item.widget.queue_draw()
    
        self.selection_changed_callback(self.row, layout)


class LayoutSelectItem:

    def __init__(self, layout):
        self.widget = cairoarea.CairoDrawableArea2(LAYOUT_ITEM_WIDTH, LAYOUT_ITEM_HEIGHT, self._draw)
        self.widget.press_func = self._press
        self.layout = layout
        image_path = respaths.IMAGE_PATH + LAYOUT_IMAGES[layout] + ".png"
        self.layout_image_surface = cairo.ImageSurface.create_from_png(image_path)
        self.change_listener = None
        self.selected = False

    def set_change_listener(self, change_listener):
        self.change_listener = change_listener

    def _press(self, event):
         self.change_listener.item_selected(self.layout)

    def _draw(self, event, cr, allocation):
        x, y, w, h = allocation

        # Draw bg
        if self.selected == True:
            color = SELECTED_BG
        else:
            color = gui.get_bg_color()

        cr.set_source_rgba(*color)
        cr.rectangle(0, 0, w, h)
        cr.fill()

        # Draw layout img
        cr.set_source_surface(self.layout_image_surface, 0, 0)
        cr.paint()


class PanelContainerSelect:
    
    def __init__(self, panel, layout_data):
        self.panel = panel
        
        always_visible, name = PANELS_DATA[panel]
        
        container_select_combo = Gtk.ComboBoxText()
        selection_values = []
        if always_visible == False:
            container_select_combo.append_text(_("Not shown"))
            selection_values.append(None)
        
        available_containers = layout_data.get_available_containers()

        for container in available_containers:
            selection_values.append(container)
            container_select_combo.append_text(CONTAINERS_NAMES[container])

        container_select_combo.set_active(0)
        
        self.widget = Gtk.HBox(False, 2)
        self.widget.pack_start(guiutils.get_right_justified_box([Gtk.Label(label=name)]), False, False, 0)
        self.widget.pack_start(container_select_combo, False, False, 0)
        


# ----------------------------------------------------------------------- CHANGING LAYOUT DATA
def selection_changed_callback(row, layout):
    print(row, layout)


