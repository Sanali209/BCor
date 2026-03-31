import os

from sqlmodel import select, col
from tqdm import tqdm

import flet as ft

from SLM.appGlue.DesignPaterns import allocator
from SLM.actions import AppAction, ActionManager
from SLM.appGlue.glue_app import GlueApp
from SLM.appGlue.images.image_anotation.imageanotation import AnnotationManager
from SLM.appGlue.images.imagesidecard import ImageSideCard, sidecard_helper, SideCardDB
from SLM.appGlue.images.image_anotation.predHelper import Image_Prediction_Helper
from SLM.flet.ext import Flet_glue_app, Flet_view, FletTextFieldBind, DropdownBind


class main_view(Flet_view):
    def __init__(self):
        super().__init__()
        self.app = allocator.Allocator.get_instance(GlueApp)
        self.xml_source = """
        <root>
            <TextField id="source_path_text_field" label="source path"/>
            <Dropdown id="job_name_dropdown" label="job name"/>
            <ElevatedButton id="start_move_button" text="start move"/>
        </root>
        """
        self.parse_xml()
        FletTextFieldBind(self.source_path_text_field, self.app.pers_app_settings.source_path)
        self.start_move_button.on_click = lambda e: AppActionMoveToDirectoryByAnnotation().run(
            self.app.pers_app_settings.source_path.val, self.app.pers_app_settings.job_name.val)

        annotationManager = AnnotationManager()
        all_jobs_names = annotationManager.get_all_jobs_names("image_multiclass")

        self.job_name_dropdown: ft.Dropdown = self.job_name_dropdown
        self.job_name_dropdown.options = [ft.dropdown.Option(x) for x in all_jobs_names]
        self.job_name_dropdown.value = all_jobs_names[0]
        DropdownBind(self.job_name_dropdown, self.app.pers_app_settings.job_name)


class bindings:
    pass


class my_app(Flet_glue_app):
    def __init__(self):
        super().__init__()
        self.pers_app_settings.Initialize()

        self.start_view = main_view()

        action_manager: ActionManager = ActionManager()
        print(action_manager.actions)


@ActionManager().register()
class AppActionMoveToDirectoryByAnnotation(AppAction):
    def __init__(self):
        super().__init__(name="move to directory by annotation", description="move to directory by annotation")

    def run(self, *args, **kwargs):
        app: my_app = allocator.Allocator.get_instance(GlueApp)
        path = args[0]
        if not os.path.exists(path):
            dialog = ft.AlertDialog(title=ft.Text("Error"), content=ft.Text("path not exists"))
            app.page.dialog = dialog
            dialog.open = True
            app.page.update()
            return
        job_name = args[1]

        query = select(ImageSideCard).where(col(ImageSideCard.image_path).like(f"{path}%"))
        result = SideCardDB().session.exec(query).all()
        for image in tqdm(result):
            annotations = Image_Prediction_Helper.get_predictions_by_name(image, job_name)
            if len(annotations) == 0:
                continue
            annotation = annotations[0]
            print(f"{image.image_path} -> {annotation.label}")
            dir_name = os.path.dirname(image.image_path) + "\\" + annotation.label
            sidecard_helper.move_image_to_path(image, dir_name)


my_app().run()
