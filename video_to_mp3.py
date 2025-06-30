import os
import subprocess
import wx
import threading
import pathlib


class FileDropTarget(wx.FileDropTarget):
    def __init__(self, listbox):
        super().__init__()
        self.listbox = listbox

    def OnDropFiles(self, x, y, filenames):
        for file in filenames:
            if os.path.isdir(file):
                self.add_folder_recursive(file)
            elif file.lower().endswith(('.mp4', '.mkv', '.avi', '.mov', '.flv', '.wmv', '.ts', '.aac')):
                self.listbox.Append(file)
        return True

    def add_folder_recursive(self, folder):
        for root, _, files in os.walk(folder):
            for file in files:
                if file.lower().endswith(('.mp4', '.mkv', '.avi', '.mov', '.flv', '.wmv', '.ts', '.aac')):
                    self.listbox.Append(os.path.join(root, file))


class VideoToMP3Converter(wx.Frame):
    def __init__(self):
        super().__init__(None, title='Video to MP3 Converter', size=(500, 550))
        panel = wx.Panel(self)

        vbox = wx.BoxSizer(wx.VERTICAL)

        # Menu bar
        menu_bar = wx.MenuBar()

        file_menu = wx.Menu()
        menu_add_video = file_menu.Append(wx.ID_ANY, "Add Video\tCtrl+A")
        menu_remove_video = file_menu.Append(wx.ID_ANY, "Remove Video\tCtrl+R")
        menu_add_folder = file_menu.Append(wx.ID_ANY, "Add Video from Folder\tCtrl+F")
        file_menu.AppendSeparator()
        menu_quit = file_menu.Append(wx.ID_EXIT, "Quit")

        self.Bind(wx.EVT_MENU, self.add_file_dialog, menu_add_video)
        self.Bind(wx.EVT_MENU, self.remove_file, menu_remove_video)
        self.Bind(wx.EVT_MENU, self.add_folder, menu_add_folder)
        self.Bind(wx.EVT_MENU, self.on_quit, menu_quit)

        menu_bar.Append(file_menu, "File")

        help_menu = wx.Menu()
        menu_help = help_menu.Append(wx.ID_ANY, "How to Use")
        menu_about = help_menu.Append(wx.ID_ANY, "About")

        self.Bind(wx.EVT_MENU, self.on_help, menu_help)
        self.Bind(wx.EVT_MENU, self.on_about, menu_about)

        menu_bar.Append(help_menu, "Help")
        self.SetMenuBar(menu_bar)

        # Status Bar
        self.status_bar = self.CreateStatusBar()

        # File list display with drag and drop
        self.file_list = wx.ListBox(panel, style=wx.LB_EXTENDED | wx.LB_HSCROLL)
        drop_target = FileDropTarget(self.file_list)
        self.file_list.SetDropTarget(drop_target)

        # Buttons to manage file list
        btn_add = wx.Button(panel, label=' Add File')
        btn_add.SetBitmap(wx.ArtProvider.GetBitmap(wx.ART_FILE_OPEN, wx.ART_BUTTON))
        btn_add.Bind(wx.EVT_BUTTON, self.add_file_dialog)

        btn_remove = wx.Button(panel, label=' Remove')
        btn_remove.SetBitmap(wx.ArtProvider.GetBitmap(wx.ART_DELETE, wx.ART_BUTTON))
        btn_remove.Bind(wx.EVT_BUTTON, self.remove_file)

        btn_add_folder = wx.Button(panel, label=' Add Folder')
        btn_add_folder.SetBitmap(wx.ArtProvider.GetBitmap(wx.ART_FOLDER_OPEN, wx.ART_BUTTON))
        btn_add_folder.Bind(wx.EVT_BUTTON, self.add_folder)

        self.keep_subfolder_chk = wx.CheckBox(panel, label="Keep Subfolder Structure")

        # Output folder selection
        default_music_path = str(pathlib.Path.home() / "Music")
        self.output_dir = wx.TextCtrl(panel, value=default_music_path, style=wx.TE_READONLY)
        btn_output = wx.Button(panel, label=' Select Output Folder', size=(180, 30))
        btn_output.SetBitmap(wx.ArtProvider.GetBitmap(wx.ART_FOLDER, wx.ART_BUTTON))
        btn_output.Bind(wx.EVT_BUTTON, self.select_output_folder)

        # Bitrate selection
        self.bitrate_choices = ['128k', '192k', '256k', '320k']
        self.bitrate_choice = wx.Choice(panel, choices=self.bitrate_choices)
        self.bitrate_choice.SetSelection(0)  # Default to 192k

        # Convert button (always enabled)
        self.btn_convert = wx.Button(panel, label='Convert Videos to MP3', size=(180, 30))
        self.btn_convert.Bind(wx.EVT_BUTTON, self.start_conversion)

        # Progress bar
        self.progress_bar = wx.Gauge(panel, range=100, size=(-1, 20))

        # Layout
        vbox.Add(wx.StaticText(panel, label='Video Files:'), flag=wx.ALL, border=5)
        vbox.Add(self.file_list, proportion=1, flag=wx.EXPAND | wx.ALL, border=5)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(btn_add, proportion=1, flag=wx.ALL, border=5)
        hbox.Add(btn_remove, proportion=1, flag=wx.ALL, border=5)
        hbox.Add(btn_add_folder, proportion=1, flag=wx.ALL, border=5)
        vbox.Add(hbox, flag=wx.EXPAND)

        vbox.Add(self.keep_subfolder_chk, flag=wx.ALL, border=5)
        vbox.Add(wx.StaticText(panel, label='Output Folder:'), flag=wx.ALL, border=5)
        vbox.Add(self.output_dir, flag=wx.EXPAND | wx.ALL, border=5)
        vbox.Add(btn_output, flag=wx.ALIGN_CENTER | wx.BOTTOM, border=5)

        vbox.Add(wx.StaticText(panel, label='Select Bitrate:'), flag=wx.ALL, border=5)
        vbox.Add(self.bitrate_choice, flag=wx.EXPAND | wx.ALL, border=5)

        vbox.Add(self.btn_convert, flag=wx.ALIGN_CENTER | wx.BOTTOM, border=25)
        vbox.Add(self.progress_bar, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=10)

        panel.SetSizer(vbox)
        panel.Layout()
        self.Centre()

    def start_conversion(self, event):
        thread = threading.Thread(target=self.convert_videos, daemon=True)
        thread.start()

    def add_folder(self, event):
        with wx.DirDialog(self, 'Select Folder', style=wx.DD_DEFAULT_STYLE) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                folder = dlg.GetPath()
                for file in os.listdir(folder):
                    if file.lower().endswith(('.mp4', '.mkv', '.avi', '.mov', '.flv', '.wmv', '.ts', '.aac')):
                        self.file_list.Append(os.path.join(folder, file))
        self.btn_convert.Enable(bool(self.file_list.GetCount()))

    def add_file_dialog(self, event):
        with wx.FileDialog(self, "Choose video files", wildcard="Video files (*.mp4;*.mkv;*.avi;*.mov;*.flv;*.wmv;*.ts;*.aac)|*.mp4;*.mkv;*.avi;*.mov;*.flv;*.wmv;*.ts;*.aac", style=wx.FD_OPEN | wx.FD_MULTIPLE) as file_dialog:
            if file_dialog.ShowModal() == wx.ID_OK:
                for file in file_dialog.GetPaths():
                    self.file_list.Append(file)

    def remove_file(self, event):
        selections = self.file_list.GetSelections()
        for index in reversed(selections):
            self.file_list.Delete(index)

    def on_quit(self, event):
        self.Close()

    def on_help(self, event):
        print("Help")

    def on_about(self, event):
        print("About")

    def select_output_folder(self, event):
        with wx.DirDialog(self, 'Select Output Folder', style=wx.DD_DEFAULT_STYLE) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                self.output_dir.SetValue(dlg.GetPath())

    def convert_videos(self):
        output_folder = self.output_dir.GetValue()
        video_files = self.file_list.GetItems()
        selected_bitrate = self.bitrate_choice.GetStringSelection()

        if not video_files or not output_folder:
            wx.CallAfter(wx.MessageBox, 'Please select files and output folder.', 'Error', wx.OK | wx.ICON_ERROR)
            return

        self.progress_bar.SetValue(0)
        self.status_bar.SetStatusText("Start conversion ...")

        total_files = len(video_files)
        for index, file in enumerate(video_files):
            output_path = os.path.join(output_folder, os.path.splitext(os.path.basename(file))[0] + '.mp3')

            # Correction : PAS DE guillemets autour des chemins si on utilise une liste
            command = [
                'ffmpeg',
                '-i', file,
                '-vn',
                '-ar', '44100',
                '-ac', '2',
                '-ab', selected_bitrate,
                '-f', 'mp3',
                output_path
            ]
            try:
                process = subprocess.Popen(
                    command,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                process.wait()
            except FileNotFoundError:
                wx.CallAfter(wx.MessageBox, 'FFmpeg not found. Make sure it is installed and added to PATH.', 'Error', wx.OK | wx.ICON_ERROR)
                return

            progress = int(((index + 1) / total_files) * 100)
            wx.CallAfter(self.progress_bar.SetValue, progress)
            wx.CallAfter(self.status_bar.SetStatusText, f'Progress: {progress}%')

        wx.CallAfter(self.progress_bar.SetValue, 100)
        wx.CallAfter(self.status_bar.SetStatusText, 'Conversion completed!')
        wx.CallAfter(wx.MessageBox, 'Conversion completed!', 'Success', wx.OK | wx.ICON_INFORMATION)


if __name__ == '__main__':
    app = wx.App(False)
    frame = VideoToMP3Converter()
    frame.Show()
    app.MainLoop()