"""macOS window arrangement for the two scrcpy processes.

macOS does not expose a supported API for embedding another process's NSWindow.
DualCPY therefore treats the two scrcpy windows as a single arranged canvas:
scrcpy supplies the video/input windows, and Accessibility moves and resizes them.
The initial layout is also passed on the scrcpy command line, so streaming works
even before Accessibility permission is granted.
"""

from dataclasses import dataclass
import logging

from . import DockManager

logger = logging.getLogger(__name__)

try:
    import Quartz
    import ApplicationServices
except ImportError:  # Covered by the startup dependency check and unit tests.
    Quartz = None
    ApplicationServices = None


@dataclass(frozen=True)
class MacWindowRef:
    pid: int
    number: int
    title: str


class MacOSDockManager(DockManager):
    """Arrange independent scrcpy windows into one capture-friendly layout."""

    supports_embedding = False

    def __init__(self):
        super().__init__()
        self._origin = (100, 100)
        self._container_size = (1, 1)
        self._capture_geometry = (100, 100, 1, 1)
        self._permission_warning_logged = False
        self._permission_prompted = False
        logger.info("Using macOS arranged-window mode")

    def create_container(self, x, y, w, h):
        self._origin = (int(x), int(y))
        self._container_size = (int(w), int(h))
        self._capture_geometry = (*self._origin, *self._container_size)
        # There is deliberately no fake empty chassis window on macOS.
        self.hwnd_container = 1
        return self.hwnd_container

    def destroy_container(self, container_id):
        self.hwnd_container = None

    def set_container_visible(self, container_id, visible):
        return None

    def resize_container(self, container_id, w, h):
        self._container_size = (int(w), int(h))
        self._capture_geometry = (*self._origin, *self._container_size)

    def get_container_geometry(self):
        return self._capture_geometry

    def process_events(self):
        return None

    def find_window(self, title):
        if Quartz is None:
            return None
        options = Quartz.kCGWindowListOptionOnScreenOnly | Quartz.kCGWindowListExcludeDesktopElements
        windows = Quartz.CGWindowListCopyWindowInfo(options, Quartz.kCGNullWindowID) or []
        for info in windows:
            name = str(info.get(Quartz.kCGWindowName, ""))
            if title.lower() in name.lower():
                return MacWindowRef(
                    pid=int(info.get(Quartz.kCGWindowOwnerPID, 0)),
                    number=int(info.get(Quartz.kCGWindowNumber, 0)),
                    title=name,
                )
        return None

    def dock_window(self, window_id, parent_id):
        # Arrangement happens in sync_layout; reparenting is not supported by macOS.
        return bool(window_id)

    def undock_window(self, window_id):
        return bool(window_id)

    def _trusted(self):
        if ApplicationServices is None:
            return False
        try:
            trusted = bool(ApplicationServices.AXIsProcessTrusted())
            if not trusted and not self._permission_prompted:
                self._permission_prompted = True
                ApplicationServices.AXIsProcessTrustedWithOptions(
                    {ApplicationServices.kAXTrustedCheckOptionPrompt: True}
                )
            return trusted
        except Exception:
            return False

    @staticmethod
    def _copy_attribute(element, attribute):
        result = ApplicationServices.AXUIElementCopyAttributeValue(element, attribute, None)
        if isinstance(result, tuple):
            return result[1] if len(result) > 1 and result[0] == 0 else None
        return result

    def _accessibility_window(self, ref):
        app = ApplicationServices.AXUIElementCreateApplication(ref.pid)
        windows = self._copy_attribute(app, ApplicationServices.kAXWindowsAttribute) or []
        for window in windows:
            title = self._copy_attribute(window, ApplicationServices.kAXTitleAttribute)
            if title and ref.title.lower() in str(title).lower():
                return window
        return None

    def _place(self, ref, x, y, width, height):
        if not ref or not self._trusted():
            if not self._permission_warning_logged:
                logger.warning(
                    "Live window positioning needs macOS Accessibility permission "
                    "for Terminal (or DualCPY when packaged). Initial placement still works."
                )
                self._permission_warning_logged = True
            return False
        try:
            window = self._accessibility_window(ref)
            if window is None:
                return False
            point = ApplicationServices.AXValueCreate(
                ApplicationServices.kAXValueCGPointType, (float(x), float(y))
            )
            size = ApplicationServices.AXValueCreate(
                ApplicationServices.kAXValueCGSizeType, (float(width), float(height))
            )
            position_error = ApplicationServices.AXUIElementSetAttributeValue(
                window, ApplicationServices.kAXPositionAttribute, point
            )
            size_error = ApplicationServices.AXUIElementSetAttributeValue(
                window, ApplicationServices.kAXSizeAttribute, size
            )
            return position_error == 0 and size_error == 0
        except Exception as exc:
            logger.debug("Could not position macOS window: %s", exc)
            return False

    def sync_layout(self, tx, ty, bx, by, w1, h1, w2, h2, is_docked=True):
        ox, oy = self._origin
        tx, ty, bx, by = map(int, (tx, ty, bx, by))
        w1, h1, w2, h2 = map(int, (w1, h1, w2, h2))
        self._place(self.hwnd_top, ox + tx, oy + ty, w1, h1)
        self._place(self.hwnd_bottom, ox + bx, oy + by, w2, h2)

        left = min(tx, bx)
        top = min(ty, by)
        right = max(tx + w1, bx + w2)
        bottom = max(ty + h1, by + h2)
        self._capture_geometry = (ox + left, oy + top, right - left, bottom - top)

    def set_window_simple_focus(self, window_id):
        if not window_id or ApplicationServices is None:
            return False
        try:
            app = ApplicationServices.AXUIElementCreateApplication(window_id.pid)
            return ApplicationServices.AXUIElementSetAttributeValue(
                app, ApplicationServices.kAXFrontmostAttribute, True
            ) == 0
        except Exception:
            return False
