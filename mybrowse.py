#!/usr/bin/python3
import gi
gi.require_version('WebKit2', '4.0')
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, WebKit2, Gdk
import configparser
import os
import sys

browser_id = 'MyBrowse 0.1'

conf_dir = f"{os.path.expanduser('~')}/.config/mybrowse/"

link_list = {"QWant Lite": "https://lite.qwant.com/", 
            "Ubuntu Users Forum": "https://forum.ubuntuusers.de/last12/", 
            "Google": "https://google.de",
            "Linux Mint Users": "https://www.linuxmintusers.de"
            }

name_list = []
url_list = []

for link in link_list.items():
    name = link[0]
    url = link[1]
    name_list.append(name)
    url_list.append(url)

css = """
#addressbar progress
{
   background: #e9f3ff;
   border: 1px;
}
.button :hover
{
   background: #ace;
   color: #222;
}
#window {
        background-color: #eee;
}
popover {
    background: #666;
    color: #eee;
    font-size: 9pt;
}
"""

if not os.path.exists(conf_dir):
    try:
        os.makedirs(conf_dir)
    except OSError as e:
        print(e)
        pass

config = configparser.ConfigParser()

config.read(conf_dir + 'mybrowse.cfg')
if not os.path.isfile(conf_dir + 'mybrowse.cfg'):
    print("no config file found")
    

class Browser(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title='MyBrowse')
        
        if len(sys.argv) > 1:
            self.startpage = sys.argv[1]
        else:
            self.startpage = config['General']['home']
        print(f'{self.startpage}')
        
        self.set_name("window")
        self.view = WebKit2.WebView()
        self.view.set_zoom_level(0.9)
        self.connect("key-press-event", self.on_key_event)
        self.view.connect("notify::title", self.change_title)
        self.view.connect("notify::uri", self.change_uri)
        self.view.connect("notify::estimated-load-progress", self.load_progress)
        self.vbox = Gtk.Box(orientation=Gtk.STYLE_CLASS_VERTICAL, 
                            margin_left=5, margin_right=5, spacing=4)
        self.vbox.expand = True
        self.set_icon_name("browser")
#        self.set_icon_from_file(conf_dir + 'mybrowse.png')

        # buttons
        self.menu = Gtk.Box(orientation=Gtk.STYLE_CLASS_HORIZONTAL, spacing=4)
        self.menu.expand = False
        self.back = Gtk.Button()
        self.back_arrow = Gtk.Image.new_from_icon_name('go-previous', 2)
        self.back.add(self.back_arrow)
        self.menu.add(self.back)
        self.forward = Gtk.Button()
        self.forward_arrow = Gtk.Image.new_from_icon_name('go-next', 2)
        self.forward.add(self.forward_arrow)
        self.menu.add(self.forward)
        self.reload = Gtk.Button()
        self.reload_arrow = Gtk.Image.new_from_icon_name('view-refresh', 2)
        self.reload.add(self.reload_arrow)
        self.menu.add(self.reload)
        self.home = Gtk.Button()
        self.home_arrow = Gtk.Image.new_from_icon_name('go-home', 2)
        self.home.add(self.home_arrow)
        self.menu.add(self.home)
        
        # addressbar
        self.addressbar = Gtk.Entry()
        self.addressbar.set_name("addressbar")
        self.addressbar.set_text(self.startpage)
        self.addressbar.set_width_chars(75)
        self.addressbar.set_progress_pulse_step(0.2)
        self.menu.pack_start(self.addressbar, False, False, 20)

        # searchbar
        self.searchbar = Gtk.SearchEntry()
        self.searchbar.set_placeholder_text("find")
        self.searchbar.connect("activate", self.do_search)
        self.searchbar.set_width_chars(32)
        self.menu.pack_end(self.searchbar, False, False, 10)
        
