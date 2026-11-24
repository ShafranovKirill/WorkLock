"""GTK interface for a visual curtain, not an operating-system lock screen."""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, Gio, GLib, Gtk  # noqa: E402

from . import config
from .password import PasswordVerifier


APP_ID = "com.github.shafranovkirill.WorkLock"


class CurtainWindow(Gtk.ApplicationWindow):
    def __init__(self, app, monitor, texture):
        super().__init__(application=app, title="WorkLock")
        self.worklock = app
        self.set_decorated(False)
        self.set_default_size(800, 600)

        overlay = Gtk.Overlay()
        picture = Gtk.Picture.new_for_paintable(texture)
        picture.set_content_fit(Gtk.ContentFit.COVER)
        picture.set_can_shrink(True)
        overlay.set_child(picture)

        click = Gtk.GestureClick()
        click.connect("pressed", lambda *_: self.show_prompt())
        picture.add_controller(click)

        panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        panel.set_halign(Gtk.Align.CENTER)
        panel.set_valign(Gtk.Align.CENTER)
        panel.set_size_request(320, -1)
        panel.set_margin_start(24)
        panel.set_margin_end(24)
        panel.set_margin_top(24)
        panel.set_margin_bottom(24)
        panel.add_css_class("card")
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        content.set_margin_start(24)
        content.set_margin_end(24)
        content.set_margin_top(24)
        content.set_margin_bottom(24)
        panel.append(content)
        title = Gtk.Label(label="Введите пароль, чтобы убрать заставку")
        title.set_wrap(True)
        content.append(title)
        self.entry = Gtk.PasswordEntry(placeholder_text="Пароль")
        self.entry.connect("activate", lambda *_: self.try_unlock())
        content.append(self.entry)
        self.error = Gtk.Label(label="")
        content.append(self.error)
        button = Gtk.Button(label="Открыть рабочий стол")
        button.add_css_class("suggested-action")
        button.connect("clicked", lambda *_: self.try_unlock())
        content.append(button)
        overlay.add_overlay(panel)
        panel.set_visible(False)
        self.panel = panel
        self.set_child(overlay)

        keys = Gtk.EventControllerKey()
        keys.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
        keys.connect("key-pressed", self.on_key)
        self.add_controller(keys)
        self.connect("close-request", self.on_close)
        self.fullscreen_on_monitor(monitor)

    def show_prompt(self):
        self.panel.set_visible(True)
        self.entry.grab_focus()

    def on_key(self, _controller, keyval, _keycode, _state):
        if keyval == Gdk.KEY_Escape and self.panel.get_visible():
            self.panel.set_visible(False)
            self.entry.set_text("")
            self.error.set_text("")
            return True
        if not self.panel.get_visible():
            self.show_prompt()
            return True  # The revealing key is not part of the password.
        return False

    def on_close(self, *_args):
        self.show_prompt()
        return True

    def try_unlock(self):
        if self.worklock.verifier.verify(self.entry.get_text()):
            self.worklock.unlock()
        else:
            self.entry.set_text("")
            self.error.set_text("Неверный пароль")
            self.entry.grab_focus()


