# Legacy Import Map — sanali209 / SLM
# WARNING: This file is being read recursively. Please check for circular references or infinite loops.

> Auto-generated during Phase 0 migration analysis.
>
> Shows which legacy files depend on what SLM modules — the basis for the migration order.

## Phase 1 Domain: ImageDedup (`applications/ImageDedupApp/`)

| File | Key SLM Imports |
|---|---|
| `qtapp.py` | `SLM.files_data_cache.pool.PILPool`, `SLM.appGlue.DesignPaterns.MessageSystem`, `SLM.appGlue.iotools.pathtools`, `SLM.modularity.modulemanager`, `SLM.metadata.MDManager`, `SLM.vision.ocv.imageDif` |
| `ImageManage/ImageSortProject.py` | (core domain — no SLM dependency, standalone logic) |
| `ImageManage/grouplist.py` | (standalone domain) |
| `ImageManage/imageItem.py` | (standalone value object) |

**Migration note:** `ImageManage/` is clean domain code — can be ported directly without ACL.
The UI in `qtapp.py` uses `MessageSystem` (→ `bubus`), `Allocator` (→ `dishka`), PyQt5 (→ PySide6).

---

## Phase 2 Domain: appGlue Utilities

Most heavily depended-upon SLM utilities (used across all applications):

| Module | Users |
|---|---|
| `SLM.appGlue.iotools.pathtools` | 15+ files — `get_files`, `move_file_ifExist`, `copy_file_ifExist` |
| `SLM.appGlue.DesignPaterns.MessageSystem` | `qtapp.py`, `image_graph_qt`, `collectionTools` |
| `SLM.appGlue.core.Allocator` | 10+ files — global ServiceLocator for everything |
| `SLM.files_data_cache.pool.PILPool` | ImageDedup, image_graph_qt, LabelStudio samples |
| `SLM.files_db.*` | `image_graph_qt` files, scraper, LabelStudio |
| `SLM.metadata.MDManager` | XMP tools, scraper, LabelStudio |
| `SLM.destr_worck.bg_worcker` | `image_graph_qt`, `collectionTools` |

---

## Phase 3 Domain: LLM / NLP

| File | Key SLM Imports |
|---|---|
| `applications/llm_tags_to_xmp/` | `SLM.logging`, `SLM.metadata.*` |
| `applications/samples/console tools/…` | `SLM.NLPSimple.NLPPipline` |
| `applications/samples/imageAnalize/` | `SLM.vision.*`, `SLM.metadata.*`, `SLM.NLPSimple.*` |
| `applications/reducer samples/` | `SLM.vision.imagetotensor.*` (deep learning encoders), `SLM.files_data_cache.tensor` |

---

## Phase 4 Domain: Web / Scrapers

| File | Key SLM Imports |
|---|---|
| `applications/scraper/` | `SLM.metadata.*`, `SLM.appGlue.helpers` |
| `core_apps/duck_duck_search/` | `SLM.core.component.Component` (wraps DI components) |
| `applications/ImageSearchDuckDuckGo_PySide6/` | (TBD — standalone PySide6 app) |

---

## Summary: SLM Module Migration Mapping

| SLM Module | BCor Target | Phase |
|---|---|---|
| `SLM.appGlue.iotools.pathtools` | `src/common/io/path_tools.py` | 2 |
| `SLM.appGlue.DesignPaterns.MessageSystem` | `bubus` events | 1/2 |
| `SLM.appGlue.core.Allocator` | `dishka` Container | 2 |
| `SLM.files_data_cache.pool.PILPool` | `adapters/thumbnail_cache.py` | 1 |
| `SLM.metadata.MDManager` | `adapters/xmp_adapter.py` | 1 |
| `SLM.vision.ocv.imageDif` | `adapters/cv_differ.py` | 1 |
| `SLM.NLPSimple.NLPPipline` | `src/modules/llm/adapters/nlp.py` | 3 |
| `SLM.vision.imagetotensor.*` | `src/modules/llm/adapters/encoders/` | 3 |
| `SLM.core.component.Component` | `BaseModule` | all |
