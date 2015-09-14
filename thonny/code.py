# -*- coding: utf-8 -*-
import sys
import os.path
import tkinter as tk
from tkinter import ttk
import tkinter.messagebox as tkMessageBox
from tkinter.filedialog import asksaveasfilename
from tkinter.filedialog import askopenfilename

from thonny.misc_utils import eqfn, get_res_path
from thonny.codeview import CodeView
from thonny.globals import get_workbench
from thonny import misc_utils

_dialog_filetypes = [('all files', '.*'), ('Python files', '.py .pyw'), ('text files', '.txt')]


                
class Editor(ttk.Frame):
    def __init__(self, master, filename=None):
        
        ttk.Frame.__init__(self, master)
        assert isinstance(master, EditorNotebook)
        
        self._code_view = CodeView(self, propose_remove_line_numbers=True)
        self._code_view.grid(sticky=tk.NSEW)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        
        self._stepper = None
        
        self._filename = None
        self.file_encoding = None
        
        if filename is not None:
            self._load_file(filename)
            self._code_view.text.edit_modified(False)
        
        self._code_view.text.bind("<<Modified>>", lambda e: master.update_editor_title(self))


    def get_text_widget(self):
        return self._code_view.text
    
    def get_code_view(self):
        # TODO: try to get rid of this
        return self._code_view
    
    def get_filename(self, try_hard=False):
        if self._filename is None and try_hard:
            self.save_file()
            
        return self._filename
            
    def _load_file(self, filename):
        source, self.file_encoding = misc_utils.read_python_file(filename) # TODO: support also text files
        self._filename = filename
        get_workbench().event_generate("Open", editor=self, filename=filename)
        self._code_view.set_content(source)
        self._code_view.focus_set()
        
    def is_modified(self):
        return self._code_view.text.edit_modified()
    
    
    def save_file_enabled(self):
        return self.is_modified() or not self.get_filename()
    
    def save_file(self):
        if self._filename is not None:
            filename = self._filename
            get_workbench().event_generate("Save", editor=self)
        else:
            # http://tkinter.unpythonic.net/wiki/tkFileDialog
            filename = asksaveasfilename (
                filetypes = _dialog_filetypes, 
                defaultextension = ".py",
                initialdir = get_workbench().get_option("run.working_directory")
            )
            if filename == "":
                return None
            
            get_workbench().event_generate("SaveAs", editor=self, filename=filename)
                
        
        content = self._code_view.get_content()
        encoding = self.file_encoding or "UTF-8" 
        f = open(filename, mode="wb", )
        f.write(content.encode(encoding))
        f.close()

        self._filename = filename
        
        self._code_view.text.edit_modified(False)
        return self._filename
    
    def change_font_size(self, delta):
        self._code_view.change_font_size(delta)
    
    def show(self):
        self.master.select(self)
    
    def select_range(self, text_range):
        self._code_view.select_range(text_range)
    
    def enter_execution_mode(self):
        self._code_view.enter_execution_mode()
    
    
    def clear_debug_view(self):
        if self._stepper is not None:
            self._stepper.clear_debug_view()
    
    def focus_set(self):
        self._code_view.focus_set()
    
    def is_focused(self):
        return self.focus_displayof() == self._code_view.text
    
