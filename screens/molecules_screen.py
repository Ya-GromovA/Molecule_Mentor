
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from kivy.clock import Clock
from kivy.logger import Logger
from kivy.metrics import dp
from kivy.graphics import Color, Line
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivy.graphics import Color, Line
from kivy.uix.screenmanager import Screen

from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel

from utils.textfield_colors import harden_mdtextfield_colors


@dataclass(frozen=True)
class MoleculeItem:
    key: str
    pdb_path: Path
    ru_name: str
    formula: str
    mass_g_mol: Optional[float]
    description: str = ""


_ATOMIC_WEIGHTS: Dict[str, float] = {
    "H": 1.008,
    "C": 12.011,
    "N": 14.007,
    "O": 15.999,
    "F": 18.998,
    "P": 30.974,
    "S": 32.06,
    "Cl": 35.45,
    "Na": 22.990,
    "K": 39.098,
}

# key -> (ru_name, description)
# Список отсортирован по русскому названию (алфавиту)
_MOLECULE_DATA: Dict[str, tuple] = {
    "adrenaline": (
        "Адреналин",
        "Гормон стресса, вырабатывается надпочечниками. Увеличивает частоту сердечных сокращений, расширяет зрачки, мобилизует энергетические резервы организма."
    ),
    "alanine": (
        "Аланин",
        "Заменимая аминокислота, входит в состав белков. Участвует в метаболизме глюкозы и является источником энергии для мышц."
    ),
    "ammonia": (
        "Аммиак",
        "Бесцветный газ с резким запахом. Хорошо растворим в воде, образует щелочной раствор. Используется для производства удобрений и азотной кислоты."
    ),
    "nitrogen": (
        "Азот",
        "Двухатомный газ, составляет 78% атмосферы Земли. Химически инертен из-за прочной тройной связи N≡N. Жидкий азот используется как хладагент (−196°C)."
    ),
    "nitric_acid": (
        "Азотная кислота",
        "Сильная минеральная кислота, бесцветная жидкость. Концентрированная кислота дымит на воздухе. Используется для производства удобрений и взрывчатых веществ."
    ),
    "anthracene": (
        "Антрацен",
        "Полициклический ароматический углеводород из трёх конденсированных бензольных колец. Флуоресцирует голубым светом. Используется в производстве красителей."
    ),
    "aspirin": (
        "Аспирин",
        "Ацетилсалициловая кислота — одно из самых известных лекарств. Обладает жаропонижающим, противовоспалительным и обезболивающим действием. Открыт в 1897 году."
    ),
    "acetylene": (
        "Ацетилен",
        "Простейший алкин с тройной связью C≡C. Бесцветный газ, горит ярким пламенем (до 3000°C). Используется для сварки и резки металлов."
    ),
    "acetone": (
        "Ацетон",
        "Простейший кетон, бесцветная летучая жидкость. Отличный растворитель для лаков, красок и смол. Образуется в организме при расщеплении жиров."
    ),
    "benzene": (
        "Бензол",
        "Ароматический углеводород, родоначальник класса аренов. Молекула имеет плоскую циклическую структуру с делокализованными π-электронами."
    ),
    "butane": (
        "Бутан",
        "Насыщенный углеводород, газ без цвета и запаха. Используется как топливо в зажигалках и газовых баллонах, а также как хладагент."
    ),
    "vitamin_c": (
        "Витамин C",
        "Аскорбиновая кислота — водорастворимый витамин, мощный антиоксидант. Необходим для синтеза коллагена. Содержится в цитрусовых, шиповнике, перце."
    ),
    "hydrogen": (
        "Водород",
        "Самый лёгкий элемент, двухатомный газ. Составляет 75% массы Вселенной. Перспективное экологически чистое топливо, горит с образованием воды."
    ),
    "water": (
        "Вода",
        "Универсальный растворитель, основа жизни на Земле. Аномально высокие температуры плавления и кипения обусловлены водородными связями между молекулами."
    ),
    "hexane": (
        "Гексан",
        "Алкан с шестью атомами углерода. Бесцветная жидкость, получаемая из нефти. Широко используется как неполярный растворитель в лабораториях."
    ),
    "naoh": (
        "Гидроксид натрия",
        "Едкий натр, сильное основание. Белое твёрдое вещество, хорошо растворимое в воде. Применяется в производстве мыла, бумаги и тканей."
    ),
    "glycerol": (
        "Глицерин",
        "Трёхатомный спирт, бесцветная вязкая жидкость. Входит в состав жиров. Применяется в косметике, медицине и производстве нитроглицерина."
    ),
    "glycine": (
        "Глицин",
        "Простейшая аминокислота, единственная не имеющая хирального центра. Является тормозным нейромедиатором в ЦНС. Входит в состав коллагена."
    ),
    "glucose": (
        "Глюкоза",
        "Моносахарид, главный источник энергии для клеток. Содержится во фруктах и мёде. Концентрация в крови регулируется инсулином."
    ),
    "dimethyl_ether": (
        "Диметиловый эфир",
        "Простейший эфир, газ со слабым запахом. Экологичная альтернатива дизельному топливу. Используется как пропеллент в аэрозолях и хладагент."
    ),
    "diethyl_ether": (
        "Диэтиловый эфир",
        "Летучая жидкость с характерным запахом. Первый ингаляционный анестетик в истории медицины (1842). Отличный растворитель для жиров и масел."
    ),
    "co2": (
        "Диоксид углерода",
        "Бесцветный газ, продукт дыхания и горения. Поглощается растениями в процессе фотосинтеза. Один из основных парниковых газов атмосферы."
    ),
    "dopamine": (
        "Дофамин",
        "Нейромедиатор «счастья и мотивации». Регулирует чувство удовольствия, обучение и движения. Недостаток связан с болезнью Паркинсона."
    ),
    "isopropanol": (
        "Изопропанол",
        "Вторичный спирт, бесцветная жидкость. Широко используется как антисептик (спиртовые салфетки), растворитель и компонент незамерзающих жидкостей."
    ),
    "caffeine": (
        "Кофеин",
        "Алкалоид из кофе, чая и какао. Стимулирует ЦНС, повышает бодрость, снимает усталость. Самый потребляемый психоактивный препарат в мире."
    ),
    "oxygen": (
        "Кислород",
        "Двухатомный газ, необходимый для дыхания. Составляет 21% атмосферы. Сильный окислитель, поддерживает горение. Образуется при фотосинтезе."
    ),
    "methane": (
        "Метан",
        "Простейший углеводород, главный компонент природного газа (до 98%). Парниковый газ, в 25 раз эффективнее CO₂. Образуется при разложении органики."
    ),
    "methylamine": (
        "Метиламин",
        "Простейший первичный амин, газ с запахом рыбы. Промежуточный продукт в синтезе пестицидов, лекарств и красителей."
    ),
    "urea": (
        "Мочевина",
        "Конечный продукт белкового обмена у млекопитающих. Первое органическое вещество, синтезированное из неорганического (Вёлер, 1828). Основное азотное удобрение."
    ),
    "formic_acid": (
        "Муравьиная кислота",
        "Простейшая карбоновая кислота. Содержится в яде муравьёв и крапивы. Используется в текстильной промышленности и как консервант."
    ),
    "naphthalene": (
        "Нафталин",
        "Полициклический ароматический углеводород из двух конденсированных бензольных колец. Характерный запах. Ранее использовался в средствах от моли."
    ),
    "nicotine": (
        "Никотин",
        "Алкалоид табака, сильный нейротоксин. Вызывает зависимость, стимулируя выброс дофамина. В малых дозах действует как стимулятор ЦНС."
    ),
    "ozone": (
        "Озон",
        "Аллотропная модификация кислорода (O₃). Озоновый слой защищает Землю от УФ-излучения. Сильный окислитель, используется для обеззараживания воды."
    ),
    "pentane": (
        "Пентан",
        "Алкан с пятью атомами углерода. Легко воспламеняющаяся жидкость. Используется как растворитель и в производстве пенополистирола."
    ),
    "hydrogen_peroxide": (
        "Перекись водорода",
        "Простейший пероксид (H₂O₂). Бесцветная жидкость, сильный окислитель. 3% раствор — антисептик, концентрированная — ракетное топливо."
    ),
    "pyrene": (
        "Пирен",
        "Полициклический ароматический углеводород из четырёх конденсированных колец. Сильно флуоресцирует. Образуется при неполном сгорании органических веществ."
    ),
    "propane": (
        "Пропан",
        "Насыщенный углеводород, бесцветный газ. Сжижается при небольшом давлении. Используется как бытовое топливо и автомобильный газ (LPG)."
    ),
    "serotonin": (
        "Серотонин",
        "Нейромедиатор «хорошего настроения». Регулирует сон, аппетит, эмоции. Недостаток связан с депрессией. Содержится в шоколаде и бананах."
    ),
    "hydrogen_sulfide": (
        "Сероводород",
        "Бесцветный газ с запахом тухлых яиц. Очень токсичен. Образуется при гниении белков. В малых концентрациях — сигнальная молекула в организме."
    ),
    "sulfur_dioxide": (
        "Диоксид серы",
        "Бесцветный газ с резким запахом. Образуется при сжигании серосодержащего топлива. Консервант (E220) в виноделии. Вызывает кислотные дожди."
    ),
    "sulfuric_acid": (
        "Серная кислота",
        "«Хлеб химии» — важнейшая минеральная кислота. Маслянистая жидкость, сильный дегидратант. Мировое производство превышает 200 млн тонн в год."
    ),
    "hydrogen_cyanide": (
        "Синильная кислота",
        "Цианистый водород — один из сильнейших ядов. Блокирует клеточное дыхание. Содержится в косточках абрикосов и горьком миндале."
    ),
    "toluene": (
        "Толуол",
        "Ароматический углеводород, бесцветная жидкость. Получают из нефти. Растворитель для красок и лаков, сырьё для синтеза тротила и бензойной кислоты."
    ),
    "carbon_monoxide": (
        "Угарный газ",
        "Монооксид углерода (CO) — ядовитый газ без цвета и запаха. Образуется при неполном сгорании. Связывается с гемоглобином в 200 раз прочнее кислорода."
    ),
    "acetic_acid": (
        "Уксусная кислота",
        "Органическая кислота с резким запахом. Основной компонент пищевого уксуса (3-9% раствор). Широко используется в химической промышленности."
    ),
    "phenol": (
        "Фенол",
        "Ароматический спирт, бесцветные кристаллы с характерным запахом. Антисептик, впервые применённый Листером. Сырьё для производства пластмасс и красителей."
    ),
    "formaldehyde": (
        "Формальдегид",
        "Простейший альдегид, газ с резким запахом. Водный раствор (формалин) — консервант для биологических препаратов. Используется в производстве пластмасс."
    ),
    "phosphine": (
        "Фосфин",
        "Гидрид фосфора (PH₃), бесцветный ядовитый газ с запахом чеснока. Самовоспламеняется на воздухе. Обнаружен в атмосфере Венеры (возможный признак жизни)."
    ),
    "chloroform": (
        "Хлороформ",
        "Трихлорметан (CHCl₃), бесцветная жидкость со сладким запахом. Исторический анестетик. Сейчас используется как растворитель и в органическом синтезе."
    ),
    "hcl": (
        "Хлороводород",
        "Бесцветный газ с резким запахом. Водный раствор — соляная кислота, важнейшая минеральная кислота. Содержится в желудочном соке человека."
    ),
    "nacl": (
        "Хлорид натрия",
        "Поваренная соль, ионное соединение с кубической кристаллической решёткой. Необходим для поддержания водно-солевого баланса организма."
    ),
    "cholesterol": (
        "Холестерин",
        "Органическое соединение из группы стеринов. Входит в состав клеточных мембран. Предшественник стероидных гормонов и витамина D."
    ),
    "cyclohexane": (
        "Циклогексан",
        "Циклический алкан, бесцветная жидкость. Молекула принимает форму «кресла». Растворитель и сырьё для производства нейлона."
    ),
    "ethane": (
        "Этан",
        "Насыщенный углеводород, бесцветный газ. Содержится в природном газе (до 10%). Используется для получения этилена методом крекинга."
    ),
    "ethylene": (
        "Этилен",
        "Простейший алкен с двойной связью C=C. Растительный гормон, ускоряющий созревание плодов. Важнейшее сырьё для производства полиэтилена."
    ),
    "ethanol": (
        "Этанол",
        "Одноатомный спирт, бесцветная жидкость с характерным запахом. Получают брожением сахаров. Применяется как растворитель, топливо и антисептик."
    ),
}

