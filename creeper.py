import wnck
import gtk, gobject, time, datetime
import redis

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
        
        self._last = self.screen.get_active_window()        

        self._start = time.time()
        
        self._pause = False



    def addCallback(self, callback):
        """
        Add function to be called on changed active window
        """

        self.callbacks += [callback]



    def toggle_pause(self, data):
        """
        Toggle state count/pause
        """
        self._pause = not self._pause



    def onChange(self, screen, last, data=None):
        """
        """
        if not self._pause:
            self.screen.force_update()        
            try:
                current = self.screen.get_active_window().get_application()

                for callback in self.callbacks:
                    callback(self._last.get_name(), 
                             self._last.get_icon())
                    self._last = current
            except AttributeError:
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

    
    def __init__(self, creeper, d=dict()):
        """Init
        
        Arguments:
        - `creeper`:
        """
        self._creeper = creeper
        self._creeper.addCallback(self.onUpdate)
        self.last = time.time()
        self._data = d
        


    def onUpdate(self, name, icon):
        """Called when active window changes
        
        Arguments:
        - `self`:
        - `name`:
        - `icon`:
        """
        now = time.time()
        spent = now - self.last

        print name, spent
        
        try:
            self._data[name]['time'] += spent
        except KeyError:
            self._data[name] = {}
            self._data[name]['time'] = spent
            self._data[name]['icon'] = icon
        except TypeError:
            print 'TypeError'
            print name
            print type(self._data)

        self.last = now



    def getData(self):
        """Return stats about active windows
        """
        return self._data

class Persistefier(object):
    """Persist using redis
    """
    
    def __init__(self, server='localhost'):
        """
        
        Arguments:
        - `server`:
        """
        self._server = redis.Redis(server)
        

    def persist(self, key, obj):
        self._server[key] = obj


    def load(self, key):
        """load object from db
        
        Arguments:
        - `self`:
        - `key`:
        """
        return self._server[key]



class MainWin(object):
    """Main window for Creeper
    """
    
    def __init__(self, ui):
        """Init MainWin
        
        Arguments:
        - `ui`:
        """

        self.p = Persistefier()

        self.load()

        self.c = Creeper()

        self.s = Statifier(self.c, self._tmp)
        del self._tmp
        
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
        self.BSave.connect('pressed', self.save)

        #Setting up pause
        self.pause = self.buildable.get_object('pause')
        self.pause.connect('pressed', self.c.toggle_pause)
        

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

        for k in d:
            self.app_store.append([d[k]['icon'],
                                   k,
                                   int(d[k]['time']/60),
                                   str((d[k]['time']
                                        / (self.c.uptime() + self._uptime))
                                       * 100) + "%"])

    def save(self, data=None):
        """Save application state
        
        Arguments:
        - `self`:
        """
        self.p.persist('time', self._uptime)
        self.p.persist('data', self.s.getData())

    def load(self):
        """Load application state
        
        Arguments:
        - `self`:
        """
        self._uptime = self.p.load('time') if self.p.load('time') != None else 0
        self._tmp = self.p.load('data') if self.p.load('data') != None else {}



    

if __name__ == '__main__':
    w = MainWin('ui.glade')

    gtk.main()


    