class EditorNotebook(ttk.Notebook):
    """
    Manages opened files / modules
    """
    def __init__(self, master):
        ttk.Notebook.__init__(self, master, padding=0)
        
        get_workbench().add_option("file.reopen_files", False)
        self._init_commands()
        self.enable_traversal()
        
        # open files from last session
        """ TODO: they should go only to recent files
        for filename in prefs["open_files"].split(";"):
            if os.path.exists(filename):
                self._open_file(filename)
        """
        self._load_startup_files()
    
    def _list_recent_files(self):
        get_workbench().add_option("file.recent_files", [])
         
        # TODO:
        
    
    def _init_commands(self):    
        # TODO: do these commands have to be in EditorNotebook ??
        # Create a module level function install_editor_notebook ??
        # Maybe add them separately, when notebook has been installed ??
        
        
        get_workbench().add_command("new_file", "file", "New", 
            self._cmd_new_file,
            default_sequence="<Control-n>",
            group=10,
            image_filename=get_res_path("file.new_file.gif"),
            include_in_toolbar=True)
        
        get_workbench().add_command("open_file", "file", "Open...", 
            self._cmd_open_file,
            default_sequence="<Control-o>",
            group=10,
            image_filename=get_res_path("file.open_file.gif"),
            include_in_toolbar=True)
        
        get_workbench().add_command("close_file", "file", "Close", 
            self._cmd_close_file,
            default_sequence="<Control-w>",
            tester=lambda: self.get_current_editor() is not None,
            group=10)
        
        get_workbench().add_command("save_file", "file", "Save", 
            self._cmd_save_file,
            default_sequence="<Control-s>",
            tester=self._cmd_save_file_enabled,
            group=10,
            image_filename=get_res_path("file.save_file.gif"),
            include_in_toolbar=True)
        
        get_workbench().add_command("save_file_as", "file", "Save as...",
            self._cmd_save_file_as,
            default_sequence=None,
            tester=lambda: self.get_current_editor() is not None,
            group=10)
        
        get_workbench().add_command("comment_in", "edit", "Comment in",
            self._cmd_comment_in,
            default_sequence="<Control-Key-3>",
            tester=None) # TODO:
        
        get_workbench().add_command("comment_out", "edit", "Comment out",
            self._cmd_comment_out,
            default_sequence="<Control-Key-4>",
            tester=None) # TODO:

        get_workbench()
    
    
    def _load_startup_files(self):
        
        filenames = sys.argv[1:]
        
        if get_workbench().get_option("file.reopen_files"):
            for filename in get_workbench().get_option("file.open_files"): 
                if filename not in filenames:
                    filenames.append(filename) 
            
        for filename in filenames:
            if os.path.exists(filename):
                self.show_file(filename)
        
        if len(filenames) == 0:
            self._cmd_new_file()
        
        self._remember_open_files()
    
    def save_all_named_editors(self):
        for editor in self.winfo_children():
            if editor.get_filename():
                editor.save_file()
    
    def _remember_open_files(self):
        open_files = [editor.get_filename() 
                      for editor in self.winfo_children() 
                      if editor.get_filename()]
        
        get_workbench().set_option("file.open_files", open_files)
    
    def _cmd_new_file(self):
        new_editor = Editor(self)
        get_workbench().event_generate("NewFile", editor=new_editor)
        self.add(new_editor, text=self._generate_editor_title(None))
        self.select(new_editor)
        new_editor.focus_set()
    
    def _cmd_open_file(self):
        filename = askopenfilename (
            filetypes = _dialog_filetypes, 
            initialdir = get_workbench().get_option("run.working_directory")
        )
        if filename != "":
            #self.close_single_untitled_unmodified_editor()
            self.show_file(filename)
            self._remember_open_files()
    
    def _cmd_close_file(self):
        # TODO: ask in case file is modified
        current_editor = self.get_current_editor()
        if current_editor: 
            self.forget(current_editor)
            current_editor.destroy()
            self._on_tab_changed(None)
            self._remember_open_files()
    
    def _cmd_save_file(self):
        if self.get_current_editor():
            self.get_current_editor().save_file()
        
        self._remember_open_files()
    
    def _cmd_save_file_enabled(self):
        return (self.get_current_editor() 
            and self.get_current_editor().save_file_enabled())
    
    def _cmd_save_file_as(self):
        if self.get_current_editor():
            self.get_current_editor().save_file()
            
        self._remember_open_files()
    
    def _cmd_save_file_as_enabled(self):
        return self.get_current_editor() is not None
    
    def _cmd_comment_in(self):
        if self.get_current_editor() is not None: 
            self.get_current_editor()._code_view._comment_in()
    
    def _cmd_comment_out(self):
        if self.get_current_editor() is not None: 
            self.get_current_editor()._code_view._comment_out()
    
    def close_single_untitled_unmodified_editor(self):
        editors = self.winfo_children()
        if (len(editors) == 1 
            and not editors[0].is_modified()
            and not editors[0].get_filename()):
            self._cmd_close_file()
        
    def get_current_editor(self):
        for child in self.winfo_children():
            if str(child) == str(self.select()):
                return child
            
        return None
    
    def show_file(self, filename, text_range=None):
        #self.close_single_untitled_unmodified_editor()
        editor = self.get_editor(filename, True)
        assert editor is not None
        
        self.select(editor)
        editor.focus_set()
        
        if text_range is not None:
            editor.select_range(text_range)
            
        return editor
    
    def change_font_size(self, delta):
        pass
    
    def update_editor_title(self, editor):
        self.tab(editor,
            text=self._generate_editor_title(editor.get_filename(), editor.is_modified()))
    
     
    def _generate_editor_title(self, filename, is_modified=False):
        if filename is None:
            result = "<untitled>"
        else:
            result = os.path.basename(filename)
        
        if is_modified:
            result += " *"
        
        return result
    
    def _open_file(self, filename):
        editor = Editor(self, filename)
        self.add(editor, text=self._generate_editor_title(filename))
              
        return editor
        
    def get_editor(self, filename, open_when_necessary=False):
        for child in self.winfo_children():
            child_filename = child.get_filename(False)
            if child_filename and eqfn(child.get_filename(), filename):
                return child
        
        if open_when_necessary:
            return self._open_file(filename)
        else:
            return None
    
    
    def focus_set(self):
        editor = self.get_current_editor()
        if editor: 
            editor.focus_set()
        else:
            super().focus_set()

    def current_editor_is_focused(self):
        editor = self.get_current_editor()
        return editor.is_focused()

    
    def check_allow_closing(self):
        modified_editors = [e for e in self.winfo_children() if e.is_modified()]
        
        if len(modified_editors) == 0:
            return True
        
        confirm = tkMessageBox.askyesnocancel(
                  title="Save On Close",
                  message="Do you want to save files before closing?",
                  default=tkMessageBox.YES,
                  master=self)
        
        if confirm:
            for editor in modified_editors:
                if editor.get_filename(True):
                    editor._cmd_save_file()
                else:
                    return False
            return True
        
        elif confirm is None:
            return False
        else:
            return True
    