# для обратной совместимости
_NAME_MAP: Dict[str, str] = {k: v[0] for k, v in _MOLECULE_DATA.items()}

_ELEMENT_RE = re.compile(r"^[A-Z][a-z]?$")


def _extract_element_from_pdb_line(line: str) -> Optional[str]:
    if len(line) >= 78:
        el = line[76:78].strip()
        if el and _ELEMENT_RE.match(el):
            return el

    parts = line.split()
    if parts:
        last = parts[-1].strip()
        if _ELEMENT_RE.match(last):
            return last

    return None


def _counts_from_pdb(pdb_path: Path) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    with pdb_path.open("r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if not (line.startswith("ATOM") or line.startswith("HETATM")):
                continue
            el = _extract_element_from_pdb_line(line)
            if not el:
                continue
            counts[el] = counts.get(el, 0) + 1
    return counts


def _formula_hill(counts: Dict[str, int]) -> str:
    if not counts:
        return "N/A"

    def fmt(el: str, n: int) -> str:
        return f"{el}{n if n != 1 else ''}"

    has_c = "C" in counts
    parts: List[str] = []

    if has_c:
        parts.append(fmt("C", counts["C"]))
        if "H" in counts:
            parts.append(fmt("H", counts["H"]))
        for el in sorted([e for e in counts.keys() if e not in ("C", "H")]):
            parts.append(fmt(el, counts[el]))
    else:
        for el in sorted(counts.keys()):
            parts.append(fmt(el, counts[el]))

    return "".join(parts)


def _mass_from_counts(counts: Dict[str, int], pdb_name: str) -> Optional[float]:
    if not counts:
        return None
    mass = 0.0
    for el, n in counts.items():
        w = _ATOMIC_WEIGHTS.get(el)
        if w is None:
            Logger.warning(f"[Molecules] Unknown atomic weight for element: {el} in {pdb_name}")
            return None
        mass += w * n
    return round(mass, 2)


class MoleculeCard(MDCard):
    """
    Без ButtonBehavior/RectangularRippleBehavior (чтобы не ловить MRO).
    Акцент при тапе — меняем фон вручную.
    Рамка — через canvas.after (стабильно на всех версиях).
    """

    def __init__(self, on_open=None, border_rgba=(1, 1, 1, 0.16), pressed_delta=0.08, **kwargs):
        super().__init__(**kwargs)
        self._on_open = on_open

        self._normal_bg = list(getattr(self, "md_bg_color", (0.10, 0.11, 0.14, 1)))
        self._pressed_bg = self._make_pressed(self._normal_bg, pressed_delta)

        # рамка
        self._border_rgba = border_rgba
        with self.canvas.after:
            self._border_color = Color(*self._border_rgba)
            self._border_line = Line(rounded_rectangle=[self.x, self.y, self.width, self.height, 18], width=1)

        self.bind(pos=self._update_border, size=self._update_border)

    @staticmethod
    def _make_pressed(rgba, delta: float):
        r, g, b, a = rgba
        return [min(1.0, r + delta), min(1.0, g + delta), min(1.0, b + delta), a]

    def _update_border(self, *_):
        # radius должен совпадать с card.radius
        rad = 18
        self._border_line.rounded_rectangle = [self.x, self.y, self.width, self.height, rad]

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.md_bg_color = self._pressed_bg
            return True
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        was_inside = self.collide_point(*touch.pos)
        self.md_bg_color = self._normal_bg
        if was_inside and self._on_open:
            try:
                self._on_open()
            except Exception as e:
                Logger.exception(f"[MoleculeCard] open failed: {e}")
            return True
        return super().on_touch_up(touch)


class MoleculesScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._all: List[MoleculeItem] = []
        self._filtered: List[MoleculeItem] = []
        self._loaded = False

    @property
    def app(self):
        from kivy.app import App
        return App.get_running_app()

    def on_pre_enter(self, *args):
        if not self._loaded:
            Clock.schedule_once(lambda *_: self._load_and_render(), 0)

        # KivyMD 2.x: иногда текст в MDTextField становится тёмным
        # фикс для Desktop/Android
        Clock.schedule_once(lambda *_: self._harden_search_field_colors(), 0)

    def _harden_search_field_colors(self) -> None:
        sf = self.ids.get("search_field")
        if not sf:
            return
        app = self.app
        harden_mdtextfield_colors(
            sf,
            text_rgba=tuple(getattr(app, "mm_text", (1, 1, 1, 1))),
            cursor_rgba=tuple(getattr(app, "mm_text", (1, 1, 1, 1))),
            selection_text_rgba=(1, 1, 1, 1),
        )

    def on_search(self, text: str) -> None:
        q = (text or "").strip().lower()
        if not self._all:
            return

        if not q:
            self._filtered = list(self._all)
        else:

            def hit(m: MoleculeItem) -> bool:
                return q in m.ru_name.lower() or q in m.formula.lower() or q in m.key.lower()

            self._filtered = [m for m in self._all if hit(m)]

        self._render_list()

    def _assets_dir(self) -> Path:
        project_root = Path(__file__).resolve().parents[1]
        return project_root / "assets" / "molecules"

    def _load_and_render(self) -> None:
        self._loaded = True

        assets = self._assets_dir()
        if not assets.exists():
            Logger.error(f"[Molecules] assets dir not found: {assets}")
            self._all = []
            self._filtered = []
            self._render_list()
            return

        pdb_files = sorted(assets.glob("*.pdb"))
        items: List[MoleculeItem] = []

        for pdb in pdb_files:
            key = pdb.stem
            mol_data = _MOLECULE_DATA.get(key)
            if mol_data:
                ru = mol_data[0]
                description = mol_data[1]
            else:
                ru = key.replace("_", " ").strip().capitalize()
                description = ""

            try:
                counts = _counts_from_pdb(pdb)
                formula = _formula_hill(counts)
                mass = _mass_from_counts(counts, pdb.name)
            except Exception as e:
                Logger.exception(f"[Molecules] Failed to parse {pdb}: {e}")
                formula = "N/A"
                mass = None

            items.append(
                MoleculeItem(
                    key=key,
                    pdb_path=pdb,
                    ru_name=ru,
                    formula=formula,
                    mass_g_mol=mass,
                    description=description,
                )
            )

        items.sort(key=lambda m: m.ru_name.lower())
        self._all = items
        self._filtered = list(items)
        self._render_list()

    def _render_list(self) -> None:
        lst = self.ids.get("molecules_list")
        if not lst:
            Logger.warning("[Molecules] KV ids not ready: molecules_list missing")
            return

        lst.clear_widgets()

        app = self.app

        # делаем "воздух" между карточками
        if hasattr(lst, "spacing"):
            lst.spacing = dp(app.mm_molecules_list_spacing)
        if hasattr(lst, "padding"):
            lst.padding = (0, 0, 0, dp(app.mm_molecules_list_bottom_padding))

        # фон карточек берём только отсюда (стабильно тёмный)
        card_bg = getattr(app, "mm_molecules_card_bg", (0.10, 0.11, 0.14, 1))
        border = getattr(app, "mm_molecules_card_border", (1, 1, 1, 0.16))
        pressed_delta = float(getattr(app, "mm_molecules_card_pressed_delta", 0.08))

        text1 = getattr(app, "mm_text", (1, 1, 1, 1))
        text2 = getattr(app, "mm_text2", (0.75, 0.78, 0.85, 1))

        title_fs = dp(18)
        sub_fs = dp(14)

        for m in self._filtered:
            title_line = f"{m.ru_name} ({m.formula})"

            def _open(m_item=m, ttl=title_line):
                self.app.open_molecule_viewer(str(m_item.pdb_path), ttl, m_item.description)

            card = MoleculeCard(
                on_open=_open,
                md_bg_color=list(card_bg),
                theme_bg_color="Custom",
                border_rgba=border,
                pressed_delta=pressed_delta,
                elevation=int(getattr(app, "mm_molecules_card_elevation", 1)),
                radius=[18, 18, 18, 18],
                padding=(dp(16), dp(12), dp(16), dp(12)),
                size_hint_x=1,
                size_hint_y=None,
                height=dp(72),
            )

            box = BoxLayout(orientation="vertical", spacing=dp(4))

            title = MDLabel(
                text=title_line,
                bold=True,
                theme_text_color="Custom",
                text_color=text1,
                font_size=title_fs,
                halign="left",
                valign="middle",
                size_hint_y=None,
                height=dp(24),
            )

            mass_txt = (
                "Молекулярная масса: N/A"
                if m.mass_g_mol is None
                else f"M = {m.mass_g_mol:.2f} г/моль"
            )
            mass = MDLabel(
                text=mass_txt,
                theme_text_color="Custom",
                text_color=text2,
                font_size=sub_fs,
                halign="left",
                valign="middle",
                size_hint_y=None,
                height=dp(20),
            )

            box.add_widget(title)
            box.add_widget(mass)
            card.add_widget(box)
            lst.add_widget(card)
