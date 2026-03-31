import os
import sys
import asyncio
from qasync import QEventLoop
from src.porting.porting import WindowsLoopManager

from SLM.files_data_cache.pool import PILPool

os.environ['DATA_CACHE_MANAGER_PATH'] = 'D:\data\ImageDataManager'
from PyQt5 import uic
from PyQt5.QtCore import Qt, pyqtSignal, pyqtProperty, pyqtSlot, QObject
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, \
    QGridLayout, QScrollArea, QLineEdit, QCheckBox, QMenu, QAction, QDialog, QSizePolicy, QSlider
from PyQt5.QtGui import QPixmap, QImage, QPainter, QPen, QColor
from PIL import Image

from ImageManage.imageItem import ImageItem
from SLM.QtExt.Dialogs.stringEditor import show_string_editor
from SLM.appGlue.DesignPaterns.MessageSystem import MessageSystem
from SLM.appGlue.iotools.pathtools import move_file_ifExist
from SLM.modularity.modulemanager import ModuleManager
from SLM.metadata.MDManager.mdmanager import MDManager
from SLM.vision.ocv.imageDif import OCV_diference_hailaiter

from ImageManage.ImageSortProject import ImageSortProject
from ImageManage.grouplist import GroupList
from ImageManage.imageGroup import ImageGroup


