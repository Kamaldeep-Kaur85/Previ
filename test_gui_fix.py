import os
import sys
from pathlib import Path
import tempfile

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PySide6.QtWidgets import QApplication
app = QApplication.instance() or QApplication(sys.argv)

from app.main import PreViewAIService, run_gui_mode

tmp_path = Path(tempfile.mkdtemp())
mock_project = tmp_path / "my_project"
mock_project.mkdir()
(mock_project / "train.py").write_text("import dataset\nprint('training...')", encoding="utf-8")
(mock_project / "app.py").write_text("import dataset\nimport train\nprint('running app...')", encoding="utf-8")
ds_dir = mock_project / "dataset"
ds_dir.mkdir()
(ds_dir / "data.csv").write_text("id,val\n1,10", encoding="utf-8")

svc = PreViewAIService(project_root=str(mock_project))
window = run_gui_mode(svc, project_path=str(mock_project), start_loop=False)

# Process events to allow Qt to initialize views
app.processEvents()

window._selected_path = None
window._update_action_bar_state()
assert not window._btn_cut.isEnabled()
assert not window._btn_copy.isEnabled()
assert not window._btn_rename.isEnabled()
assert not window._btn_delete.isEnabled()
assert not window._btn_sim_act.isEnabled()
assert not window._btn_paste.isEnabled()

ds_path = str(mock_project / "dataset")
idx = window._fs_model.index(ds_path)
assert idx.isValid()

window._file_view.setCurrentIndex(idx)
window._on_file_clicked(idx)

assert window._btn_cut.isEnabled()
assert window._btn_copy.isEnabled()
assert window._btn_rename.isEnabled()
assert window._btn_delete.isEnabled()
assert window._btn_sim_act.isEnabled()

# Clean up window and threads before exit
if window._scan_worker and window._scan_worker.isRunning():
    window._scan_worker.wait(2000)
if window._impact_worker and window._impact_worker.isRunning():
    window._impact_worker.wait(2000)
window.close()
app.processEvents()

print("GUI TEST PASSED WITH CLEANUP!", flush=True)
