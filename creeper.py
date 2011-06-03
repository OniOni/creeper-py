import wnck, gtk, gobject
import time, datetime
import pickle

class Creeper(object):
    """lurk moar
    """
    
    def __init__(self):
        """Init
        """
        
        self.callbacks = []

        self.screen = wnck.screen_get_default()
        self.screen.force_update()

        self.screen.connect('active-window-changed',
                            self.onChange)
        
        self._last = self.screen.get_active_window().get_application()

        self._start = time.time()
        

    def addCallback(self, callback):
        """
        Add function to be called on changed active window
        """

        self.callbacks += [callback]



    def onChange(self, screen, last, data=None):
        """
        """
        self.screen.force_update()        
        try:
            current = self.screen.get_active_window().get_application()
            
            for callback in self.callbacks:
                callback(self._last.get_name(), 
                         self._last.get_icon())

            self._last = current
        except AttributeError as e:
            print e
            pass
        
    def uptime(self):
        """Get deamon running time
        
        Arguments:
        - `self`:
        """
        return time.time() - self._start



class Statifier(object):
    """Build info about active windows
    """
    
    def __init__(self, creeper):
        """Init
        
        Arguments:
        - `creeper`:
        """
        self._creeper = creeper
        self._creeper.addCallback(self.onUpdate)

        self.persis = Persitefier('dump')

        self.last = time.time()
        self.load()
        self._pause = False
        self._current = ''


    
    def toggle_pause(self, data=None):
        """
        """
        self._pause = not self._pause

        if not self._pause:
            self._last = time.time()
        
    def __spent(self):
        now = time.time()
        ret = now - self.last if not self._pause else 0
        self.last = now
        return ret
            

    def onUpdate(self, name, icon):
        """Called when active window changes
        
        Arguments:
        - `self`:
        - `name`:
        - `icon`:
        """
        self._current = name

        spent = self.__spent()
        
        print name, spent
        
        try:
            self._data[name]['time'] += spent
        except KeyError:
            self._data[name] = {}
            self._data[name]['time'] = spent
            self._data[name]['icon'] = icon


    def getData(self):
        """Return stats about active windows
        """
        for k in self._data:
            time = int(self._data[k]['time'])
            yield (self._data[k]['icon'], 
                   k, 
                   #self._data[k]['time'] if k != self._current else self._data[k]['time'] + self.__spent(),  
                   str(time) + " s" if time < 60 else str(time/60) + " m",
                   str(int((self._data[k]['time']/self._creeper.uptime())) * 100) + "%"
                   )
    
    def save(self, w=None):
        """Save State of Statifier
        
        Arguments:
        - `self`:
        """
        to_save = self._data

        for k in to_save:
            to_save[k]['icon'].save(k+'.png', 'png')
            to_save[k]['icon'] = k+'.png'

        self.persis.write(to_save)

    def load(self):
        """Load saved state of Statifier
        
        Arguments:
        - `self`:
        """
        self._data = self.persis.read()

        print self._data

        for k in self._data:
            self._data[k]['icon'] = gtk.gdk.pixbuf_new_from_file(self._data[k]['icon'])

        print self._data

    

class Persitefier(object):
    """
    Create persistance contexte for saving objects with gdk.pixbuff
    Based on pickle
    """
    
    def __init__(self, file):
        """
        
        Arguments:
        - `file`:
        """
        self._file = file
        

    def write(self, obj):
        """
        Write object to persistance context
        """
        fd = open(self._file, 'w')
        pickle.dump(obj, fd)


    def read(self):
        """
        
        Arguments:
        - `self`:
        """
        fd = open(self._file, 'r')
        return pickle.load(fd)



class MainWin(object):
    """Main window for Creeper
    """
    
    def __init__(self, ui):
        """Init MainWin
        
        Arguments:
        - `ui`:
        """
        self.c = Creeper()

        self.s = Statifier(self.c)
        #self.s.load()
        
        self.buildable = gtk.Builder()
        self.buildable.add_from_file(ui)

        #Setting up MainWin
        self.MainWin = self.buildable.get_object('MainWin')
        self.MainWin.set_title("Creeper-py")
        self.MainWin.connect('destroy', lambda x: gtk.main_quit)

        #Setting up BRefresh
        self.BRefresh = self.buildable.get_object('BRefresh')
        self.BRefresh.connect('pressed', self.refresh)

        #Setting up BQuit
        self.BQuit = self.buildable.get_object('BQuit')
        self.BQuit.connect('pressed', lambda x: gtk.main_quit)

        #Setting up BSave
        self.BSave = self.buildable.get_object('BSave')
        self.BSave.connect('pressed', self.s.save)

        #Setting up pause
        self.pause = self.buildable.get_object('pause')
        self.pause.connect('pressed', self.s.toggle_pause)
        

        self.app_store = self.buildable.get_object('app_store')

        self.TreeView = self.buildable.get_object('AppTreeView')

        # create a CellRenderer to render the data
        self.cell = gtk.CellRendererText()
        self.cell_pix = gtk.CellRendererPixbuf()

        # create the TreeViewColumns to display the data
        self.tvcolumn = gtk.TreeViewColumn('Icon', self.cell_pix)
        self.tvcolumn1 = gtk.TreeViewColumn('Name', self.cell)
        self.tvcolumn2 = gtk.TreeViewColumn('Total Time', self.cell)
        self.tvcolumn3 = gtk.TreeViewColumn('%', self.cell)

        self.tvcolumn.add_attribute(self.cell_pix, 'pixbuf', 0)
        self.tvcolumn1.add_attribute(self.cell, 'text', 1)
        self.tvcolumn2.add_attribute(self.cell, 'text', 2)
        self.tvcolumn3.add_attribute(self.cell, 'text', 3)

        self.TreeView.append_column(self.tvcolumn)
        self.TreeView.append_column(self.tvcolumn1)
        self.TreeView.append_column(self.tvcolumn2)
        self.TreeView.append_column(self.tvcolumn3)

        self.MainWin.show_all()

    def update(self, name, icon):
        """Update list
        
        Arguments:
        - `name`:
        - `icon`:
        """
        print name, icon
        try: 
            self.app_store.append([name, icon])
        except:
            print self.app_store.get_n_columns()

    def refresh(self, button):
        """Refresh info in 
        """
        d = self.s.getData()

        self.app_store.clear()

        for t in d:
            self.app_store.append(t);

    

if __name__ == '__main__':
    w = MainWin('ui.glade')

    gtk.main()


    