#        # popover links
        self.popover = Gtk.Popover()
        self.popover.set_property('margin', 0)
        link_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
   
        for x in range(len(name_list)):
            url_btn = Gtk.ModelButton(label=name_list[x])
            link_box.pack_start(url_btn, False, True, 2)
            url_btn.connect("clicked", self.item_activated, x)            
            
        # show menu
        link_box.show_all()
        self.popover.add(link_box)
        self.popover.set_position(Gtk.PositionType.BOTTOM)
        img = Gtk.Image.new_from_icon_name("browser", 2)
        button = Gtk.MenuButton(label="Links", image=img, popover=self.popover, relief=2)
        self.menu.pack_end(button, False, False, 20)
        
        # style
        provider = Gtk.CssProvider()
        provider.load_from_data(bytes(css.encode()))
        style = self.get_style_context()
        style.add_class("button")
        screen = Gdk.Screen.get_default()
        priority = Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        style.add_provider_for_screen(screen, provider, priority) 
        
        # search inside page
        self.page_finder = WebKit2.FindController(web_view=self.view)
        self.search_win = Gtk.SearchBar()
        self.searchentry = Gtk.SearchEntry()
        self.searchentry.connect("activate", self.find_in_page)
        self.search_win.connect_entry(self.searchentry)
        self.search_win.add(self.searchentry)
        self.vbox.pack_end(self.search_win, False, False, 2)
        
        # connect
        self.addressbar.connect("activate", self.change_url)
        self.back.connect("clicked", self.go_back)
        self.forward.connect("clicked", self.go_forward)
        self.reload.connect("clicked", self.go_reload)
        self.home.connect("clicked", self.go_home)
        self.vbox.add(self.menu)

        self.sw = Gtk.ScrolledWindow()
        self.sw.add(self.view)

        self.vbox.pack_start(self.sw, True, True, 0)
        self.add(self.vbox)
        self.view.load_uri(self.startpage)


    def change_url(self, widget):
        url = self.addressbar.get_text()
        self.view.load_uri(url)

    def go_back(self, widget):
        self.view.go_back()

    def go_forward(self, widget):
        self.view.go_forward()

    def go_reload(self, widget):
        self.view.reload()

    def go_home(self, widget):
        self.addressbar.set_text(self.startpage)
        self.view.load_uri(self.startpage)

    def change_title(self, widget, data, *arg):
        title = widget.get_title()
        self.set_title(title)
        
    def change_uri(self, widget, data, *arg):
        uri = widget.get_uri()
        self.addressbar.set_text(uri)

    def load_progress(self, widget, data, *arg):
        progress = widget.get_estimated_load_progress()
        self.addressbar.set_progress_fraction(progress)

    def do_search(self, widget):
        search_text = f'"{self.searchbar.get_text()}"'
        print(f"searching for '{search_text}'")
        search_url = f"{self.startpage}search?q={search_text}"
        self.addressbar.set_text(search_url)
        self.view.load_uri(search_url)
        
    def url_btn_1_clicked(self, *args):
        url = "https://lite.qwant.com/"
        self.addressbar.set_text(url)
        self.view.load_uri(url)
        
    def url_btn_2_clicked(self, *args):
        url = "https://forum.ubuntuusers.de/last12/"
        self.addressbar.set_text(url)
        self.view.load_uri(url)
        
    def url_btn_3_clicked(self, *args):
        url = "https://google.de"
        self.addressbar.set_text(url)
        self.view.load_uri(url)
        
    def on_key_event(self, widget, event, *args):
        kname  = Gdk.keyval_name(event.keyval)
        if event.keyval == 65288:
            self.view.go_back()
        if (kname == "f" and
            event.state == Gdk.ModifierType.CONTROL_MASK):
            if self.search_win.get_search_mode():
                self.search_win.set_search_mode(False)
                self.page_finder.search_finish()
            else:
                self.search_win.set_search_mode(True)
                self.find_in_page()
        if kname == "Escape":
            self.page_finder.search_finish()
        
    def item_activated(self, wdg, i):
        url = url_list[i]
        self.view.load_uri(url)
        
    def find_in_page(self, *args):
        search_text = self.searchentry.get_text()
        if not search_text == "":
            self.page_finder.search(search_text, 1, 500)

        
if __name__ == "__main__":
    browser = Browser()
    browser.set_default_size(1024, 704)
    #browser.resize(1200, 900)
    browser.move(0, 0)
    browser.connect("delete-event", Gtk.main_quit)
    browser.show_all()
    browser.maximize()
    Gtk.main()
