from __future__ import annotations

import threading
from pathlib import Path
from typing import Optional

from kivy.clock import Clock
from kivy.logger import Logger
from kivy.metrics import dp
from kivy.properties import NumericProperty, StringProperty, BooleanProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.utils import platform

from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.label import MDLabel
from kivymd.uix.progressindicator import MDLinearProgressIndicator

from .base_screen import BaseScreen


class ModelDownloadScreen(BaseScreen):
    """Экран скачивания AI-модели для Lite версии приложения."""
    
    progress = NumericProperty(0)  # 0-100
    status_text = StringProperty("Для работы ИИ-помощника необходимо скачать модель")
    downloaded_mb = NumericProperty(0)
    total_mb = NumericProperty(1880)  # ~1.88 GB
    is_downloading = BooleanProperty(False)
    download_error = StringProperty("")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._download_thread: Optional[threading.Thread] = None
        self._cancel_flag = False
        self._content_built = False
        self._wakelock = None
    
    def on_pre_enter(self, *args):
        self.title = "Загрузка модели"
        super().on_pre_enter(*args)
        
        if not self._content_built:
            self._build_content()
            self._content_built = True
    
    def _build_content(self):
        app = self.get_app()
        bg_color = getattr(app, "mm_bg", (0.06, 0.07, 0.09, 1))
        text_color = getattr(app, "mm_text", (1, 1, 1, 1))
        text2_color = getattr(app, "mm_text2", (0.75, 0.78, 0.85, 1))
        accent_color = getattr(app, "mm_accent", (0.4, 0.6, 1, 1))
        
        self.clear_widgets()
        
        root = MDBoxLayout(
            orientation="vertical",
            padding=[dp(24), dp(24), dp(24), dp(24)],
            spacing=dp(16),
            md_bg_color=bg_color,
        )
        
        # заголовок
        title_label = MDLabel(
            text="ИИ-помощник",
            font_style="Headline",
            role="medium",
            halign="center",
            theme_text_color="Custom",
            text_color=text_color,
            size_hint_y=None,
            height=dp(48),
        )
        root.add_widget(title_label)
        
        # описание
        self._status_label = MDLabel(
            text=self.status_text,
            halign="center",
            theme_text_color="Custom",
            text_color=text2_color,
            size_hint_y=None,
            height=dp(80),
            max_lines=2,
        )
        root.add_widget(self._status_label)
        
        # размер модели
        size_label = MDLabel(
            text="Размер: ~1.88 ГБ",
            halign="center",
            theme_text_color="Custom",
            text_color=text2_color,
            size_hint_y=None,
            height=dp(32),
        )
        root.add_widget(size_label)
        
        # контейнер прогресс-бара
        progress_container = MDBoxLayout(
            orientation="vertical",
            spacing=dp(8),
            size_hint_y=None,
            height=dp(60),
            padding=[dp(16), 0, dp(16), 0],
        )
        
        self._progress_bar = MDLinearProgressIndicator(
            value=0,
            type="determinate",
            size_hint_y=None,
            height=dp(8),
        )
        progress_container.add_widget(self._progress_bar)
        
        # текст прогресса
        self._progress_label = MDLabel(
            text="0 МБ / 1880 МБ",
            halign="center",
            theme_text_color="Custom",
            text_color=text2_color,
            size_hint_y=None,
            height=dp(24),
        )
        progress_container.add_widget(self._progress_label)
        
        root.add_widget(progress_container)
        
        # сообщение об ошибке
        self._error_label = MDLabel(
            text="",
            halign="center",
            theme_text_color="Custom",
            text_color=(1, 0.4, 0.4, 1),
            size_hint_y=None,
            height=dp(48),
        )
        root.add_widget(self._error_label)
        
        # спейсер
        root.add_widget(BoxLayout(size_hint_y=1))
        
        # кнопки
        buttons_box = MDBoxLayout(
            orientation="horizontal",
            spacing=dp(16),
            size_hint_y=None,
            height=dp(56),
            padding=[dp(16), 0, dp(16), 0],
        )
        
        # кнопка "Пропустить"
        self._skip_btn = MDButton(
            style="outlined",
            size_hint_x=0.5,
            on_release=lambda x: self._on_skip(),
        )
        self._skip_btn.add_widget(MDButtonText(text="Пропустить"))
        buttons_box.add_widget(self._skip_btn)
        
        # кнопка "Скачать"
        self._download_btn = MDButton(
            style="filled",
            size_hint_x=0.5,
            on_release=lambda x: self._on_download(),
        )
        self._download_btn.add_widget(MDButtonText(text="Скачать"))
        buttons_box.add_widget(self._download_btn)
        
        root.add_widget(buttons_box)
        
        # примечание
        note_label = MDLabel(
            text="Без модели ИИ-помощник будет работать только онлайн",
            halign="center",
            theme_text_color="Custom",
            text_color=text2_color,
            font_style="Body",
            role="small",
            size_hint_y=None,
            height=dp(40),
        )
        root.add_widget(note_label)
        
        self.add_widget(root)

        def _reflow_status(*_):
            if not hasattr(self, "_status_label"):
                return
            self._status_label.text_size = (root.width - dp(32), None)
            self._status_label.font_size = min(dp(15), max(dp(11), root.width * 0.035))
            self._status_label.texture_update()
            self._status_label.height = max(dp(36), self._status_label.texture_size[1])

        root.bind(width=_reflow_status)
        Clock.schedule_once(lambda *_: _reflow_status(), 0)
        
        # привязка свойств
        self.bind(progress=self._update_progress_ui)
        self.bind(status_text=self._update_status_ui)
        self.bind(download_error=self._update_error_ui)
        self.bind(is_downloading=self._update_buttons_ui)
    
    def _update_progress_ui(self, *args):
        if hasattr(self, "_progress_bar"):
            self._progress_bar.value = self.progress / 100.0
        if hasattr(self, "_progress_label"):
            self._progress_label.text = f"{self.downloaded_mb:.0f} МБ / {self.total_mb:.0f} МБ"
    
    def _update_status_ui(self, *args):
        if hasattr(self, "_status_label"):
            self._status_label.text = self.status_text
    
    def _update_error_ui(self, *args):
        if hasattr(self, "_error_label"):
            self._error_label.text = self.download_error
    
    def _update_buttons_ui(self, *args):
        if hasattr(self, "_download_btn") and hasattr(self, "_skip_btn"):
            if self.is_downloading:
                # меняем кнопку "Скачать" на "Отмена"
                self._download_btn.clear_widgets()
                cancel_text = MDButtonText(text="Отмена", pos_hint={"center_x": 0.5, "center_y": 0.5})
                self._download_btn.add_widget(cancel_text)
                self._skip_btn.disabled = True
            else:
                self._download_btn.clear_widgets()
                download_text = MDButtonText(text="Скачать", pos_hint={"center_x": 0.5, "center_y": 0.5})
                self._download_btn.add_widget(download_text)
                self._skip_btn.disabled = False
    
    def _on_skip(self):
        """Пропустить скачивание и перейти на главный экран."""
        app = self.get_app()
        app.open_home()
    
    def _on_download(self):
        """Начать или отменить скачивание."""
        if self.is_downloading:
            self._cancel_download()
        else:
            self._start_download()
    
    def _start_download(self):
        """Запуск скачивания в фоновом потоке."""
        from utils.model_bootstrap import download_model, OFFLINE_MODEL_NAME
        
        self._cancel_flag = False
        self.is_downloading = True
        self.download_error = ""
        self.status_text = "Скачивание модели..."
        self.progress = 0
        self.downloaded_mb = 0
        self._acquire_wakelock()
        # сбрасываем прогресс-бар на 0 (без анимации)
        if hasattr(self, "_progress_bar"):
            self._progress_bar.value = 0
        
        def progress_callback(downloaded: int, total: int):
            if self._cancel_flag:
                raise Exception("Cancelled")
            
            # обновляем UI в главном потоке
            def update(dt):
                self.downloaded_mb = downloaded / (1024 * 1024)
                self.total_mb = total / (1024 * 1024)
                if total > 0:
                    self.progress = (downloaded / total) * 100
            
            Clock.schedule_once(update, 0)
        
        def download_work():
            try:
                # импортируем здесь, чтобы избежать циклического импорта
                from utils.model_bootstrap import download_model
                
                download_model(OFFLINE_MODEL_NAME, progress_callback)
                
                def on_success(dt):
                    self.is_downloading = False
                    self.status_text = "Модель успешно загружена!"
                    self.progress = 100
                    if hasattr(self, "_progress_bar"):
                        self._progress_bar.value = 1.0  # 100%
                    self._release_wakelock()
                    self._reset_quiz_progress_once()
                    # автоматически переходим на главный экран через 1.5 сек
                    Clock.schedule_once(lambda dt: self._finish_and_go_home(), 1.5)
                
                Clock.schedule_once(on_success, 0)
                
            except Exception as e:
                def on_error(dt):
                    self.is_downloading = False
                    if "Cancelled" in str(e):
                        self.status_text = "Скачивание отменено"
                        self.download_error = ""
                    else:
                        self.status_text = "Ошибка скачивания"
                        self.download_error = str(e)[:100]
                    self._release_wakelock()
                
                Clock.schedule_once(on_error, 0)
        
        self._download_thread = threading.Thread(target=download_work, daemon=True)
        self._download_thread.start()

    def start_download(self) -> None:
        """Публичный запуск скачивания с внешнего экрана."""
        if self.is_downloading:
            return
        if not self._content_built:
            self._build_content()
            self._content_built = True
        Clock.schedule_once(lambda *_: self._start_download(), 0)
    
    def _cancel_download(self):
        """Отмена скачивания."""
        self._cancel_flag = True
        self.status_text = "Отмена..."
        self._release_wakelock()
    
    def _finish_and_go_home(self):
        """Завершить и перейти на главный экран."""
        app = self.get_app()
        # перезапускаем подготовку модели
        if hasattr(app, "_prepare_offline_model_async"):
            app._prepare_offline_model_async()
        app.open_home()

    def _acquire_wakelock(self) -> None:
        if platform != "android":
            return
        try:
            if self._wakelock and self._wakelock.isHeld():
                return
        except Exception:
            pass

        try:
            from jnius import autoclass

            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            Context = autoclass("android.content.Context")
            PowerManager = autoclass("android.os.PowerManager")

            activity = PythonActivity.mActivity
            pm = activity.getSystemService(Context.POWER_SERVICE)
            self._wakelock = pm.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, "moleculementor:download")
            self._wakelock.setReferenceCounted(False)
            self._wakelock.acquire()
        except Exception as e:
            Logger.exception(f"[ModelDownload] wakelock acquire failed: {e}")

    def _release_wakelock(self) -> None:
        if platform != "android":
            return
        if not self._wakelock:
            return
        try:
            if self._wakelock.isHeld():
                self._wakelock.release()
        except Exception as e:
            Logger.exception(f"[ModelDownload] wakelock release failed: {e}")

    def _reset_quiz_progress_once(self) -> None:
        """Сбрасывает попытки тестов только при первом скачивании модели."""
        app = self.get_app()
        marker = None
        try:
            marker = Path(app.user_data_dir) / "mm_model_downloaded.flag"
        except Exception:
            marker = None

        if marker and marker.exists():
            return

        repo = getattr(app, "course_repo", None)
        if not repo:
            return

        try:
            repo.reset_all_quiz_progress()
            if marker:
                marker.write_text("ok", encoding="utf-8")
        except Exception as e:
            Logger.exception(f"[ModelDownload] reset quiz progress failed: {e}")
