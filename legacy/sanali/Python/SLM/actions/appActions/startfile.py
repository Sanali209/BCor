import os

from SLM.flet.flet_ext import flet_dialog_alert

import SLM.actions as ac


@ac.action_manager.register()
class AppActionStartFile(ac.AppAction):
    """
        This class represents an action to open a file with its associated editor.

        It inherits from the AppAction class and overrides the run method to implement the specific behavior of opening a file.
        """
    def __init__(self):
        super().__init__(name="show on associated editor", description="show in associated editor")

    def run(self, *args, **kwargs):
        """
                Runs the action to open a file with its associated editor.

                Args:
                    *args: The arguments for the action. The first argument should be the path of the file to open.
                    **kwargs: Additional keyword arguments. Not used in this method.

                Raises:
                    flet_dialog_alert: If the file does not exist, an alert dialog is shown with the title "Error" and the content "path not exists".

                sa
                """
        path = args[0]
        if not os.path.exists(path):
            dialog = flet_dialog_alert(title="Error", content="path not exists")
            dialog.show()
            return
        os.startfile(path)
