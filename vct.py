#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
#
# generated by wxGlade 0.8.2 on Mon Jun  4 11:10:11 2018
#

import wx
import wx.grid

# begin wxGlade: dependencies
# end wxGlade

# begin wxGlade: extracode
# end wxGlade

import os
import sys
import time
import threading as thr
from pydispatch import dispatcher
import types
import conv_to

#-------------------------------------------------------------------------------

BIN = 'bin'

VCT_DONE = 'VCT_SIGNAL_DONE'
VCT_PROG = 'VCT_SIGNAL_PROGRESS'
VCT_INIT = 'VCT_SIGNAL_START'

ST_QU = 'On Queue'
ST_CO = 'Converting...'
ST_DN = 'Done'
ST_DD = 'Done/Deleted'
ST_ER = 'Error'

#-------------------------------------------------------------------------------

def resource_path():
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return base_path

#-------------------------------------------------------------------------------

def get_total (txt):
    total = 0
    urls = txt.splitlines()
    if len(urls) != 0:
        for url in urls:
            if len(url)!=0 and url.find('DONE') < 0:
                total = total + 1
    return total

#-------------------------------------------------------------------------------

def convertFile (params, file):
    args = params
    args.files = [file]
    status, out_files = conv_to.run (args)
    #print (status, out_files)
    return status, out_files

#-------------------------------------------------------------------------------

def joinToFile (params, files):
    args = params
    args.files = files
    status, out_files = conv_to.run (args)
    #print (status, out_files)
    return status, out_files

#-------------------------------------------------------------------------------

def convertFiles (params, sender):
    conv_to.sep(">>> vct: JOB started!")
    conv_to.sep()

    if params.join_to == '':
        # File to file coversion
        for index, file in params.files:
            wx.CallAfter(dispatcher.send, signal=VCT_INIT, sender=sender, row=index)

            status, out_filenames = convertFile(params, file)

            if status == 0:
                filename = out_filenames[file]
            else:
                filename = ''

            wx.CallAfter(dispatcher.send, signal=VCT_PROG, sender=sender, increment=(index, filename, params.delete, status))
    else:
        # Join of different files
        files_join = []
        files_vct = []

        for index, file in params.files:
            files_join.append(file)
            files_vct.append((index, file))
            wx.CallAfter(dispatcher.send, signal=VCT_INIT, sender=sender, row=index)
       
        status, out_filenames = joinToFile (params, files_join)

        for index, file in files_vct:
            if status == 0:
                filename = out_filenames[file] 
            else:
                filename = ''   
            wx.CallAfter(dispatcher.send, signal=VCT_PROG, sender=sender, increment=(index, filename, params.delete, status))

    print(">>> vct: JOB Completed!\n")

#-------------------------------------------------------------------------------

def vct_run(params, sender):
    try:
        convertFiles(params, sender)
        exit_status = 0

    except SystemExit as exit:
        if exit.code != 0:
            print('!!! THR Run-Time Error: [{}]'.format(exit.code))
            exit_status = exit.code

    except Exception as exc:
        print('!!! THR Run-Time Exception: [{}]'.format(exc))
        exit_status = exc

    # Send exit status (wx Publish/Subscribe)
    wx.CallAfter (dispatcher.send, signal=VCT_DONE, sender=sender, status=exit_status)

#-------------------------------------------------------------------------------

def vct_run_thread (params, sender):
    try:
        thr_vct_script = thr.Thread(target=vct_run,args=(params, sender))
        thr_vct_script.start()
        return 0
    except Exception as exc:
        print('!!! Run-Time Exception: [{}]'.format(exc))
        return(exc)

#-------------------------------------------------------------------------------