class WorkLock(Adw.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID, flags=Gio.ApplicationFlags.DEFAULT_FLAGS)
        self.settings = None
        self.curtains = []
        self.verifier = None
        self.texture = None
        self.inhibit_cookie = 0
        self.monitor_model = None
        self.monitor_handler = None

    def do_activate(self):
        if self.verifier:
            if self.curtains:
                self.curtains[0].present()
            return
        if self.settings is None:
            self.make_settings()
        self.settings.present()

    def make_settings(self):
        self.settings = Adw.ApplicationWindow(application=self, title="WorkLock")
        self.settings.set_default_size(480, 370)
        view = Adw.ToolbarView()
        view.add_top_bar(Adw.HeaderBar())
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        box.set_margin_start(24)
        box.set_margin_end(24)
        box.set_margin_top(24)
        box.set_margin_bottom(24)
        box.append(Gtk.Label(label="Фото-заставка", xalign=0))
        self.photo_label = Gtk.Label(label="Фото не выбрано", xalign=0)
        self.photo_label.set_ellipsize(3)
        box.append(self.photo_label)
        choose = Gtk.Button(label="Выбрать фото…")
        choose.connect("clicked", self.choose_photo)
        box.append(choose)
        self.password = Gtk.PasswordEntry(placeholder_text="Пароль для этой заставки")
        box.append(self.password)
        self.confirm = Gtk.PasswordEntry(placeholder_text="Повторите пароль")
        box.append(self.confirm)
        self.keep_awake = Gtk.CheckButton(label="Не гасить экран и не переходить в сон")
        box.append(self.keep_awake)
        self.message = Gtk.Label(label="", xalign=0)
        self.message.set_wrap(True)
        box.append(self.message)
        start = Gtk.Button(label="Показать заставку")
        start.add_css_class("suggested-action")
        start.connect("clicked", self.start_curtain)
        box.append(start)
        view.set_content(box)
        self.settings.set_content(view)
        saved = config.load()
        self.image_path = saved.get("image_path", "") if isinstance(saved.get("image_path", ""), str) else ""
        self.photo_label.set_text(self.image_path or "Фото не выбрано")
        self.keep_awake.set_active(saved.get("keep_awake") is True)

    def choose_photo(self, *_args):
        dialog = Gtk.FileDialog(title="Выберите фото")
        filters = Gio.ListStore.new(Gtk.FileFilter)
        image_filter = Gtk.FileFilter()
        image_filter.set_name("Изображения")
        image_filter.add_pixbuf_formats()
        filters.append(image_filter)
        dialog.set_filters(filters)
        dialog.open(self.settings, None, self.photo_chosen)

    def photo_chosen(self, dialog, result):
        try:
            file = dialog.open_finish(result)
        except GLib.Error:
            return
        path = file.get_path()
        if path:
            self.image_path = path
            self.photo_label.set_text(path)

    def start_curtain(self, *_args):
        if not self.image_path:
            self.message.set_text("Сначала выберите фото")
            return
        password = self.password.get_text()
        if not password or password != self.confirm.get_text():
            self.message.set_text("Введите пароль и одинаковое подтверждение")
            return
        try:
            texture = Gdk.Texture.new_from_filename(self.image_path)
        except GLib.Error:
            self.message.set_text("Не удалось открыть изображение")
            return
        display = Gdk.Display.get_default()
        monitors = display.get_monitors() if display else None
        if monitors is None or monitors.get_n_items() == 0:
            self.message.set_text("Не найден экран для заставки")
            return
        self.message.set_text("")
        self.verifier = PasswordVerifier(password)
        self.password.set_text("")
        self.confirm.set_text("")
        self.texture = texture
        self.settings.set_visible(False)
        self.monitor_model = monitors
        self.monitor_handler = self.monitor_model.connect("items-changed", self.monitors_changed)
        self.sync_monitors()
        if self.keep_awake.get_active() and self.curtains:
            self.inhibit_cookie = self.inhibit(
                self.curtains[0], Gtk.ApplicationInhibitFlags.IDLE | Gtk.ApplicationInhibitFlags.SUSPEND,
                "WorkLock показывает заставку",
            )
            if not self.inhibit_cookie:
                for window in self.curtains:
                    window.error.set_text("Не удалось запретить сон системы")
        try:
            config.save(self.image_path, self.keep_awake.get_active())
        except OSError:
            pass  # Preferences are optional; the active curtain remains usable.

    def sync_monitors(self):
        current = [self.monitor_model.get_item(i) for i in range(self.monitor_model.get_n_items())]
        for window in list(self.curtains):
            if window.monitor not in current:
                self.curtains.remove(window)
                window.destroy()
        for monitor in current:
            if not any(window.monitor == monitor for window in self.curtains):
                window = CurtainWindow(self, monitor, self.texture)
                window.monitor = monitor
                self.curtains.append(window)
                window.present()

    def monitors_changed(self, *_args):
        if self.verifier:
            self.sync_monitors()

    def unlock(self):
        if self.inhibit_cookie:
            self.uninhibit(self.inhibit_cookie)
            self.inhibit_cookie = 0
        if self.monitor_model is not None and self.monitor_handler is not None:
            self.monitor_model.disconnect(self.monitor_handler)
        self.monitor_model = None
        self.monitor_handler = None
        self.verifier = None
        self.texture = None
        for window in self.curtains:
            window.destroy()
        self.curtains.clear()
        self.message.set_text("Для новой заставки введите новый пароль")
        self.settings.present()


def main():
    return WorkLock().run()
