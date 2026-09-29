import os
import sys
import traceback
from pathlib import Path
import tempfile

os.environ["QT_QPA_PLATFORM"] = "offscreen"

log_file = open("test_err.log", "w", encoding="utf-8")

def log(msg):
    log_file.write(str(msg) + "\n")
    log_file.flush()
    print(msg, flush=True)

try:
    log("Starting script")
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication(sys.argv)
    log("QApplication initialized")

    from app.main import PreViewAIService, run_gui_mode

    tmp_path = Path(tempfile.mkdtemp())
    mock_project = tmp_path / "my_project"
    mock_project.mkdir()
    (mock_project / "train.py").write_text("import dataset\nprint('training...')", encoding="utf-8")
    (mock_project / "app.py").write_text("import dataset\nimport train\nprint('running app...')", encoding="utf-8")
    ds_dir = mock_project / "dataset"
    ds_dir.mkdir()
    (ds_dir / "data.csv").write_text("id,val\n1,10", encoding="utf-8")

    log("Instantiating PreViewAIService")
    svc = PreViewAIService(project_root=str(mock_project))
    log("PreViewAIService created")

    log("Calling run_gui_mode")
    window = run_gui_mode(svc, project_path=str(mock_project), start_loop=False)
    log("run_gui_mode returned window!")

    app.processEvents()
    log("processEvents completed")

    window._selected_path = None
    window._update_action_bar_state()
    log("Action bar updated")

    assert not window._btn_cut.isEnabled()
    assert not window._btn_copy.isEnabled()
    assert not window._btn_rename.isEnabled()
    assert not window._btn_delete.isEnabled()
    assert not window._btn_sim_act.isEnabled()
    assert not window._btn_paste.isEnabled()
    log("Initial assertion passed")

    ds_path = str(mock_project / "dataset")
    idx = window._fs_model.index(ds_path)
    log(f"Index for dataset: valid={idx.isValid()}")
    assert idx.isValid()

    window._file_view.setCurrentIndex(idx)
    log("Calling _on_file_clicked")
    window._on_file_clicked(idx)
    log("_on_file_clicked done")

    log(f"btn_cut.isEnabled={window._btn_cut.isEnabled()}")
    log(f"btn_copy.isEnabled={window._btn_copy.isEnabled()}")
    log(f"btn_rename.isEnabled={window._btn_rename.isEnabled()}")
    log(f"btn_delete.isEnabled={window._btn_delete.isEnabled()}")
    log(f"btn_sim_act.isEnabled={window._btn_sim_act.isEnabled()}")

    assert window._btn_cut.isEnabled()
    assert window._btn_copy.isEnabled()
    assert window._btn_rename.isEnabled()
    assert window._btn_delete.isEnabled()
    assert window._btn_sim_act.isEnabled()
    log("Selection assertions passed!")

    if window._scan_worker and window._scan_worker.isRunning():
        log("Waiting for scan worker...")
        window._scan_worker.wait(2000)
    if window._impact_worker and window._impact_worker.isRunning():
        log("Waiting for impact worker...")
        window._impact_worker.wait(2000)
    window.close()
    app.processEvents()
    log("ALL TESTS COMPLETED SUCCESSFULLY!")

except BaseException as e:
    log(f"EXCEPTION: {type(e).__name__}: {e}")
    traceback.print_exc(file=log_file)
    log_file.flush()
    sys.exit(1)
finally:
    log_file.close()