def vct_play(file, base):
    try:
        cmd = '{}ffplay -hide_banner "{}"'.format(base, file)
        conv_to.exec_command(cmd, file_stdout=os.devnull, file_stderr=os.devnull)
        exit_status = 0

    except SystemExit as exit:
        if exit.code != 0:
            print('!!! THR Run-Time Error: [{}]'.format(exit.code))
            exit_status = exit.code

    except Exception as exc:
        print('!!! THR Run-Time Exception: [{}]'.format(exc))
        exit_status = exc

#-------------------------------------------------------------------------------

def vct_run_player (file, base):
    try:
        thr_vct_script = thr.Thread(target=vct_play,args=(file, base))
        thr_vct_script.start()
        return 0
    except Exception as exc:
        print('!!! Run-Time Exception: [{}]'.format(exc))
        return(exc)

#-------------------------------------------------------------------------------

def SignalStart (sender, row):
    sender.gc_files.SetCellValue(row, 2, ST_CO)
    sender.gc_files.SetCellTextColour(row, 2, wx.YELLOW)
    sender.gc_files.SetCellBackgroundColour(row, 2, wx.BLACK)

    sender.gc_files.AutoSizeColumn(2)
    sender.gc_files.AutoSizeColumn(3)
    sender.gc_files.AutoSizeColumn(4)

#-------------------------------------------------------------------------------

def SignalDone(sender, status):
    if status != 0:
        wx.MessageBox('VDG Operation could not be completed:\n{}'.format(status), 'Error', wx.OK | wx.ICON_ERROR)

    sender.CONVERTING=False
    sender.button_OK.Enable()
    sender.button_join_to.Enable()
    sender.button_3.Enable()
    sender.button_4.Enable()

#-------------------------------------------------------------------------------

def SignalProgress(sender, increment):
    sender.done = sender.done+1
    perc=(sender.done/sender.total)*100

    sender.label_progress.SetLabel('{:.0f}%'.format(perc))
    sender.gauge.SetValue(perc)

    index = increment[0]
    file = increment[1]
    delete = increment[2]
    status = increment[3]

    if status != 0:
        done = ST_ER
        sender.gc_files.SetCellTextColour(index, 2, wx.WHITE)
        sender.gc_files.SetCellBackgroundColour(index, 2, wx.RED)

    else:    
        if delete:
            done = ST_DD
            del_color = (0x6d, 0x6e, 0x61)
            sender.gc_files.SetCellTextColour(index, 0, del_color)
            sender.gc_files.SetCellTextColour(index, 2, wx.BLACK)
            sender.gc_files.SetCellBackgroundColour(index, 2, wx.GREEN)
    
        else:
            done = ST_DN
            sender.gc_files.SetCellTextColour(index, 0, wx.BLACK)
            sender.gc_files.SetCellTextColour(index, 2, wx.BLACK)
            sender.gc_files.SetCellBackgroundColour(index, 2, wx.GREEN)

    sender.gc_files.SetCellValue(index, 2, done)

    if status == 0:
        sender.gc_files.SetCellValue(index, 3, file)
        sender.gc_files.SetCellValue(index, 4, '{:.2f} MB'.format(conv_to.show_file_size(file, verbose=False)))
    else:
        sender.gc_files.SetCellValue(index, 3, '')
        sender.gc_files.SetCellValue(index, 4, '')        

    sender.gc_files.AutoSizeColumn(2)
    sender.gc_files.AutoSizeColumn(3)
    sender.gc_files.AutoSizeColumn(4)

#-------------------------------------------------------------------------------

def ShowFileInfo (file, cmd_bin):
    # Create argument object
    arguments = types.SimpleNamespace()
    arguments.verbose = False
    arguments.delete = False
    arguments.force = False
    arguments.info = True
    arguments.no_audio = False
    arguments.no_subs = False
    arguments.flip = False
    arguments.tag = False
    arguments.fps = 0.0
    arguments.join_to = ''
    arguments.container = 'mp4'
    arguments.resol = 'input'
    arguments.files = [file]
    arguments.bin = cmd_bin
    conv_to.run(arguments)

