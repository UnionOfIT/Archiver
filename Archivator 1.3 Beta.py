import wx
import os
from datetime import datetime
import zipfile
import tarfile
import json
import sys

class Archiver(wx.Frame):
    def __init__(self, parent, title):
        self.config_dir = os.path.join(os.getenv('LOCALAPPDATA'), 'Archiver')
        self.config_path = os.path.join(self.config_dir, 'config.json')
        self.load_config()
        super(Archiver, self).__init__(parent, title=self.get_translation(title), size=(800, 600))
        self.current_directory = os.path.dirname(os.path.abspath(__file__))
        self.SetIcon(self.load_icon('archive.png', wx.ART_FILE_OPEN))
        self.panel = wx.Panel(self)
        self.panel.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.archive_name = ""
        self.current_folder = ""
        self.create_menu()
        self.create_toolbar()
        self.create_main_area()
        self.create_status_bar()
        self.Show()

    def load_config(self):
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.language = config.get('language', 'ru')
            except:
                self.language = 'ru'
        else:
            self.language = 'ru'
            self.save_config()

    def save_config(self):
        config = {'language': self.language}
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
        except Exception as e:
            self.show_error_dialog(f"{self.get_translation('Ошибка сохранения конфига: ')}{str(e)}")

    def restart_application(self):
        python = sys.executable
        os.execl(python, python, *sys.argv)

    def load_icon(self, filename, fallback_art):
        icon_path = os.path.join(self.current_directory, filename)
        if os.path.exists(icon_path):
            return wx.Icon(icon_path, wx.BITMAP_TYPE_PNG)
        else:
            return wx.ArtProvider.GetIcon(fallback_art, wx.ART_OTHER)

    def create_menu(self):
        self.menubar = wx.MenuBar()
        self.update_file_menu()
        self.update_tools_menu()
        self.SetMenuBar(self.menubar)

    def update_file_menu(self):
        self.fileMenu = wx.Menu()
        self.fileMenu.Append(wx.ID_NEW, self.get_translation("Новый архив\tCtrl+N"), self.get_translation("Создать новый архив"))
        self.fileMenu.Append(wx.ID_OPEN, self.get_translation("Открыть архив\tCtrl+O"), self.get_translation("Открыть существующий архив"))
        self.fileMenu.Append(wx.ID_EXIT, self.get_translation("Выход\tCtrl+Q"), self.get_translation("Выход из приложения"))
        self.Bind(wx.EVT_MENU, self.on_create_archive, id=wx.ID_NEW)
        self.Bind(wx.EVT_MENU, self.on_select_archive, id=wx.ID_OPEN)
        self.Bind(wx.EVT_MENU, self.on_exit, id=wx.ID_EXIT)
        self.menubar.Append(self.fileMenu, self.get_translation("Файл"))

    def update_tools_menu(self):
        self.toolsMenu = wx.Menu()
        add_item = self.toolsMenu.Append(wx.ID_ADD, self.get_translation("Добавить файл или папку\tCtrl+A"), self.get_translation("Добавить файл или папку в архив"))
        extract_item = self.toolsMenu.Append(wx.ID_EXECUTE, self.get_translation("Извлечь всё\tCtrl+E"), self.get_translation("Извлечь все файлы из архива"))
        extract_selected_item = self.toolsMenu.Append(wx.ID_ANY, self.get_translation("Извлечь выбранное\tCtrl+Shift+E"), self.get_translation("Извлечь выбранный файл"))
        create_folder_item = self.toolsMenu.Append(wx.ID_ANY, self.get_translation("Создать папку"), self.get_translation("Создать папку в архиве"))
        feedback_item = self.toolsMenu.Append(wx.ID_ANY, self.get_translation("Обратная связь"), self.get_translation("Связь с разработчиком"))
        settings_item = self.toolsMenu.Append(wx.ID_ANY, self.get_translation("Настройки"), self.get_translation("Настройки приложения"))
        self.Bind(wx.EVT_MENU, self.on_open_settings, id=settings_item.GetId())
        self.Bind(wx.EVT_MENU, self.on_add_file_or_folder, id=add_item.GetId())
        self.Bind(wx.EVT_MENU, self.on_extract_all, id=extract_item.GetId())
        self.Bind(wx.EVT_MENU, self.on_extract_selected, id=extract_selected_item.GetId())
        self.Bind(wx.EVT_MENU, self.on_create_folder, id=create_folder_item.GetId())
        self.Bind(wx.EVT_MENU, self.on_feedback, id=feedback_item.GetId())
        self.menubar.Append(self.toolsMenu, self.get_translation("Инструменты"))

    def create_toolbar(self):
        toolbar = self.CreateToolBar()
        toolbar.SetBackgroundColour(wx.Colour(240, 240, 240))
        toolbar.AddTool(wx.ID_NEW, self.get_translation("Новый"), wx.ArtProvider.GetBitmap(wx.ART_NEW, wx.ART_TOOLBAR))
        toolbar.AddTool(wx.ID_OPEN, self.get_translation("Открыть"), wx.ArtProvider.GetBitmap(wx.ART_FILE_OPEN, wx.ART_TOOLBAR))
        toolbar.AddTool(wx.ID_ADD, self.get_translation("Добавить"), wx.ArtProvider.GetBitmap(wx.ART_PLUS, wx.ART_TOOLBAR))
        toolbar.AddTool(wx.ID_EXECUTE, self.get_translation("Извлечь"), wx.ArtProvider.GetBitmap(wx.ART_EXECUTABLE_FILE, wx.ART_TOOLBAR))
        search_tool_icon = wx.ArtProvider.GetBitmap(wx.ART_FIND, wx.ART_TOOLBAR)
        search_tool = toolbar.AddTool(wx.ID_ANY, self.get_translation("Поиск"), search_tool_icon, shortHelp=self.get_translation("Поиск файла в архиве"))
        delete_tool_icon = self.load_icon('delete.png', wx.ART_DELETE)
        delete_tool = toolbar.AddTool(wx.ID_ANY, self.get_translation("Удалить"), delete_tool_icon, shortHelp=self.get_translation("Удалить выбранный файл"))
        toolbar.Realize()
        self.Bind(wx.EVT_TOOL, self.on_create_archive, id=wx.ID_NEW)
        self.Bind(wx.EVT_TOOL, self.on_select_archive, id=wx.ID_OPEN)
        self.Bind(wx.EVT_TOOL, self.on_add_file_or_folder, id=wx.ID_ADD)
        self.Bind(wx.EVT_TOOL, self.on_extract_all, id=wx.ID_EXECUTE)
        self.Bind(wx.EVT_TOOL, self.on_search_file, id=search_tool.GetId())
        self.Bind(wx.EVT_TOOL, self.delete_selected_file, id=delete_tool.GetId())

    def create_main_area(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.list_ctrl = wx.ListCtrl(self.panel, style=wx.LC_REPORT | wx.BORDER_SUNKEN)
        self.list_ctrl.InsertColumn(0, self.get_translation("Имя файла/папки"), width=400)
        self.list_ctrl.InsertColumn(1, self.get_translation("Размер"), width=90)
        self.list_ctrl.InsertColumn(2, self.get_translation("Дата изменения"), width=120)
        sizer.Add(self.list_ctrl, 1, wx.EXPAND | wx.ALL, 10)
        self.panel.SetSizer(sizer)
        self.list_ctrl.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.on_item_double_click)

    def create_status_bar(self):
        self.status_bar = self.CreateStatusBar()
        self.status_bar.SetBackgroundColour(wx.Colour(220, 220, 220))
        self.status_bar.SetStatusText(self.get_translation("Готово"))

    def get_translation(self, text):
        translations = {
            'ru': {
                "Имя файла/папки": "Имя файла/папки",
                "Размер": "Размер",
                "Дата изменения": "Дата изменения",
                "Готово": "Готово",
                "Обратная связь": "Обратная связь",
                "Выбор": "Выбор",
                "Поиск файла": "Поиск файла",
                "Удаление": "Удаление",
                "Файлы загружены из": "Файлы загружены из",
                "Файлы добавлены в архив.": "Файлы добавлены в архив.",
                "Файл не найден.": "Файл не найден.",
                "Настройки": "Настройки",
                "Новый архив\tCtrl+N": "Новый архив\tCtrl+N",
                "Открыть архив\tCtrl+O": "Открыть архив\tCtrl+O",
                "Выход\tCtrl+Q": "Выход\tCtrl+Q",
                "Файл": "Файл",
                "Добавить файл или папку\tCtrl+A": "Добавить файл или папку\tCtrl+A",
                "Извлечь всё\tCtrl+E": "Извлечь всё\tCtrl+E",
                "Извлечь выбранное\tCtrl+Shift+E": "Извлечь выбранное\tCtrl+Shift+E",
                "Создать папку": "Создать папку",
                "Инструменты": "Инструменты",
                "Новый": "Новый",
                "Открыть": "Открыть",
                "Добавить": "Добавить",
                "Извлечь": "Извлечь",
                "Поиск": "Поиск",
                "Удалить": "Удалить",
                "Поиск файла в архиве": "Поиск файла в архиве",
                "Удалить выбранный файл": "Удалить выбранный файл",
                "Ошибка сохранения конфига: ": "Ошибка сохранения конфига: ",
                "Некорректный zip файл.": "Некорректный zip файл.",
                "Сначала откройте архив.": "Сначала откройте архив.",
                "Выберите хотя бы один файл для извлечения.": "Выберите хотя бы один файл для извлечения.",
                "Выберите файл для удаления.": "Выберите файл для удаления.",
                "Файлы удалены.": "Файлы удалены.",
                "Папка и файлы добавлены в архив.": "Папка и файлы добавлены в архив.",
                "Введите имя файла для поиска:": "Введите имя файла для поиска:",
                "Создать новый архив": "Создать новый архив",
                "Открыть существующий архив": "Открыть существующий архив",
                "Выход из приложения": "Выход из приложения",
                "Связь с разработчиком": "Связь с разработчиком",
                "Настройки приложения": "Настройки приложения",
                "Архиватор": "Архиватор",
                "Выберите язык:": "Выберите язык:",
                "Настройки языка": "Настройки языка",
                "Язык изменен. Программа будет перезапущена.": "Язык изменен. Программа будет перезапущена.",
                "Информация": "Информация",
                "Ошибка": "Ошибка",
                "Добавить файл или папку в архив": "Добавить файл или папку в архив",
                "Извлечь все файлы из архива": "Извлечь все файлы из архива",
                "Извлечь выбранный файл": "Извлечь выбранный файл",
                "Создать папку в архиве": "Создать папку в архиве",
                "Введите имя папки:": "Введите имя папки:",
                "Создание папки": "Создание папки",
                "Папка": "Папка",
                "создана.": "создана.",
                "Выберите архив": "Выберите архив",
                "Открыт архив:": "Открыт архив:",
                "Создать архив": "Создать архив",
                "Создание архива:": "Создание архива:",
                "Архив": "Архив",
                "создан.": "создан.",
                "Добавить файл (OK) или папку (Cancel)?": "Добавить файл (OK) или папку (Cancel)?",
                "Выберите файл для добавления": "Выберите файл для добавления",
                "Выберите папку для добавления": "Выберите папку для добавления",
                "Выберите папку для извлечения": "Выберите папку для извлечения",
                "Все файлы извлечены в": "Все файлы извлечены в",
                "Файлы извлечены в": "Файлы извлечены в",
                "Вы уверены, что хотите удалить": "Вы уверены, что хотите удалить",
                "файл(ов)?": "файл(ов)?"
            },
            'en': {
                "Имя файла/папки": "File/Folder Name",
                "Размер": "Size",
                "Дата изменения": "Date Modified",
                "Готово": "Ready",
                "Обратная связь": "Feedback",
                "Выбор": "Selection",
                "Поиск файла": "Search File",
                "Удаление": "Deletion",
                "Файлы загружены из": "Files loaded from",
                "Файлы добавлены в архив.": "Files added to archive.",
                "Файл не найден.": "File not found.",
                "Настройки": "Settings",
                "Новый архив\tCtrl+N": "New Archive\tCtrl+N",
                "Открыть архив\tCtrl+O": "Open Archive\tCtrl+O",
                "Выход\tCtrl+Q": "Exit\tCtrl+Q",
                "Файл": "File",
                "Добавить файл или папку\tCtrl+A": "Add File or Folder\tCtrl+A",
                "Извлечь всё\tCtrl+E": "Extract All\tCtrl+E",
                "Извлечь выбранное\tCtrl+Shift+E": "Extract Selected\tCtrl+Shift+E",
                "Создать папку": "Create Folder",
                "Инструменты": "Tools",
                "Новый": "New",
                "Открыть": "Open",
                "Добавить": "Add",
                "Извлечь": "Extract",
                "Поиск": "Search",
                "Удалить": "Delete",
                "Поиск файла в архиве": "Search file in archive",
                "Удалить выбранный файл": "Delete selected file",
                "Ошибка сохранения конфига: ": "Error saving config: ",
                "Некорректный zip файл.": "Invalid zip file.",
                "Сначала откройте архив.": "Open the archive first.",
                "Выберите хотя бы один файл для извлечения.": "Select at least one file to extract.",
                "Выберите файл для удаления.": "Select a file to delete.",
                "Файлы удалены.": "Files deleted.",
                "Папка и файлы добавлены в архив.": "Folder and files added to archive.",
                "Введите имя файла для поиска:": "Enter the file name to search:",
                "Создать новый архив": "Create new archive",
                "Открыть существующий архив": "Open existing archive",
                "Выход из приложения": "Exit application",
                "Связь с разработчиком": "Contact developer",
                "Настройки приложения": "Application settings",
                "Архиватор": "Archiver",
                "Выберите язык:": "Select language:",
                "Настройки языка": "Language settings",
                "Язык изменен. Программа будет перезапущена.": "Language changed. Application will restart.",
                "Информация": "Information",
                "Ошибка": "Error",
                "Добавить файл или папку в архив": "Add file or folder to archive",
                "Извлечь все файлы из архива": "Extract all files from archive",
                "Извлечь выбранный файл": "Extract selected file",
                "Создать папку в архиве": "Create folder in archive",
                "Введите имя папки:": "Enter folder name:",
                "Создание папки": "Create folder",
                "Папка": "Folder",
                "создана.": "created.",
                "Выберите архив": "Select archive",
                "Открыт архив:": "Archive opened:",
                "Создать архив": "Create archive",
                "Создание архива:": "Creating archive:",
                "Архив": "Archive",
                "создан.": "created.",
                "Добавить файл (OK) или папку (Cancel)?": "Add file (OK) or folder (Cancel)?",
                "Выберите файл для добавления": "Select file to add",
                "Выберите папку для добавления": "Select folder to add",
                "Выберите папку для извлечения": "Select folder for extraction",
                "Все файлы извлечены в": "All files extracted to",
                "Файлы извлечены в": "Files extracted to",
                "Вы уверены, что хотите удалить": "Are you sure you want to delete",
                "файл(ов)?": "file(s)?"
            },
            'fr': {
                "Имя файла/папки": "Nom de fichier/dossier",
                "Размер": "Taille",
                "Дата изменения": "Date modifiée",
                "Готово": "Prêt",
                "Обратная связь": "Retour",
                "Выбор": "Sélection",
                "Поиск файла": "Recherche de fichier",
                "Удаление": "Suppression",
                "Файлы загружены из": "Fichiers chargés depuis",
                "Файлы добавлены в архив.": "Fichiers ajoutés à l'archive.",
                "Файл не найден.": "Fichier non trouvé.",
                "Настройки": "Paramètres",
                "Новый архив\tCtrl+N": "Nouvelle archive\tCtrl+N",
                "Открыть архив\tCtrl+O": "Ouvrir l'archive\tCtrl+O",
                "Выход\tCtrl+Q": "Sortie\tCtrl+Q",
                "Файл": "Fichier",
                "Добавить файл или папку\tCtrl+A": "Ajouter un fichier ou dossier\tCtrl+A",
                "Извлечь всё\tCtrl+E": "Tout extraire\tCtrl+E",
                "Извлечь выбранное\tCtrl+Shift+E": "Extraire sélectionné\tCtrl+Shift+E",
                "Создать папку": "Créer un dossier",
                "Инструменты": "Outils",
                "Новый": "Nouveau",
                "Открыть": "Ouvrir",
                "Добавить": "Ajouter",
                "Извлечь": "Extraire",
                "Поиск": "Recherche",
                "Удалить": "Supprimer",
                "Поиск файла в архиве": "Recherche de fichier dans l'archive",
                "Удалить выбранный файл": "Supprimer le fichier sélectionné",
                "Ошибка сохранения конфига: ": "Erreur lors de l'enregistrement de la config: ",
                "Некорректный zip файл.": "Fichier zip invalide.",
                "Сначала откройте архив.": "Ouvrez d'abord l'archive.",
                "Выберите хотя бы один файл для извлечения.": "Sélectionnez au moins un fichier à extraire.",
                "Выберите файл для удаления.": "Sélectionnez un fichier à supprimer.",
                "Файлы удалены.": "Fichiers supprimés.",
                "Папка и файлы добавлены в архив.": "Dossier et fichiers ajoutés à l'archive.",
                "Введите имя файла для поиска:": "Entrez le nom du fichier à rechercher:",
                "Создать новый архив": "Créer une nouvelle archive",
                "Открыть существующий архив": "Ouvrir une archive existante",
                "Выход из приложения": "Quitter l'application",
                "Связь с разработчиком": "Contacter le développeur",
                "Настройки приложения": "Paramètres de l'application",
                "Архиватор": "Archiveur",
                "Выберите язык:": "Sélectionnez la langue:",
                "Настройки языка": "Paramètres de langue",
                "Язык изменен. Программа будет перезапущена.": "Langue modifiée. L'application va redémarrer.",
                "Информация": "Information",
                "Ошибка": "Erreur",
                "Добавить файл или папку в архив": "Ajouter un fichier ou dossier à l'archive",
                "Извлечь все файлы из архива": "Extraire tous les fichiers de l'archive",
                "Извлечь выбранный файл": "Extraire le fichier sélectionné",
                "Создать папку в архиве": "Créer un dossier dans l'archive",
                "Введите имя папки:": "Entrez le nom du dossier:",
                "Создание папки": "Création de dossier",
                "Папка": "Dossier",
                "создана.": "créé.",
                "Выберите архив": "Sélectionnez l'archive",
                "Открыт архив:": "Archive ouverte:",
                "Создать архив": "Créer une archive",
                "Создание архива:": "Création de l'archive:",
                "Архив": "Archive",
                "создан.": "créée.",
                "Добавить файл (OK) или папку (Cancel)?": "Ajouter un fichier (OK) ou un dossier (Annuler)?",
                "Выберите файл для добавления": "Sélectionnez le fichier à ajouter",
                "Выберите папку для добавления": "Sélectionnez le dossier à ajouter",
                "Выберите папку для извлечения": "Sélectionnez le dossier d'extraction",
                "Все файлы извлечены в": "Tous les fichiers extraits vers",
                "Файлы извлечены в": "Fichiers extraits vers",
                "Вы уверены, что хотите удалить": "Êtes-vous sûr de vouloir supprimer",
                "файл(ов)?": "fichier(s)?"
            },
            'zh': {
                "Имя файла/папки": "文件/文件夹名",
                "Размер": "大小",
                "Дата изменения": "修改日期",
                "Готово": "准备完毕",
                "Обратная связь": "反馈",
                "Выбор": "选择",
                "Поиск файла": "搜索文件",
                "Удаление": "删除",
                "Файлы загружены из": "文件从...加载",
                "Файлы добавлены в архив.": "文件已添加到档案中。",
                "Файл не найден.": "未找到文件。",
                "Настройки": "设置",
                "Новый архив\tCtrl+N": "新档案\tCtrl+N",
                "Открыть архив\tCtrl+O": "打开档案\tCtrl+O",
                "Выход\tCtrl+Q": "退出\tCtrl+Q",
                "Файл": "文件",
                "Добавить файл или папку\tCtrl+A": "添加文件或文件夹\tCtrl+A",
                "Извлечь всё\tCtrl+E": "提取全部\tCtrl+E",
                "Извлечь выбранное\tCtrl+Shift+E": "提取所选项\tCtrl+Shift+E",
                "Создать папку": "创建文件夹",
                "Инструменты": "工具",
                "Новый": "新建",
                "Открыть": "打开",
                "Добавить": "添加",
                "Извлечь": "提取",
                "Поиск": "搜索",
                "Удалить": "删除",
                "Поиск файла в архиве": "在档案中搜索文件",
                "Удалить выбранный файл": "删除所选文件",
                "Ошибка сохранения конфига: ": "保存配置时出错: ",
                "Некорректный zip файл.": "无效的zip文件。",
                "Сначала откройте архив.": "请先打开档案。",
                "Выберите хотя бы один файл для извлечения.": "请选择至少一个要提取的文件。",
                "Выберите файл для удаления.": "请选择要删除的文件。",
                "Файлы удалены.": "文件已删除。",
                "Папка и файлы добавлены в архив.": "文件夹和文件已添加到档案中。",
                "Введите имя файла для поиска:": "输入要搜索的文件名:",
                "Создать новый архив": "创建新档案",
                "Открыть существующий архив": "打开现有档案",
                "Выход из приложения": "退出应用程序",
                "Связь с разработчиком": "联系开发者",
                "Настройки приложения": "应用程序设置",
                "Архиватор": "档案管理器",
                "Выберите язык:": "选择语言：",
                "Настройки языка": "语言设置",
                "Язык изменен. Программа будет перезапущена.": "语言已更改。应用程序将重新启动。",
                "Информация": "信息",
                "Ошибка": "错误",
                "Добавить файл или папку в архив": "添加文件或文件夹到档案",
                "Извлечь все файлы из архива": "从档案中提取所有文件",
                "Извлечь выбранный файл": "提取所选文件",
                "Создать папку в архиве": "在档案中创建文件夹",
                "Введите имя папки:": "输入文件夹名称：",
                "Создание папки": "创建文件夹",
                "Папка": "文件夹",
                "создана.": "已创建。",
                "Выберите архив": "选择档案",
                "Открыт архив:": "已打开档案：",
                "Создать архив": "创建档案",
                "Создание архива:": "创建档案：",
                "Архив": "档案",
                "создан.": "已创建。",
                "Добавить файл (OK) или папку (Cancel)?": "添加文件（确定）或文件夹（取消）？",
                "Выберите файл для добавления": "选择要添加的文件",
                "Выберите папку для добавления": "选择要添加的文件夹",
                "Выберите папку для извлечения": "选择提取目标文件夹",
                "Все файлы извлечены в": "所有文件已提取到",
                "Файлы извлечены в": "文件已提取到",
                "Вы уверены, что хотите удалить": "您确定要删除",
                "файл(ов)?": "个文件吗？"
            },
            'ja': {
                "Имя файла/папки": "ファイル/フォルダー名",
                "Размер": "サイズ",
                "Дата изменения": "変更日",
                "Готово": "準備完了",
                "Обратная связь": "フィードバック",
                "Выбор": "選択",
                "Поиск файла": "ファイル検索",
                "Удаление": "削除",
                "Файлы загружены из": "ファイルが読み込まれました",
                "Файлы добавлены в архив.": "ファイルがアーカイブに追加されました。",
                "Файл не найден.": "ファイルが見つかりません。",
                "Настройки": "設定",
                "Новый архив\tCtrl+N": "新しいアーカイブ\tCtrl+N",
                "Открыть архив\tCtrl+O": "アーカイブを開く\tCtrl+O",
                "Выход\tCtrl+Q": "終了\tCtrl+Q",
                "Файл": "ファイル",
                "Добавить файл или папку\tCtrl+A": "ファイルまたはフォルダーを追加\tCtrl+A",
                "Извлечь всё\tCtrl+E": "すべて抽出\tCtrl+E",
                "Извлечь выбранное\tCtrl+Shift+E": "選択を抽出\tCtrl+Shift+E",
                "Создать папку": "フォルダーを作成",
                "Инструменты": "ツール",
                "Новый": "新しい",
                "Открыть": "開く",
                "Добавить": "追加",
                "Извлечь": "抽出",
                "Поиск": "検索",
                "Удалить": "削除",
                "Поиск файла в архиве": "アーカイブ内のファイルを検索",
                "Удалить выбранный файл": "選択したファイルを削除",
                "Ошибка сохранения конфига: ": "設定の保存中にエラーが発生しました: ",
                "Некорректный zip файл.": "無効なzipファイル。",
                "Сначала откройте архив.": "まずアーカイブを開いてください。",
                "Выберите хотя бы один файл для извлечения.": "抽出するファイルを1つ以上選択してください。",
                "Выберите файл для удаления.": "削除するファイルを選択してください。",
                "Файлы удалены.": "ファイルが削除されました。",
                "Папка и файлы добавлены в архив.": "フォルダーとファイルがアーカイブに追加されました。",
                "Введите имя файла для поиска:": "検索するファイル名を入力してください:",
                "Создать новый архив": "新しいアーカイブを作成",
                "Открыть существующий архив": "既存のアーカイブを開く",
                "Выход из приложения": "アプリケーションを終了",
                "Связь с разработчиком": "開発者に連絡",
                "Настройки приложения": "アプリケーション設定",
                "Архиватор": "アーカイバー",
                "Выберите язык:": "言語を選択：",
                "Настройки языка": "言語設定",
                "Язык изменен. Программа будет перезапущена.": "言語が変更されました。アプリケーションを再起動します。",
                "Информация": "情報",
                "Ошибка": "エラー",
                "Добавить файл или папку в архив": "アーカイブにファイルまたはフォルダーを追加",
                "Извлечь все файлы из архива": "アーカイブからすべてのファイルを抽出",
                "Извлечь выбранный файл": "選択したファイルを抽出",
                "Создать папку в архиве": "アーカイブ内にフォルダーを作成",
                "Введите имя папки:": "フォルダー名を入力：",
                "Создание папки": "フォルダーの作成",
                "Папка": "フォルダー",
                "создана.": "が作成されました。",
                "Выберите архив": "アーカイブを選択",
                "Открыт архив:": "開いたアーカイブ：",
                "Создать архив": "アーカイブを作成",
                "Создание архива:": "アーカイブの作成：",
                "Архив": "アーカイブ",
                "создан.": "が作成されました。",
                "Добавить файл (OK) или папку (Cancel)?": "ファイル（OK）またはフォルダー（キャンセル）を追加？",
                "Выберите файл для добавления": "追加するファイルを選択",
                "Выберите папку для добавления": "追加するフォルダーを選択",
                "Выберите папку для извлечения": "抽出先フォルダーを選択",
                "Все файлы извлечены в": "すべてのファイルが次の場所に抽出されました：",
                "Файлы извлечены в": "ファイルが次の場所に抽出されました：",
                "Вы уверены, что хотите удалить": "本当に削除しますか",
                "файл(ов)?": "個のファイル？"
            },
            'es': {
                "Имя файла/папки": "Nombre de archivo/carpeta",
                "Размер": "Tamaño",
                "Дата изменения": "Fecha de modificación",
                "Готово": "Listo",
                "Обратная связь": "Comentarios",
                "Выбор": "Selección",
                "Поиск файла": "Buscar archivo",
                "Удаление": "Eliminación",
                "Файлы загружены из": "Archivos cargados de",
                "Файлы добавлены в архив.": "Archivos añadidos al archivo.",
                "Файл не найден.": "Archivo no encontrado.",
                "Настройки": "Configuraciones",
                "Новый архив\tCtrl+N": "Nuevo archivo\tCtrl+N",
                "Открыть архив\tCtrl+O": "Abrir archivo\tCtrl+O",
                "Выход\tCtrl+Q": "Salir\tCtrl+Q",
                "Файл": "Archivo",
                "Добавить файл или папку\tCtrl+A": "Agregar archivo o carpeta\tCtrl+A",
                "Извлечь всё\tCtrl+E": "Extraer todo\tCtrl+E",
                "Извлечь выбранное\tCtrl+Shift+E": "Extraer seleccionado\tCtrl+Shift+E",
                "Создать папку": "Crear carpeta",
                "Инструменты": "Herramientas",
                "Новый": "Nuevo",
                "Открыть": "Abrir",
                "Добавить": "Agregar",
                "Извлечь": "Extraer",
                "Поиск": "Buscar",
                "Удалить": "Eliminar",
                "Поиск файла в архиве": "Buscar archivo en el archivo",
                "Удалить выбранный файл": "Eliminar archivo seleccionado",
                "Ошибка сохранения конфига: ": "Error al guardar la configuración: ",
                "Некорректный zip файл.": "Archivo zip inválido.",
                "Сначала откройте архив.": "Primero abre el archivo.",
                "Выберите хотя бы один файл для извлечения.": "Seleccione al menos un archivo para extraer.",
                "Выберите файл для удаления.": "Seleccione un archivo para eliminar.",
                "Файлы удалены.": "Archivos eliminados.",
                "Папка и файлы добавлены в архив.": "Carpeta y archivos añadidos al archivo.",
                "Введите имя файла для поиска:": "Ingrese el nombre del archivo a buscar:",
                "Создать новый архив": "Crear nuevo archivo",
                "Открыть существующий архив": "Abrir archivo existente",
                "Выход из приложения": "Salir de la aplicación",
                "Связь с разработчиком": "Contactar al desarrollador",
                "Настройки приложения": "Configuración de la aplicación",
                "Архиватор": "Archivador",
                "Выберите язык:": "Seleccione el idioma:",
                "Настройки языка": "Configuración de idioma",
                "Язык изменен. Программа будет перезапущена.": "Idioma cambiado. La aplicación se reiniciará.",
                "Информация": "Información",
                "Ошибка": "Error",
                "Добавить файл или папку в архив": "Agregar archivo o carpeta al archivo",
                "Извлечь все файлы из архива": "Extraer todos los archivos del archivo",
                "Извлечь выбранный файл": "Extraer archivo seleccionado",
                "Создать папку в архиве": "Crear carpeta en el archivo",
                "Введите имя папки:": "Ingrese el nombre de la carpeta:",
                "Создание папки": "Crear carpeta",
                "Папка": "Carpeta",
                "создана.": "creada.",
                "Выберите архив": "Seleccionar archivo",
                "Открыт архив:": "Archivo abierto:",
                "Создать архив": "Crear archivo",
                "Создание архива:": "Creando archivo:",
                "Архив": "Archivo",
                "создан.": "creado.",
                "Добавить файл (OK) или папку (Cancel)?": "¿Agregar archivo (OK) o carpeta (Cancelar)?",
                "Выберите файл для добавления": "Seleccione archivo para agregar",
                "Выберите папку для добавления": "Seleccione carpeta para agregar",
                "Выберите папку для извлечения": "Seleccione carpeta para extraer",
                "Все файлы извлечены в": "Todos los archivos extraídos en",
                "Файлы извлечены в": "Archivos extraídos en",
                "Вы уверены, что хотите удалить": "¿Está seguro de que desea eliminar",
                "файл(ов)?": "archivo(s)?"
            },
            'be': {
                "Имя файла/папки": "Імя файла/папкі",
                "Размер": "Памер",
                "Дата изменения": "Дата змены",
                "Готово": "Гатова",
                "Обратная связь": "Зваротная сувязь",
                "Выбор": "Выбар",
                "Поиск файла": "Пошук файла",
                "Удаление": "Выдаленне",
                "Файлы загружены из": "Файлы загружаны з",
                "Файлы добавлены в архив.": "Файлы дададзены ў архіў.",
                "Файл не найден.": "Файл не знойдзены.",
                "Настройки": "Налады",
                "Новый архив\tCtrl+N": "Новы архів\tCtrl+N",
                "Открыть архив\tCtrl+O": "Адкрыць архіў\tCtrl+O",
                "Выход\tCtrl+Q": "Выхад\tCtrl+Q",
                "Файл": "Файл",
                "Добавить файл или папку\tCtrl+A": "Дадаць файл або папку\tCtrl+A",
                "Извлечь всё\tCtrl+E": "Аднавіць усё\tCtrl+E",
                "Извлечь выбранное\tCtrl+Shift+E": "Аднавіць выбранае\tCtrl+Shift+E",
                "Создать папку": "Стварыць папку",
                "Инструменты": "Інструменты",
                "Новый": "Новы",
                "Открыть": "Адкрыць",
                "Добавить": "Дадаць",
                "Извлечь": "Аднавіць",
                "Поиск": "Пошук",
                "Удалить": "Выдаліць",
                "Поиск файла в архиве": "Пошук файла ў архіве",
                "Удалить выбранный файл": "Выдаліць выбраны файл",
                "Ошибка сохранения конфига: ": "Памылка пры захаванні канфігурацыі: ",
                "Некорректный zip файл.": "Недапушчальны zip файл.",
                "Сначала откройте архив.": "Спачатку адкрыйце архіў.",
                "Выберите хотя бы один файл для извлечения.": "Выберыце прынамсі адзін файл для аднаўлення.",
                "Выберите файл для удаления.": "Выберыце файл для выдалення.",
                "Файлы удалены.": "Файлы выдалены.",
                "Папка и файлы добавлены в архив.": "Папка і файлы дададзены ў архіў.",
                "Введите имя файла для поиска:": "Увядзіце імя файла для пошуку:",
                "Создать новый архив": "Стварыць новы архіў",
                "Открыть существующий архив": "Адкрыць існуючы архіў",
                "Выход из приложения": "Выхад з праграмы",
                "Связь с разработчиком": "Сувязь з распрацоўшчыкам",
                "Настройки приложения": "Налады праграмы",
                "Архиватор": "Архіватар",
                "Выберите язык:": "Выберыце мову:",
                "Настройки языка": "Налады мовы",
                "Язык изменен. Программа будет перезапущена.": "Мова зменена. Праграма будзе перазапушчана.",
                "Информация": "Інфармацыя",
                "Ошибка": "Памылка",
                "Добавить файл или папку в архив": "Дадаць файл або папку ў архіў",
                "Извлечь все файлы из архива": "Аднавіць усе файлы з архіва",
                "Извлечь выбранный файл": "Аднавіць выбраны файл",
                "Создать папку в архиве": "Стварыць папку ў архіве",
                "Введите имя папки:": "Увядзіце імя папкі:",
                "Создание папки": "Стварэнне папкі",
                "Папка": "Папка",
                "создана.": "створана.",
                "Выберите архив": "Выберыце архіў",
                "Открыт архив:": "Адкрыты архіў:",
                "Создать архив": "Стварыць архіў",
                "Создание архива:": "Стварэнне архіва:",
                "Архив": "Архіў",
                "создан.": "створаны.",
                "Добавить файл (OK) или папку (Cancel)?": "Дадаць файл (OK) ці папку (Адмена)?",
                "Выберите файл для добавления": "Выберыце файл для даданння",
                "Выберите папку для добавления": "Выберыце папку для даданння",
                "Выберите папку для извлечения": "Выберыце папку для аднаўлення",
                "Все файлы извлечены в": "Усе файлы адноўлены ў",
                "Файлы извлечены в": "Файлы адноўлены ў",
                "Вы уверены, что хотите удалить": "Вы ўпэўнены, што жадаеце выдаліць",
                "файл(ов)?": "файл(аў)?"
            }
        }
        return translations[self.language].get(text, text)

    def on_open_settings(self, event):
        dialog = wx.SingleChoiceDialog(
            self, 
            self.get_translation("Выберите язык:"),
            self.get_translation("Настройки языка"),
            ["Русский", "English", "Français", "中文", "日本語", "Español", "Беларуская"]
        )
        current_selection = 0 if self.language == 'ru' else 1 if self.language == 'en' else 2 if self.language == 'fr' else 3 if self.language == 'zh' else 4 if self.language == 'ja' else 5 if self.language == 'es' else 6
        dialog.SetSelection(current_selection)
        if dialog.ShowModal() == wx.ID_OK:
            selection = dialog.GetStringSelection()
            old_language = self.language
            if selection == "Русский":
                self.language = 'ru'
            elif selection == "English":
                self.language = 'en'
            elif selection == "Français":
                self.language = 'fr'
            elif selection == "中文":
                self.language = 'zh'
            elif selection == "日本語":
                self.language = 'ja'
            elif selection == "Español":
                self.language = 'es'
            elif selection == "Беларуская":
                self.language = 'be'
            if old_language != self.language:
                self.save_config()
                dialog.Destroy()
                msg = self.get_translation("Язык изменен. Программа будет перезапущена.") if self.language == 'ru' else "Language changed. The application will restart."
                wx.MessageBox(msg, self.get_translation("Информация"), wx.OK | wx.ICON_INFORMATION)
                self.Close()
                self.restart_application()
            else:
                dialog.Destroy()
        else:
            dialog.Destroy()

    def on_feedback(self, event):
        wx.MessageBox("Для обратной связи свяжитесь со мной в Discord: nonamecgalockoi", self.get_translation("Обратная связь"), wx.OK | wx.ICON_INFORMATION)

    def on_item_double_click(self, event):
        item = event.GetItem()
        item_name = item.GetText()
        if item_name.endswith('/'):
            self.current_folder = os.path.join(self.current_folder, item_name)
            self.update_file_list()

    def on_create_folder(self, event):
        if not self.archive_name:
            self.show_error_dialog(self.get_translation("Сначала откройте архив."))
            return
        dialog = wx.TextEntryDialog(self, self.get_translation("Введите имя папки:"), self.get_translation("Создание папки"), "")
        if dialog.ShowModal() == wx.ID_OK:
            folder_name = dialog.GetValue() + '/'
            if folder_name:
                try:
                    if self.archive_name.lower().endswith('.zip'):
                        with zipfile.ZipFile(self.archive_name, 'a') as archive:
                            archive.writestr(os.path.join(self.current_folder, folder_name), b'')
                    elif self.archive_name.lower().endswith('.tar'):
                        with tarfile.open(self.archive_name, 'a') as archive:
                            archive.addfile(tarfile.TarInfo(os.path.join(self.current_folder, folder_name)))
                    self.show_info_dialog(f"{self.get_translation('Папка')} '{folder_name}' {self.get_translation('создана.')}")
                    self.update_file_list()
                except Exception as e:
                    self.show_error_dialog(str(e))

    def on_select_archive(self, event):
        wildcard = "Архивы (*.zip;*.tar)|*.zip;*.tar"
        with wx.FileDialog(self, self.get_translation("Выберите архив"), wildcard=wildcard, style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return
            self.archive_name = fileDialog.GetPath()
            self.current_folder = ""
            self.status_bar.SetStatusText(f"{self.get_translation('Открыт архив:')} {self.archive_name}")
            self.update_file_list()

    def on_create_archive(self, event):
        wildcard = "Архивы (*.zip;*.tar)|*.zip;*.tar"
        with wx.FileDialog(self, self.get_translation("Создать архив"), wildcard=wildcard, style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return
            self.archive_name = fileDialog.GetPath()
            self.current_folder = ""
            self.status_bar.SetStatusText(f"{self.get_translation('Создание архива:')} {self.archive_name}")
            try:
                if self.archive_name.lower().endswith('.zip'):
                    with zipfile.ZipFile(self.archive_name, 'w') as archive:
                        pass
                elif self.archive_name.lower().endswith('.tar'):
                    with tarfile.open(self.archive_name, 'w') as archive:
                        pass
                self.show_info_dialog(f"{self.get_translation('Архив')} {self.archive_name} {self.get_translation('создан.')}.")
            except Exception as e:
                self.show_error_dialog(str(e))
            self.update_file_list()

    def show_info_dialog(self, message):
        wx.MessageBox(message, self.get_translation("Информация"), wx.OK | wx.ICON_INFORMATION)

    def show_error_dialog(self, message):
        wx.MessageBox(message, self.get_translation("Ошибка"), wx.OK | wx.ICON_ERROR)

    def on_add_file_or_folder(self, event):
        if not self.archive_name:
            self.show_error_dialog(self.get_translation("Сначала откройте архив."))
            return
        options = wx.MessageBox(f"{self.get_translation('Добавить файл (OK) или папку (Cancel)?')}", self.get_translation("Выбор"), wx.OK | wx.CANCEL | wx.ICON_QUESTION)
        if options == wx.OK:
            with wx.FileDialog(self, self.get_translation("Выберите файл для добавления"), wildcard="*.*", style=wx.FD_OPEN | wx.FD_MULTIPLE) as fileDialog:
                if fileDialog.ShowModal() == wx.ID_OK:
                    paths = fileDialog.GetPaths()
                    try:
                        if self.archive_name.lower().endswith('.zip'):
                            with zipfile.ZipFile(self.archive_name, 'a') as archive:
                                for file_path in paths:
                                    arcname = os.path.join(self.current_folder, os.path.basename(file_path))
                                    archive.write(file_path, arcname)
                        elif self.archive_name.lower().endswith('.tar'):
                            with tarfile.open(self.archive_name, 'a') as archive:
                                for file_path in paths:
                                    archive.add(file_path, os.path.join(self.current_folder, os.path.basename(file_path)))
                        self.show_info_dialog(self.get_translation("Файлы добавлены в архив."))
                    except Exception as e:
                        self.show_error_dialog(str(e))
        elif options == wx.CANCEL:
            with wx.DirDialog(self, self.get_translation("Выберите папку для добавления"), style=wx.DD_DEFAULT_STYLE) as dirDialog:
                if dirDialog.ShowModal() == wx.ID_OK:
                    folder_path = dirDialog.GetPath()
                    try:
                        if self.archive_name.lower().endswith('.zip'):
                            with zipfile.ZipFile(self.archive_name, 'a') as archive:
                                for root, dirs, files in os.walk(folder_path):
                                    for file in files:
                                        file_path = os.path.join(root, file)
                                        arcname = os.path.relpath(file_path, start=folder_path)
                                        archive.write(file_path, os.path.join(self.current_folder, arcname))
                        elif self.archive_name.lower().endswith('.tar'):
                            with tarfile.open(self.archive_name, 'a') as archive:
                                for root, dirs, files in os.walk(folder_path):
                                    for file in files:
                                        file_path = os.path.join(root, file)
                                        arcname = os.path.relpath(file_path, start=folder_path)
                                        archive.add(file_path, os.path.join(self.current_folder, arcname))
                        self.show_info_dialog(self.get_translation("Папка и файлы добавлены в архив."))
                    except Exception as e:
                        self.show_error_dialog(str(e))
        self.update_file_list()

    def on_extract_all(self, event):
        if not self.archive_name:
            self.show_error_dialog(self.get_translation("Сначала откройте архив."))
            return
        with wx.DirDialog(self, self.get_translation("Выберите папку для извлечения"), style=wx.DD_DEFAULT_STYLE) as dirDialog:
            if dirDialog.ShowModal() == wx.ID_CANCEL:
                return
            extract_path = dirDialog.GetPath()
            try:
                if self.archive_name.lower().endswith('.zip'):
                    with zipfile.ZipFile(self.archive_name, 'r') as archive:
                        archive.extractall(extract_path)
                elif self.archive_name.lower().endswith('.tar'):
                    with tarfile.open(self.archive_name, 'r') as archive:
                        archive.extractall(extract_path)
                self.show_info_dialog(f"{self.get_translation('Все файлы извлечены в')} {extract_path}.")
            except zipfile.BadZipFile:
                self.show_error_dialog(self.get_translation("Некорректный zip файл."))
            except Exception as e:
                self.show_error_dialog(str(e))

    def on_extract_selected(self, event):
        if not self.archive_name:
            self.show_error_dialog(self.get_translation("Сначала откройте архив."))
            return
        selected_items = self.list_ctrl.GetSelectedItemCount()
        if selected_items == 0:
            self.show_error_dialog(self.get_translation("Выберите хотя бы один файл для извлечения."))
            return
        with wx.DirDialog(self, self.get_translation("Выберите папку для извлечения"), style=wx.DD_DEFAULT_STYLE) as dirDialog:
            if dirDialog.ShowModal() == wx.ID_CANCEL:
                return
            extract_path = dirDialog.GetPath()
            try:
                if self.archive_name.lower().endswith('.zip'):
                    with zipfile.ZipFile(self.archive_name, 'r') as archive:
                        for index in range(self.list_ctrl.GetItemCount()):
                            if self.list_ctrl.IsSelected(index):
                                file_name = os.path.join(self.current_folder, self.list_ctrl.GetItemText(index))
                                archive.extract(file_name, extract_path)
                elif self.archive_name.lower().endswith('.tar'):
                    with tarfile.open(self.archive_name, 'r') as archive:
                        for index in range(self.list_ctrl.GetItemCount()):
                            if self.list_ctrl.IsSelected(index):
                                file_name = os.path.join(self.current_folder, self.list_ctrl.GetItemText(index))
                                archive.extract(file_name, extract_path)
                self.show_info_dialog(f"{self.get_translation('Файлы извлечены в')} {extract_path}.")
            except zipfile.BadZipFile:
                self.show_error_dialog(self.get_translation("Некорректный zip файл."))
            except Exception as e:
                self.show_error_dialog(str(e))

    def delete_selected_file(self, event):
        selected_items = self.list_ctrl.GetSelectedItemCount()
        if selected_items == 0:
            self.show_error_dialog(self.get_translation("Выберите файл для удаления."))
            return
        selected_file_names = [os.path.join(self.current_folder, self.list_ctrl.GetItemText(i)) for i in range(self.list_ctrl.GetItemCount()) if self.list_ctrl.IsSelected(i)]
        if wx.MessageBox(f"{self.get_translation('Вы уверены, что хотите удалить')} {len(selected_file_names)} {self.get_translation('файл(ов)?')}", self.get_translation("Удаление"), wx.YES_NO | wx.ICON_WARNING) == wx.NO:
            return
        temp_archive = self.archive_name + ".tmp"
        try:
            if self.archive_name.lower().endswith('.zip'):
                with zipfile.ZipFile(self.archive_name, 'r') as archive:
                    with zipfile.ZipFile(temp_archive, 'w') as temp_zip:
                        for file_info in archive.infolist():
                            if file_info.filename not in selected_file_names:
                                temp_zip.writestr(file_info.filename, archive.read(file_info.filename))
            elif self.archive_name.lower().endswith('.tar'):
                with tarfile.open(self.archive_name, 'r') as archive:
                    with tarfile.open(temp_archive, 'w') as temp_tar:
                        for file_info in archive.getmembers():
                            if file_info.name not in selected_file_names:
                                temp_tar.addfile(file_info, archive.extractfile(file_info))
            os.remove(self.archive_name)
            os.rename(temp_archive, self.archive_name)
            self.show_info_dialog(self.get_translation("Файлы удалены."))
            self.update_file_list()
        except Exception as e:
            self.show_error_dialog(str(e))

    def on_exit(self, event):
        self.Close(True)

    def update_file_list(self):
        self.list_ctrl.DeleteAllItems()
        try:
            if self.archive_name.lower().endswith('.zip'):
                with zipfile.ZipFile(self.archive_name, 'r') as archive:
                    for file_info in archive.infolist():
                        if file_info.filename.startswith(self.current_folder):
                            display_name = file_info.filename[len(self.current_folder):] if self.current_folder else file_info.filename
                            display_name = display_name if display_name else file_info.filename
                            index = self.list_ctrl.InsertItem(self.list_ctrl.GetItemCount(), display_name)
                            if not display_name.endswith('/'):
                                self.list_ctrl.SetItem(index, 1, str(file_info.file_size))
                                date_time = datetime(*file_info.date_time)
                                self.list_ctrl.SetItem(index, 2, date_time.strftime("%Y-%m-%d %H:%M:%S"))
            elif self.archive_name.lower().endswith('.tar'):
                with tarfile.open(self.archive_name, 'r') as archive:
                    for file_info in archive.getmembers():
                        if file_info.name.startswith(self.current_folder):
                            display_name = file_info.name[len(self.current_folder):] if self.current_folder else file_info.name
                            display_name = display_name if display_name else file_info.name
                            index = self.list_ctrl.InsertItem(self.list_ctrl.GetItemCount(), display_name)
                            if not display_name.endswith('/'):
                                self.list_ctrl.SetItem(index, 1, str(file_info.size))
                                date_time = datetime.fromtimestamp(file_info.mtime)
                                self.list_ctrl.SetItem(index, 2, date_time.strftime("%Y-%m-%d %H:%M:%S"))
            self.status_bar.SetStatusText(f"{self.get_translation('Файлы загружены из')} {self.archive_name}.")
        except Exception as e:
            self.show_error_dialog(str(e))

    def on_search_file(self, event):
        dialog = wx.TextEntryDialog(self, self.get_translation("Введите имя файла для поиска:"), self.get_translation("Поиск файла"), "")
        if dialog.ShowModal() == wx.ID_OK:
            search_text = dialog.GetValue().lower()
            self.search_in_archive(search_text)
        dialog.Destroy()

    def search_in_archive(self, search_text):
        if not self.archive_name:
            self.show_error_dialog(self.get_translation("Сначала откройте архив."))
            return
        self.list_ctrl.DeleteAllItems()
        try:
            found = False
            if self.archive_name.lower().endswith('.zip'):
                with zipfile.ZipFile(self.archive_name, 'r') as archive:
                    for file_info in archive.infolist():
                        if search_text in file_info.filename.lower():
                            found = True
                            display_name = file_info.filename[len(self.current_folder):] if self.current_folder else file_info.filename
                            index = self.list_ctrl.InsertItem(self.list_ctrl.GetItemCount(), display_name)
                            self.list_ctrl.SetItem(index, 1, str(file_info.file_size))
                            date_time = datetime(*file_info.date_time)
                            self.list_ctrl.SetItem(index, 2, date_time.strftime("%Y-%m-%d %H:%M:%S"))
            elif self.archive_name.lower().endswith('.tar'):
                with tarfile.open(self.archive_name, 'r') as archive:
                    for file_info in archive.getmembers():
                        if search_text in file_info.name.lower():
                            found = True
                            display_name = file_info.name[len(self.current_folder):] if self.current_folder else file_info.name
                            index = self.list_ctrl.InsertItem(self.list_ctrl.GetItemCount(), display_name)
                            self.list_ctrl.SetItem(index, 1, str(file_info.size))
                            date_time = datetime.fromtimestamp(file_info.mtime)
                            self.list_ctrl.SetItem(index, 2, date_time.strftime("%Y-%m-%d %H:%M:%S"))
            if not found:
                self.show_info_dialog(self.get_translation("Файл не найден."))
        except Exception as e:
            self.show_error_dialog(str(e))

if __name__ == "__main__":
    app = wx.App(False)
    frame = Archiver(None, "Архиватор")
    app.MainLoop()