class ImageWidget(QWidget):
    def __init__(self, parent, imageItem: ImageItem):
        super().__init__(parent)
        self.size = (300, 300)
        self.imageItem = imageItem
        self.pilImagePath = ImageSortProject().fileThumbHash.getTumbPath(imageItem.path)
        self.pilImage = PILPool.get_pil_image(self.pilImagePath)
        maxwidth = self.size[0]
        if self.pilImage.size[0] > maxwidth:
            self.pilImage.thumbnail((maxwidth, maxwidth))
        self.image = QImage(self.pilImage.tobytes("raw", "RGB"), self.pilImage.size[0], self.pilImage.size[1],
                            QImage.Format_RGB888)

        self.imageLabel = QLabel(self)
        self.imageLabel.setAlignment(Qt.AlignCenter)
        self.imageLabel.setPixmap(QPixmap.fromImage(self.image))
        self.imageLabel.setScaledContents(False)

        # on imageView left click select imageView
        self.imageLabel.mousePressEvent = lambda event: self.on_select(event)

        self.textLabel = QLabel(self)
        imagepath_text = imagepath_text.replace('\\', f'\\ ')
        self.textLabel.setText(imagepath_text)
        self.textLabel.setWordWrap(True)

        layout = QVBoxLayout()
        # marging 1 px
        layout.setContentsMargins(1, 1, 1, 1)
        layout.addWidget(self.imageLabel)
        layout.addWidget(self.textLabel)

        self.setLayout(layout)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        if self.imageItem.selected:
            # Set the red box properties
            pen = QPen(QColor("red"))
            pen.setWidth(1)
            painter.setPen(pen)

            # Draw the red box around the label
            painter.drawRect(self.rect().adjusted(1, 1, -1, -1))

    def on_select(self, event):
        if event.button() == Qt.LeftButton:
            self.imageItem.selected = not self.imageItem.selected
            # repaint
            self.update()
        elif event.button() == Qt.RightButton:
            self.show_context_menu(event.globalPos())

    def show_context_menu(self, pos):
        context_menu = QMenu(self)
        select_action = QAction('Select', context_menu)
        context_menu.addAction(select_action)
        select_action.triggered.connect(lambda: self.on_context_select(True))

        unselect_action = QAction('Unselect', context_menu)
        context_menu.addAction(unselect_action)
        unselect_action.triggered.connect(lambda: self.on_context_select(False))

        add_xmp_tag_action = QAction('Add xmp tag', context_menu)
        context_menu.addAction(add_xmp_tag_action)
        add_xmp_tag_action.triggered.connect(self.on_context_add_xmp_tag)

        show_image_action = QAction('Show imageView', context_menu)
        context_menu.addAction(show_image_action)
        show_image_action.triggered.connect(self.on_context_show_image)

        show_diff_action = QAction('Show diff', context_menu)
        context_menu.addAction(show_diff_action)
        show_diff_action.triggered.connect(self.on_context_show_diff)

        show_diff_action = QAction('mark parent dir as imageset', context_menu)
        context_menu.addAction(show_diff_action)
        show_diff_action.triggered.connect(self.on_context_mark_parent_dir_as_imageset)

        show_diff_action = QAction('move selected to this location', context_menu)
        context_menu.addAction(show_diff_action)
        show_diff_action.triggered.connect(self.on_context_move_selected_to_this_location)

        show_diff_action = QAction('copy image path', context_menu)
        context_menu.addAction(show_diff_action)
        show_diff_action.triggered.connect(self.on_context_copy_image_path)



        context_menu.exec_(pos)

    def on_context_copy_image_path(self):
        QApplication.clipboard().setText(self.imageItem.path)

    def on_context_move_selected_to_this_location(self):
        # get selected images
        selectedImages = list(ImageSortProject().imageGroups.GetSelImages())
        # get context imageView
        selectedImage = self.imageItem
        base_path = os.path.dirname(selectedImage.path)
        # move selected images to this location
        for image in selectedImages:
            new_path = os.path.join(base_path, os.path.basename(image.path))
            move_file_ifExist(image.path, new_path)
            image.path = new_path

        # clear selection
        ImageSortProject().imageGroups.ClearSel()

        parent_window = self.parentWidget()
        while not isinstance(parent_window, MainW):
            parent_window = parent_window.parentWidget()
        parent_window.UpdateLayout()

    def on_context_add_xmp_tag(self):

        metadatamanager = MDManager(self.imageItem.path)
        metadatamanager.Read()
        #xmp_tags = metadatamanager.getXMPKeywords()
        #tags_string = ''
        #if xmp_tags:
            #tags_string = ','.join(xmp_tags)
        #xmpnew, acepted = show_string_editor("edit tags", tags_string, self)
        #if acepted:
            #tags = list(set(xmpnew.split(',')))
            #metadatamanager.setXMPKeywords(tags)
            #metadatamanager.Save()

    def on_context_mark_parent_dir_as_imageset(self):
        parentdir = os.path.dirname(self.imageItem.path)
        ImageSortProject().AddFolderAsImageSet(parentdir)

    def on_context_show_diff(self):
        # todo convert to grouplist functionality
        # faind parent group of imageView item
        parentGroup = ImageSortProject().imageGroups.ImageGetParentGroup(self.imageItem)
        # get selected images
        selectedImages = list(parentGroup.GetSelImages())
        # filter selectyon by current imageView
        selectedImages = [image for image in selectedImages if image.path != self.imageItem.path]
        # get first selected imageView
        selectedImage = selectedImages[0]
        ocv_dif_helper = OCV_diference_hailaiter(self.imageItem.path, selectedImage.path)
        ocv_dif_helper.DrawImageMachesSideBySide()

    def on_context_show_image(self):
        self.imsplash = ImageSplashWindow(self.imageItem.path)
        screen = QApplication.primaryScreen()
        display_size = screen.size()
        display_size *= 0.8
        min_display_size = display_size * 0.1
        # set window size
        self.imsplash.setMaximumSize(display_size)
        self.imsplash.setMinimumSize(min_display_size)
        self.imsplash.show()
        # set window size to imageView size
        self.imsplash.resize(self.imsplash.image.size())
        # get display size

    def on_context_select(self, select):
        self.imageItem.selected = select
        self.update()