#-------------------------------------------------------------------------------          

def ToFloat(value):
    try:
        return (float(value))
    except:
        return (0.0)

#-------------------------------------------------------------------------------

class RedirectText(object):
    def __init__(self,aWxTextCtrl):
        self.out=aWxTextCtrl

    def write(self,string):
        wx.CallAfter(self.out.WriteText, string)

#-------------------------------------------------------------------------------

class MyVCT(wx.Frame):
    def __init__(self, *args, **kwds):
        # begin wxGlade: MyVCT.__init__
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.SetSize((800, 700))
        
        # Menu Bar
        self.VCT_menubar = wx.MenuBar()
        self.SetMenuBar(self.VCT_menubar)
        # Menu Bar end
        self.gc_files = wx.grid.Grid(self, wx.ID_ANY, size=(1, 1))
        self.button_3 = wx.Button(self, wx.ID_ANY, "Clean files")
        self.button_4 = wx.Button(self, wx.ID_ANY, "Select files")
        self.ch_delete = wx.CheckBox(self, wx.ID_ANY, "Delete originals", style=wx.CHK_2STATE)
        self.ch_tag = wx.CheckBox(self, wx.ID_ANY, "Tag video file", style=wx.CHK_2STATE)
        self.ch_ns = wx.CheckBox(self, wx.ID_ANY, "No subtitles", style=wx.CHK_2STATE)
        self.ch_na = wx.CheckBox(self, wx.ID_ANY, "No audio", style=wx.CHK_2STATE)
        self.ch_force = wx.CheckBox(self, wx.ID_ANY, "Force", style=wx.CHK_2STATE)
        self.ch_flip = wx.CheckBox(self, wx.ID_ANY, u"Flip 180\u00ba", style=wx.CHK_2STATE)
        self.cb_container = wx.ComboBox(self, wx.ID_ANY, choices=["mp3", "m4a", "ogg", "avi", "mp4", "mkv"], style=wx.CB_DROPDOWN)
        self.cb_fps = wx.ComboBox(self, wx.ID_ANY, choices=["input", "24", "23.98", "25", "29.97", "30", "50", "59.94", "60"], style=wx.CB_DROPDOWN)
        self.cb_resolution = wx.ComboBox(self, wx.ID_ANY, choices=["input", "std", "VCD", "DVD", "HD", "FHD", "UHD", "DCI"], style=wx.CB_DROPDOWN)
        self.button_join_to = wx.Button(self, wx.ID_ANY, "Join to file")
        self.join_to = wx.TextCtrl(self, wx.ID_ANY, "", style=wx.TE_READONLY)
        self.label_progress = wx.StaticText(self, wx.ID_ANY, "", style=wx.ALIGN_RIGHT)
        self.gauge = wx.Gauge(self, wx.ID_ANY, 100)
        self.button_OK = wx.Button(self, wx.ID_ANY, "Convert")
        self.text_ctrl_log = wx.TextCtrl(self, wx.ID_ANY, "", style=wx.HSCROLL | wx.TE_MULTILINE | wx.TE_READONLY)

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.grid.EVT_GRID_CMD_CELL_LEFT_CLICK, self.cellSelected, self.gc_files)
        self.Bind(wx.grid.EVT_GRID_CMD_CELL_LEFT_DCLICK, self.cellActivated, self.gc_files)
        self.Bind(wx.EVT_BUTTON, self.cleanFiles, self.button_3)
        self.Bind(wx.EVT_BUTTON, self.selectFiles, self.button_4)
        self.Bind(wx.EVT_COMBOBOX, self.containerSelected, self.cb_container)
        self.Bind(wx.EVT_BUTTON, self.outputFolder, self.button_join_to)
        self.Bind(wx.EVT_BUTTON, self.convertFiles, self.button_OK)
        # end wxGlade

        self.done =  0
        self.total = 0
        self.label_progress.SetLabel('')
        self.gauge.SetValue(0)
        self.CONVERTING = False

        # Better for log reading ...
        self.text_ctrl_log.SetFont(wx.Font(11, wx.MODERN, wx.NORMAL, wx.NORMAL, 0, "Courier"))

        # Redirect STDOUT/STDERR
        redir=RedirectText(self.text_ctrl_log)
        sys.stdout=redir
        sys.stderr=redir

        self.CMDROOT = os.path.join(resource_path(), BIN, '')

        # create pubsub receivers
        dispatcher.connect(SignalDone, signal=VCT_DONE, sender=self)
        dispatcher.connect(SignalProgress, signal=VCT_PROG, sender=self)
        dispatcher.connect(SignalStart, signal=VCT_INIT, sender=self)

    def __set_properties(self):
        # begin wxGlade: MyVCT.__set_properties
        self.SetTitle("VCT")
        self.gc_files.CreateGrid(0, 5)
        self.gc_files.SetRowLabelSize(30)
        self.gc_files.SetColLabelSize(20)
        self.gc_files.EnableEditing(0)
        self.gc_files.EnableDragRowSize(0)
        self.gc_files.SetColLabelValue(0, "File")
        self.gc_files.SetColSize(0, 262)
        self.gc_files.SetColLabelValue(1, "Size")
        self.gc_files.SetColSize(1, 75)
        self.gc_files.SetColLabelValue(2, "Status")
        self.gc_files.SetColSize(2, 78)
        self.gc_files.SetColLabelValue(3, "Output File")
        self.gc_files.SetColSize(3, 262)
        self.gc_files.SetColLabelValue(4, "Output Size")
        self.gc_files.SetColSize(4, 75)
        self.ch_delete.SetToolTip("Delete original input files once the conversion has finished successfully.")
        self.ch_tag.SetToolTip(u"Set a tag on the output video file name on the form of \u201c[9999x999-<video_codec>]\u201d.")
        self.ch_ns.SetToolTip("Do not process subtitles. Output files will not have subtitles streams.")
        self.ch_na.SetToolTip("Do not process audio. Output files will not have audio streams.")
        self.ch_force.SetToolTip("Force re-encoding of files. Do not optimize conversion process.")
        self.ch_flip.SetToolTip(u"Rotate video 180\u00ba (upside down).")
        self.cb_container.SetToolTip("Set the container format value for the converted files")
        self.cb_container.SetSelection(4)
        self.cb_fps.SetToolTip("Set the FPS value for the converted files")
        self.cb_fps.SetSelection(0)
        self.cb_resolution.SetToolTip("Set the resolution value for the converted files")
        self.cb_resolution.SetSelection(0)
        self.join_to.SetToolTip("Set the output folder for the output file containing the joining of the selected input files.")
        self.label_progress.SetMinSize((40, 15))
        self.text_ctrl_log.SetBackgroundColour(wx.Colour(222, 222, 222))
        self.text_ctrl_log.SetFont(wx.Font(10, wx.MODERN, wx.NORMAL, wx.NORMAL, 0, "Courier"))
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: MyVCT.__do_layout
        self.sizer_app = wx.BoxSizer(wx.VERTICAL)
        self.sizer_1 = wx.StaticBoxSizer(wx.StaticBox(self, wx.ID_ANY, "Details/Log"), wx.HORIZONTAL)
        self.sizer_buttons = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_join = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_options_cb = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_options_ck = wx.BoxSizer(wx.HORIZONTAL)
        sizer_files = wx.BoxSizer(wx.VERTICAL)
        grid_sizer_2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_files.Add(self.gc_files, 1, wx.ALL | wx.EXPAND, 5)
        grid_sizer_2.Add(self.button_3, 0, wx.ALL, 5)
        grid_sizer_2.Add((20, 20), 9, wx.EXPAND, 0)
        grid_sizer_2.Add(self.button_4, 0, wx.ALIGN_RIGHT | wx.ALL, 5)
        sizer_files.Add(grid_sizer_2, 0, wx.EXPAND, 0)
        self.sizer_app.Add(sizer_files, 4, wx.ALL | wx.EXPAND, 4)
        self.sizer_options_ck.Add(self.ch_delete, 0, wx.ALL, 5)
        self.sizer_options_ck.Add(self.ch_tag, 0, wx.ALL, 5)
        self.sizer_options_ck.Add(self.ch_ns, 0, wx.ALL, 5)
        self.sizer_options_ck.Add(self.ch_na, 0, wx.ALL, 5)
        self.sizer_options_ck.Add(self.ch_force, 0, wx.ALL, 5)
        self.sizer_options_ck.Add(self.ch_flip, 0, wx.ALL, 5)
        self.sizer_app.Add(self.sizer_options_ck, 0, wx.ALL | wx.EXPAND, 4)
        label_1 = wx.StaticText(self, wx.ID_ANY, "Container:")
        self.sizer_options_cb.Add(label_1, 0, wx.ALIGN_RIGHT | wx.ALL, 10)
        self.sizer_options_cb.Add(self.cb_container, 0, wx.ALL, 5)
        FPS = wx.StaticText(self, wx.ID_ANY, "FPS:")
        self.sizer_options_cb.Add(FPS, 0, wx.ALIGN_RIGHT | wx.ALL, 10)
        self.sizer_options_cb.Add(self.cb_fps, 0, wx.ALL, 5)
        label_2 = wx.StaticText(self, wx.ID_ANY, "Resolution:")
        self.sizer_options_cb.Add(label_2, 0, wx.ALIGN_RIGHT | wx.ALL, 10)
        self.sizer_options_cb.Add(self.cb_resolution, 0, wx.ALL, 5)
        self.sizer_app.Add(self.sizer_options_cb, 0, wx.ALL | wx.EXPAND, 4)
        self.sizer_join.Add(self.button_join_to, 0, wx.ALL, 5)
        self.sizer_join.Add(self.join_to, 5, wx.ALL, 5)
        self.sizer_app.Add(self.sizer_join, 0, wx.ALL | wx.EXPAND, 4)
        self.sizer_buttons.Add(self.label_progress, 0, wx.ALL, 5)
        self.sizer_buttons.Add(self.gauge, 9, wx.ALL | wx.EXPAND, 5)
        self.sizer_buttons.Add(self.button_OK, 0, wx.ALIGN_RIGHT | wx.ALL | wx.EXPAND, 5)
        self.sizer_app.Add(self.sizer_buttons, 0, wx.ALL | wx.EXPAND, 4)
        self.sizer_1.Add(self.text_ctrl_log, 10, wx.ALL | wx.EXPAND, 0)
        self.sizer_app.Add(self.sizer_1, 3, wx.EXPAND, 0)
        self.SetSizer(self.sizer_app)
        self.Layout()
        # end wxGlade

    def ExitApp(self, event):  # wxGlade: MyVCT.<event_handler>
        self.Close()
        event.Skip()

    def cleanFiles(self, event):  # wxGlade: MyVCT.<event_handler>
        self.text_ctrl_log.SetValue('')
        self.gauge.SetValue(0)
        self.label_progress.SetLabel('')

        rows = self.gc_files.GetNumberRows()
        if rows > 0:
            self.gc_files.DeleteRows(0,rows)

        event.Skip()

    def selectFiles(self, event):  # wxGlade: MyVCT.<event_handler>
        self.text_ctrl_log.SetValue('')
        self.gauge.SetValue(0)
        self.label_progress.SetLabel('')

        dialog = wx.FileDialog(None, "Choose audio/video file/s:", style=wx.FD_OPEN|wx.FD_MULTIPLE|wx.FD_FILE_MUST_EXIST)
        if dialog.ShowModal() == wx.ID_OK:
            selecteds = dialog.GetPaths()
            for f in selecteds:
                row = self.gc_files.GetNumberRows()
                self.gc_files.AppendRows(1)
                self.gc_files.SetCellValue(row, 0, f)
                self.gc_files.SetCellValue(row, 1, '{:.2f} MB'.format(conv_to.show_file_size(f, verbose=False)))
                sz_color = (0x6d, 0x6e, 0x61)
                self.gc_files.SetCellTextColour(row, 1, sz_color)
                self.gc_files.SetCellValue(row, 2, ST_QU)
                #bg_color = wx.SystemSettings.GetColour(wx.SYS_COLOUR_BACKGROUND)
                self.gc_files.SetCellBackgroundColour(row, 2, wx.BLUE)
                self.gc_files.SetCellTextColour(row, 2, wx.WHITE)
                self.gc_files.SetCellValue(row, 3, '')
                self.gc_files.SetCellValue(row, 4, '')
                self.gc_files.SetCellTextColour(row, 4, sz_color)
        dialog.Destroy()
        self.gc_files.AutoSizeColumn(0)
        self.gc_files.AutoSizeColumn(1)
        self.gc_files.AutoSizeColumn(2)
        self.gc_files.AutoSizeColumn(3)
        self.gc_files.AutoSizeColumn(4)
        event.Skip()

    def outputFolder(self, event):  # wxGlade: MyVCT.<event_handler>
        self.text_ctrl_log.SetValue('')
        self.gauge.SetValue(0)
        self.label_progress.SetLabel('')

        dialog = wx.FileDialog(None, "Choose join file:", style=wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)
        if dialog.ShowModal() == wx.ID_OK:
            self.join_to.SetValue(dialog.GetPath())
            self.cb_container.Disable()
            #self.ch_delete.Disable()
            self.cb_resolution.Disable()
            self.cb_fps.Disable()
            self.ch_tag.Disable()
            self.ch_ns.Disable()
            self.ch_na.Disable()
            self.ch_force.Disable()
            self.ch_flip.Disable()
        else:
            self.join_to.SetValue('')
            self.cb_container.Enable()
            self.ch_delete.Enable()
            if conv_to.IsVideo(self.cb_container.GetValue()):
                self.cb_resolution.Enable()
                self.cb_fps.Enable()
                self.ch_tag.Enable()
                self.ch_ns.Enable()
                self.ch_na.Enable()
                self.ch_force.Enable()
                self.ch_flip.Enable()
            else:
                self.cb_resolution.Disable()
                self.cb_fps.Disable()
                self.ch_tag.Disable()
                self.ch_ns.Disable()
                self.ch_na.Disable()
                self.ch_force.Disable()
                self.ch_flip.Disable()
        dialog.Destroy()
        event.Skip()

    def convertFiles(self, event):  # wxGlade: MyVCT.<event_handler>
        files_list = []
        files_on_queue = 0
        for ind in range(0,self.gc_files.GetNumberRows()):
            status = self.gc_files.GetCellValue(ind, 2)
            if status == ST_QU:
                file = self.gc_files.GetCellValue(ind, 0)
                item = (ind, file)
                files_list.append(item)
                files_on_queue = files_on_queue + 1

        self.total = files_on_queue
        self.done = 0

        # Create argument object
        arguments = types.SimpleNamespace()
        arguments.verbose = False
        arguments.delete = self.ch_delete.GetValue()
        arguments.force = self.ch_force.GetValue()
        arguments.info = False
        arguments.no_audio = self.ch_na.GetValue()
        arguments.no_subs = self.ch_ns.GetValue()
        arguments.flip = self.ch_flip.GetValue()
        arguments.tag = self.ch_tag.GetValue()
        arguments.fps = ToFloat(self.cb_fps.GetValue())
        arguments.join_to = self.join_to.GetValue()
        arguments.container = self.cb_container.GetValue()
        arguments.resol = self.cb_resolution.GetValue()
        arguments.files = files_list
        arguments.bin = self.CMDROOT

        if self.total != 0:
            status = vct_run_thread(params=arguments, sender=self)
            if status != 0:
                self.text_ctrl_log.SetValue('')
                self.gauge.SetValue(0)
                self.label_progress.SetLabel('')
                wx.MessageBox('Error launching operation:\n{}'.format(status), 'Error', wx.OK|wx.ICON_ERROR)
            else:
                self.CONVERTING=True
                self.text_ctrl_log.SetValue('')
                self.gauge.SetValue(0)
                self.label_progress.SetLabel('0%')
                self.button_OK.Disable()
                self.button_join_to.Disable()
                self.button_3.Disable()
                self.button_4.Disable()
        else:
            self.text_ctrl_log.SetValue('')
            self.gauge.SetValue(0)
            self.label_progress.SetLabel('')
            wx.MessageBox('Conversion queue is empty', 'Warning', wx.OK|wx.ICON_WARNING)

        event.Skip()

    def containerSelected(self, event):  # wxGlade: MyVCT.<event_handler>
        if not self.CONVERTING:
            self.text_ctrl_log.SetValue('')
            self.gauge.SetValue(0)
            self.label_progress.SetLabel('')

        if conv_to.IsVideo(self.cb_container.GetValue()):
            self.cb_resolution.Enable()
            self.cb_fps.Enable()
            self.ch_tag.Enable()
            self.ch_ns.Enable()
            self.ch_na.Enable()
            self.ch_force.Enable()
            self.ch_flip.Enable()
        else:
            self.cb_resolution.Disable()
            self.cb_fps.Disable()
            self.ch_tag.Disable()
            self.ch_ns.Disable()
            self.ch_na.Disable()
            self.ch_force.Disable()
            self.ch_flip.Disable()
        event.Skip()

    def cellSelected(self, event):  # wxGlade: MyVCT.<event_handler>
        if not self.CONVERTING:
            self.text_ctrl_log.SetValue('')
            self.gauge.SetValue(0)
            self.label_progress.SetLabel('')

            col = event.GetCol()
            if col == 0 or col == 3:
                file = self.gc_files.GetCellValue(event.GetRow(), col)
                st = self.gc_files.GetCellValue(event.GetRow(), 2)
                if len(file)!=0:
                    if col != 0 or st != ST_DD:
                        ShowFileInfo(file, self.CMDROOT)

        event.Skip()

    def cellActivated(self, event):  # wxGlade: MyVCT.<event_handler>
        if not self.CONVERTING:
            self.text_ctrl_log.SetValue('')
            self.gauge.SetValue(0)
            self.label_progress.SetLabel('')

        col = event.GetCol()
        if col == 0 or col == 3:
            file = self.gc_files.GetCellValue(event.GetRow(), col)
            st = self.gc_files.GetCellValue(event.GetRow(), 2)
            if len(file)!=0:
                if col!=0 or st != ST_DD:
                    dlg = wx.MessageDialog(None, 'Do you want to play file:\n"{}"?'.format(file),'VCT Player',wx.YES_NO | wx.ICON_QUESTION)
                    result = dlg.ShowModal()       
                    if result == wx.ID_YES:
                        status = vct_run_player(file=file, base=self.CMDROOT)
                        if status != 0:
                            wx.MessageBox('Error launching VCT Player', 'Error', wx.OK|wx.ICON_ERROR)
        event.Skip()

# end of class MyVCT

class vct(wx.App):
    def OnInit(self):
        self.VCT = MyVCT(None, wx.ID_ANY, "")
        self.SetTopWindow(self.VCT)
        self.VCT.Show()
        return True

# end of class vct

if __name__ == "__main__":
    vct = vct(0)
    vct.MainLoop()