class ImageGroupWidget(QWidget):
    def __init__(self, parent, imageGroup: ImageGroup):
        super().__init__(parent)
        self.imageGroup = imageGroup

        self.selCheckWidget = QCheckBox()
        self.selCheckWidget.setChecked(imageGroup.selected)
        self.selCheckWidget.stateChanged.connect(self.on_select)

        self.toolButSelInvert = QPushButton("InvertSel")
        self.toolButSelInvert.clicked.connect(self.invert_sel)

        # edit group label widget
        self.headerTextEdit = QLineEdit(imageGroup.label)
        # on text change
        self.headerTextEdit.textChanged.connect(lambda: setattr(imageGroup, 'label', self.headerTextEdit.text()))

        self.imageWidgets = []
        self.gridLayout = QGridLayout()
        self.gridLayout.setVerticalSpacing(2)
        self.gridLayout.setHorizontalSpacing(2)

        for i, imageItem in enumerate(imageGroup.items):
            imageWidget = ImageWidget(self, imageItem)
            self.imageWidgets.append(imageWidget)
            self.gridLayout.addWidget(imageWidget, i // 4, i % 4)

        layout = QVBoxLayout()
        toolsLayout = QHBoxLayout()
        toolsLayout.addWidget(self.selCheckWidget)
        toolsLayout.addWidget(self.headerTextEdit)
        toolsLayout.addWidget(self.toolButSelInvert)
        layout.addLayout(toolsLayout)
        layout.addLayout(self.gridLayout)
        #button tools layout


        self.setLayout(layout)

    def on_select(self):
        self.imageGroup.selected = self.selCheckWidget.isChecked()

    def invert_sel(self):
        for imageItem in self.imageWidgets:
            imageItem.imageItem.selected = not imageItem.imageItem.selected
            imageItem.update()


class GroupListWidget(QWidget):
    def __init__(self, parent, groupList):
        super().__init__(parent)
        self.groupList: GroupList = groupList
        self.GRWidgets = []
        self.groupPerPage = 20
        self.maxPage = len(self.groupList.groups) // self.groupPerPage
        self.currentPage = 0

        self.prevPageButton = QPushButton("Prev")
        self.prevPageButton.clicked.connect(self.prev_page)

        # page info label
        self.pageInfoLabel = QLabel("0/0")
        self.pageInfoLabel.setAlignment(Qt.AlignCenter)

        self.nextPageButton = QPushButton("Next")
        self.nextPageButton.clicked.connect(self.next_page)

        self.mainLayout = QVBoxLayout()
        self.GroupScrol = QScrollArea(self)
        self.GroupScrol.setWidgetResizable(True)
        self.GroupContainerLayout = QVBoxLayout()
        self.grcontainer = QWidget()
        self.grcontainer.setLayout(self.GroupContainerLayout)
        self.GroupScrol.setWidget(self.grcontainer)

        buttontoolLayout = QHBoxLayout()

        buttontoolLayout.addWidget(self.prevPageButton)
        buttontoolLayout.addWidget(self.pageInfoLabel)
        buttontoolLayout.addWidget(self.nextPageButton)

        self.mainLayout.addWidget(self.GroupScrol)
        self.mainLayout.addLayout(buttontoolLayout)

        self.setLayout(self.mainLayout)

        self.UpdateLayout()

    def next_page(self):
        if self.currentPage < self.maxPage:
            self.currentPage += 1
            self.ClearLayout()
            self.UpdateLayout()
            # scroll to top
            self.GroupScrol.verticalScrollBar().setValue(0)

    def prev_page(self):
        if self.currentPage > 0:
            self.currentPage -= 1
            self.ClearLayout()
            self.UpdateLayout()
            # scroll to top
            self.GroupScrol.verticalScrollBar().setValue(0)

    def UpdateLayout(self):
        self.maxPage = len(self.groupList.groups) // self.groupPerPage
        start = self.currentPage * self.groupPerPage
        end = start + self.groupPerPage
        self.pageInfoLabel.setText(f"{self.currentPage}/{self.maxPage}")
        drawgroups = self.groupList.groups[start:end]
        for group in drawgroups:
            groupWidget = ImageGroupWidget(self.GroupScrol, group)
            self.GRWidgets.append(groupWidget)
            self.GroupContainerLayout.addWidget(groupWidget)

    def ClearLayout(self):
        # remuve all group widgets
        for groupWidget in self.GRWidgets:
            self.GroupContainerLayout.removeWidget(groupWidget)
            groupWidget.deleteLater()
        self.GRWidgets.clear()


class ImageSplashWindow(QWidget):
    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
        self.image_path = image_path
        self.imageLabel = QLabel(self)
        self.imageLabel.setAlignment(Qt.AlignCenter)
        self.imageLabel.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)

        layout = QVBoxLayout()
        layout.addWidget(self.imageLabel)
        self.setLayout(layout)

        self.set_image()

    def set_image(self):
        self.image = QImage(self.image_path)
        self.imageLabel.setPixmap(QPixmap.fromImage(self.image).scaled(
            self.imageLabel.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        # Set window caption
        self.setWindowTitle(self.image_path)

    def resizeEvent(self, event):
        self.imageLabel.setPixmap(QPixmap.fromImage(self.image).scaled(
            self.imageLabel.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))


class MainW(QMainWindow):
    def __init__(self, presenter: Optional['ImageDedupPresenter'] = None):
        super().__init__()

        self.groupListWidget = GroupListWidget(self, ImageSortProject().imageGroups)
        self.Wactions = MainW2Actions(self, presenter)
        self.initUI()

    def initUI(self):
        # load ui from file
        uic.loadUi('mainui.ui', self)
        # add widget group list to GroupWidgetLayout layout by name

        self.GroupWidgetLayout.addWidget(self.groupListWidget)

        # add actions

        # project actions
        self.actionsearch_dubs.triggered.connect(self.Wactions.on_search_dubs)

        self.actioncreate_advision_list.triggered.connect(self.Wactions.on_create_advision_list)

        self.actionadd_image_to_sel_group.triggered.connect(self.Wactions.on_add_image_to_sel_group)

        self.actionSolve_Collisions.triggered.connect(self.Wactions.on_solve_collisions)
        self.actionAdd_to_hiden_all.triggered.connect(self.Wactions.on_add_to_hiden_all)
        self.actioncreate_list_by_neirofilter.triggered.connect(self.Wactions.on_create_list_by_neirofilter)

        # butoons actions

        # project actions
        self.pushButton_ClearSel.clicked.connect(self.Wactions.on_clear_selection)
        self.pushButton_SelAll.clicked.connect(self.Wactions.on_select_all)
        self.pushButton_Load_project.clicked.connect(self.Wactions.on_load)
        self.pushButton_Save_project.clicked.connect(self.Wactions.on_save)

        # group actions
        self.pushButton_goup_list_up.clicked.connect(self.Wactions.on_move_up)
        self.pushButton_goup_list_down.clicked.connect(self.Wactions.on_move_down)
        self.pushButton_goup_list_top.clicked.connect(self.Wactions.on_move_to_top)
        self.pushButton_goup_list_bottom.clicked.connect(self.Wactions.on_move_to_bottom)
        self.pushButton_goup_list_delete.clicked.connect(self.Wactions.on_delete_groups)
        self.pushButton_goup_list_merge.clicked.connect(self.Wactions.on_merge_groups)
        self.pushButton_goup_list_delete_with_one_or_null_image.clicked.connect(
            self.Wactions.on_delete_groups_with_one_or_null_image)
        self.pushButton_goup_list_rem_existed_images.clicked.connect(self.Wactions.rem_existed_images)

        # imageView actions
        self.pushButton_image_list_muveGroup.clicked.connect(self.Wactions.on_move_images_to_group)
        self.pushButton_Image_list_muvetogr_named.clicked.connect(self.Wactions.on_move_images_to_namedgroup)
        self.pushButton_image_list_muveGroupToNew.clicked.connect(self.Wactions.on_move_images_to_ngroup)
        self.pushButton_image_list_remove.clicked.connect(self.Wactions.on_remove_images)
        self.pushButton_image_list_remove_from_hd.clicked.connect(self.Wactions.on_remove_images_from_hd)
        self.pushButton_image_list_make_unick.clicked.connect(self.Wactions.on_make_unick)
        self.pushButton_image_list_locate.clicked.connect(self.Wactions.on_locate_selected_image)
        self.pushButton_image_list_add_propositions.clicked.connect(self.Wactions.on_add_propositions)
        self.pushButton_image_list_add_propositions2.clicked.connect(self.Wactions.on_add_propositions2)
        self.pushButton_image_list_move_to_folder.clicked.connect(self.Wactions.on_group_sel_move_to_folder)
        self.pushButton_image_list_add_hiden_pair.clicked.connect(self.Wactions.add_hiden_pair)

        # prop
        projectNameLineEdit = self.findChild(QLineEdit, 'projectNameLineEdit')
        projectNameLineEdit.setText(ImageSortProject().ProjectSettingsPath)
        projectNameLineEdit.textChanged.connect(lambda: setattr(ImageSortProject(), 'ProjectSettingsPath',
                                                                projectNameLineEdit.text()))

        horizontalSliderSimilarity = self.findChild(QSlider, 'horizontalSliderSimilarity')
        label_sim_value = self.findChild(QLabel, 'label_sim_value')
        horizontalSliderSimilarity.setValue(int(ImageSortProject().dubsThreshold * 100))
        label_sim_value.setText(str(horizontalSliderSimilarity.value()))
        horizontalSliderSimilarity.valueChanged.connect(lambda: setattr(ImageSortProject(), 'dubsThreshold',
                                                                        horizontalSliderSimilarity.value() / 100))

        def ImageSortProjectPropChanged(propname, value):
            if propname == 'ProjectSettingsPath':
                projectNameLineEdit.setText(value)
            elif propname == 'dubsThreshold':
                horizontalSliderSimilarity.setValue(int(value * 100))
                label_sim_value.setText(str(horizontalSliderSimilarity.value()))

        MessageSystem.Subscribe('ImageSortProjectPropChanged', self, ImageSortProjectPropChanged)

        self.show()

    def UpdateLayout(self):
        imagegroups_list = ImageSortProject().imageGroups
        self.groupListWidget.groupList = imagegroups_list
        self.groupListWidget.ClearLayout()
        self.groupListWidget.UpdateLayout()

    @pyqtSlot(str)
    def on_project_name_changed(self, value):
        projectNameLineEdit = self.findChild(QLineEdit, 'projectNameLineEdit')
        projectNameLineEdit.setText(value)


class MainW2Actions:
    def __init__(self, mainw: 'MainW', presenter: Optional['ImageDedupPresenter'] = None):
        self.mainw = mainw
        self.presenter = presenter

    def on_select_all(self):
        ImageSortProject().imageGroups.ImageSelectAll()
        self.mainw.UpdateLayout()

    def on_add_image_to_sel_group(self):
        add_image_path = show_string_editor("Enter image path", "", self.mainw)
        if add_image_path[1] == QDialog.Accepted:
            ImageSortProject().imageGroups.AddImageToSelGroup(add_image_path[0])
            self.mainw.UpdateLayout()



    def on_create_list_by_neirofilter(self):
        ImageSortProject().CreateListByNeiroFilter('sanali209/nsfwfilter')
        self.mainw.UpdateLayout()

    def on_add_to_hiden_all(self):
        ImageSortProject().AddHideItemAll()
        self.mainw.UpdateLayout()

    def on_solve_collisions(self):
        ImageSortProject().SolveCollision_FolderAsImageSet()
        self.mainw.UpdateLayout()

    def add_hiden_pair(self):
        # iterate trout all group
        for group in ImageSortProject().imageGroups.groups:
            # get selected images
            selectedim = list(group.GetSelImages())
            # if selected images more then 2
            if len(selectedim) > 1:
                # get key imageView
                key = selectedim[0]
                # iterate trout all selected images
                for selectedim in selectedim[1:]:
                    # add hiden pair
                    ImageSortProject().AddHideItemPair(key.path, selectedim.path)

        # clear selection
        ImageSortProject().imageGroups.ImageRemoveSelectedFromGroups()
        self.mainw.UpdateLayout()

    def rem_existed_images(self):
        ImageSortProject().imageGroups.GroupRemuveExistedImages()
        self.mainw.UpdateLayout()

    def on_locate_selected_image(self):
        ImageSortProject().imageGroups.ImageOpenSelectedInExplorer()

    def on_delete_groups_with_one_or_null_image(self):
        ImageSortProject().imageGroups.GroupDeleteWithOneoreNullImage()
        self.mainw.UpdateLayout()

    def on_remove_images(self):
        ImageSortProject().imageGroups.ImageRemoveSelectedFromGroups()
        self.mainw.UpdateLayout()

    def on_move_to_top(self):
        ImageSortProject().imageGroups.GroupMoveSelectedToTop()
        self.mainw.UpdateLayout()

    def on_move_to_bottom(self):
        ImageSortProject().imageGroups.GroupMoveSelectedToBottom()
        self.mainw.UpdateLayout()

    def on_group_sel_move_to_folder(self):
        ImageSortProject().imageGroups.GroupSelMuveToFolder()
        self.mainw.UpdateLayout()

    def on_add_propositions(self):
        ImageSortProject().imageGroups.AddSimilar(ImageSortProject().dublicateFinder)
        self.mainw.UpdateLayout()

    def on_add_propositions2(self):
        ImageSortProject().imageGroups.AddSimilar2(ImageSortProject().dublicateFinder)
        self.mainw.UpdateLayout()

    def on_make_unick(self):
        first_selected_group = ImageSortProject().imageGroups.GetSelGroups()
        listofgroups = list(first_selected_group)
        if len(listofgroups) == 0:
            return
        first_selected_group = listofgroups[0]
        ImageSortProject().imageGroups.RemoveFromOthers(first_selected_group)
        self.mainw.UpdateLayout()

    def on_remove_images_from_hd(self):
        ImageSortProject().imageGroups.ImageDeleteSelectedFromHdd()
        self.mainw.UpdateLayout()

    def on_move_images_to_group(self):
        ImageSortProject().imageGroups.ImageMoveSelToFirstSelGroup()
        self.mainw.UpdateLayout()

    def on_move_images_to_namedgroup(self):
        result = show_string_editor("Enter group name", "group", self.mainw)
        if result[1] == QDialog.Accepted:
            ImageSortProject().imageGroups.ImageMoveSelToNamedGroup(result[0])
            self.mainw.UpdateLayout()

    def on_delete_groups(self):
        ImageSortProject().imageGroups.GroupDeleteSelected()
        self.mainw.UpdateLayout()

    def on_move_up(self):
        ImageSortProject().imageGroups.GroupMoveSelectedUp()
        self.mainw.UpdateLayout()

    def on_move_down(self):
        ImageSortProject().imageGroups.GroupMoveSelectedDown()
        self.mainw.UpdateLayout()

    def on_clear_selection(self):
        ImageSortProject().imageGroups.ClearSel()
        self.mainw.UpdateLayout()

    def on_merge_groups(self):
        ImageSortProject().imageGroups.GroupMergeSelected()
        self.mainw.UpdateLayout()

    def on_save(self):
        if self.presenter:
            import asyncio
            asyncio.ensure_future(self.presenter.save_project())
        else:
            ImageSortProject().Save()

    def on_load(self):
        if self.presenter:
            import asyncio
            asyncio.ensure_future(self.presenter.load_project(ImageSortProject().ProjectSettingsPath))
        else:
            ImageSortProject().Load()
        self.mainw.UpdateLayout()

    def on_search_dubs(self):
        if self.presenter:
            import asyncio
            asyncio.ensure_future(self.presenter.search_duplicates(ImageSortProject().dubsThreshold))
        else:
            ImageSortProject().CreateDubList()
        self.mainw.UpdateLayout()

    def on_create_advision_list(self):
        if self.presenter:
            import asyncio
            asyncio.ensure_future(self.presenter.create_advision_list())
        else:
            ImageSortProject().CreateAdvisionList()
        self.mainw.UpdateLayout()

    def on_create_list_by_neirofilter(self):
        if self.presenter:
            import asyncio
            # In a real app we might want to let user chose model, but for now use default
            asyncio.ensure_future(self.presenter.create_neiro_filter_list())
        else:
            ImageSortProject().CreateListByNeiroFilter("sanali209/nsfwfilter")
        self.mainw.UpdateLayout()

    def on_move_images_to_ngroup(self):
        ImageSortProject().imageGroups.ImageMoveSelectedToNewGroup()
        self.mainw.UpdateLayout()


class ImageSortProjectQBind(QObject):
    project_name_changed = pyqtSignal(str)

    @pyqtProperty(str, notify=project_name_changed)
    def project_name(self):
        return ImageSortProject().ProjectSettingsPath

    @project_name.setter
    def project_name(self, value):
        ImageSortProject().ProjectSettingsPath = value
        self.project_name_changed.emit(value)

    @project_name.getter
    def project_name(self):
        return ImageSortProject().ProjectSettingsPath


def main():
    WindowsLoopManager.setup_loop()
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    
    modmanager = ModuleManager()
    modmanager.initialize()
    
    # 3. Prepare BCor Bridge
    from src.apps.experemental.sanali.Python.core_apps.services.service_container import get_service_container
    container = get_service_container()
    
    async def startup():
        from src.modules.sanali.presenters import ImageDedupPresenter
        from src.modules.sanali.services import ProjectStateService, NeiroFilterService, UserPreferenceService
        await container.prepare_bcor_bridge(extra_services=[
            ImageDedupPresenter, ProjectStateService, 
            NeiroFilterService, UserPreferenceService
        ])
        presenter = container.get_service(ImageDedupPresenter)
        
        mainWindow = MainW(presenter)
        mainWindow.show()
        return mainWindow

    # Use ensure_future to start the async startup
    mainWindow_task = asyncio.ensure_future(startup())
    
    try:
        # 4. Run the integrated event loop
        loop.run_forever()
    finally:
        # 4. Correctly drain the loop before exit
        loop.run_until_complete(WindowsLoopManager.drain_loop(0.2))

if __name__ == "__main__":
    main()
