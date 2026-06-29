#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Olho de Deus V2 — Versão Mobile (Android/iOS)
Criado por Martins Store
Discord: https://discord.com/invite/ksRpjyrKU6

Dependências (instale via pip ou buildozer):
  pip install kivy kivymd requests

Para compilar .apk use buildozer:
  buildozer android debug
"""

# ─────────────────────────────────────────────────────────────────────────────
#  IMPORTS
# ─────────────────────────────────────────────────────────────────────────────
import os
import sys
import json
import re
import threading
import hashlib
import uuid
from datetime import datetime
from pathlib import Path

import requests

from kivy.app import App
from kivy.clock import Clock, mainthread
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.utils import platform
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton, MDFlatButton, MDIconButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.card import MDCard
from kivymd.uix.list import MDList, TwoLineIconListItem, IconLeftWidget
from kivymd.uix.dialog import MDDialog
from kivymd.uix.progressindicator import MDCircularProgressIndicator
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.snackbar import MDSnackbar
from kivymd.uix.selectioncontrol import MDCheckbox
from kivymd.uix.chip import MDChip

# ─────────────────────────────────────────────────────────────────────────────
#  CONFIGURAÇÕES DO BOT (NÃO ALTERAR)
# ─────────────────────────────────────────────────────────────────────────────
BOT_VERIFY_URL = "https://msbot.squareweb.app/api/olhodeus/verify"
BOT_DB_URL     = "https://msbot.squareweb.app/api/olhodeus/db"

DB_NOMES = {
    1: "DB Gov",
    2: "DB Gov / Sites em Geral",
    3: "DB Gov V2",
}

# ─────────────────────────────────────────────────────────────────────────────
#  TEMA — roxo/violeta igual ao terminal
# ─────────────────────────────────────────────────────────────────────────────
PALETA_PRIMARIA  = "DeepPurple"
PALETA_ACENTO    = "Purple"
FUNDO_ESCURO     = [0.06, 0.04, 0.09, 1]   # quase preto-roxo
CARD_COR         = [0.11, 0.08, 0.16, 1]
ROXO_HEX         = "#7B2FBE"
VERDE_HEX        = "#22c55e"
AMARELO_HEX      = "#facc15"
VERMELHO_HEX     = "#ef4444"
CINZA_HEX        = "#9ca3af"

# ─────────────────────────────────────────────────────────────────────────────
#  HARDWARE ID (adaptado para mobile)
# ─────────────────────────────────────────────────────────────────────────────

def _hardware_id() -> str:
    """Gera HWID único para o dispositivo (Android/iOS/Desktop)."""
    if platform == "android":
        try:
            from jnius import autoclass
            Settings = autoclass("android.provider.Settings$Secure")
            context  = autoclass("org.kivy.android.PythonActivity").mActivity
            android_id = Settings.getString(context.getContentResolver(),
                                            Settings.ANDROID_ID)
            raw = f"android-{android_id}"
            return hashlib.sha256(raw.encode()).hexdigest()[:16].upper()
        except Exception:
            pass

    if platform == "ios":
        try:
            from pyobjus import autoclass
            UIDevice = autoclass("UIDevice")
            raw = str(UIDevice.currentDevice().identifierForVendor)
            return hashlib.sha256(raw.encode()).hexdigest()[:16].upper()
        except Exception:
            pass

    # Fallback: UUID persistido em arquivo local
    id_file = Path(_cache_dir()) / "device_id.txt"
    try:
        if id_file.exists():
            return id_file.read_text().strip()
        new_id = hashlib.sha256(str(uuid.uuid4()).encode()).hexdigest()[:16].upper()
        id_file.parent.mkdir(parents=True, exist_ok=True)
        id_file.write_text(new_id)
        return new_id
    except Exception:
        return hashlib.sha256(str(uuid.getnode()).encode()).hexdigest()[:16].upper()


def _formatar_hwid(raw: str) -> str:
    raw = raw.upper().replace("-", "").replace(" ", "")
    return "-".join(raw[i:i+4] for i in range(0, min(len(raw), 16), 4))


def _cache_dir() -> str:
    if platform == "android":
        try:
            from jnius import autoclass
            ctx = autoclass("org.kivy.android.PythonActivity").mActivity
            return str(ctx.getFilesDir().getAbsolutePath())
        except Exception:
            pass
    return str(Path.home() / ".olhodeus")


def _cache_file() -> Path:
    return Path(_cache_dir()) / "license.dat"


def _salvar_cache(hwid: str):
    p = _cache_file()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"hwid": hwid, "verified_at": __import__("time").time()}))


def _cache_valido() -> bool:
    import time
    try:
        p = _cache_file()
        if not p.exists():
            return False
        d = json.loads(p.read_text())
        if d.get("hwid") != _hardware_id():
            return False
        return (time.time() - d.get("verified_at", 0)) < 86400
    except Exception:
        return False


# ─────────────────────────────────────────────────────────────────────────────
#  API — verificação e download de DB
# ─────────────────────────────────────────────────────────────────────────────

def api_verificar(hwid: str) -> dict:
    try:
        r = requests.post(BOT_VERIFY_URL,
                          json={"hwid": hwid},
                          headers={"Content-Type": "application/json"},
                          timeout=10)
        return r.json()
    except Exception as ex:
        return {"authorized": False, "reason": f"Sem conexão: {ex}"}


def api_baixar_db(num: int, hwid: str) -> list[str] | None:
    try:
        r = requests.get(f"{BOT_DB_URL}/{num}",
                         headers={"X-HWID": hwid, "User-Agent": "OlhoDeusMobile/2.0"},
                         timeout=30)
        if r.status_code == 403:
            return None
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return [l.strip() for l in r.text.split("\n") if l.strip()]
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────────────────────
#  BUSCA INTELIGENTE
# ─────────────────────────────────────────────────────────────────────────────

def _extrair_campos(linha: str):
    linha = linha.strip()
    if not linha:
        return None
    for sep in [":", "|", ";"]:
        partes = linha.split(sep)
        if len(partes) >= 3:
            for i, p in enumerate(partes):
                p_low = p.lower()
                if (p_low.startswith("http://") or p_low.startswith("https://")
                        or ("." in p and "/" in p and len(p) > 6)):
                    restantes = partes[:i] + partes[i+1:]
                    login = restantes[0] if len(restantes) > 0 else ""
                    senha = sep.join(restantes[1:]) if len(restantes) > 1 else ""
                    return (p.strip(), login.strip(), senha.strip())
            url   = sep.join(partes[:-2]).strip() if len(partes) > 3 else partes[0].strip()
            login = partes[-2].strip()
            senha = partes[-1].strip()
            return (url, login, senha)
        elif len(partes) == 2:
            return (linha, partes[0].strip(), partes[1].strip())
    return (linha, "", "")


def _url_match(url_linha: str, url_busca: str) -> bool:
    def sem_proto(u):
        return re.sub(r"^https?://", "", u.lower().strip().rstrip("/"))
    base_l = sem_proto(url_linha)
    base_b = sem_proto(url_busca)
    return (base_b in base_l or base_l in base_b
            or base_l.startswith(base_b) or base_b.startswith(base_l))


def buscar_na_db(linhas: list[str], url_busca: str) -> list[dict]:
    resultados = []
    for linha in linhas:
        campos = _extrair_campos(linha)
        if campos is None:
            continue
        url_linha, login, senha = campos
        if _url_match(url_linha, url_busca):
            resultados.append({"url": url_linha, "login": login, "senha": senha, "raw": linha})
    return resultados


# ─────────────────────────────────────────────────────────────────────────────
#  HELPERS UI
# ─────────────────────────────────────────────────────────────────────────────

def snack(msg: str, cor: str = ROXO_HEX):
    MDSnackbar(
        MDLabel(text=msg, theme_text_color="Custom", text_color="white"),
        bg_color=cor,
        duration=3,
    ).open()


def spinner_box() -> MDBoxLayout:
    box = MDBoxLayout(orientation="vertical", adaptive_height=True,
                      padding=dp(20), spacing=dp(10))
    sp  = MDCircularProgressIndicator(size_hint=(None, None),
                                      size=(dp(48), dp(48)),
                                      pos_hint={"center_x": .5})
    box.add_widget(sp)
    return box


# ─────────────────────────────────────────────────────────────────────────────
#  TELA: SPLASH / VERIFICAÇÃO DE LICENÇA
# ─────────────────────────────────────────────────────────────────────────────

class TelaLicenca(MDScreen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.name = "licenca"
        self._hwid = _hardware_id()
        self._build()

    def _build(self):
        root = MDBoxLayout(orientation="vertical", md_bg_color=FUNDO_ESCURO,
                           padding=dp(24), spacing=dp(16))

        root.add_widget(MDLabel(
            text="◉  OLHO DE DEUS V2",
            halign="center",
            theme_text_color="Custom",
            text_color=ROXO_HEX,
            font_style="H5",
            bold=True,
        ))
        root.add_widget(MDLabel(
            text="SISTEMA DE BUSCA EM BASE DE DADOS",
            halign="center",
            theme_text_color="Custom",
            text_color="#a78bfa",
            font_style="Subtitle2",
        ))

        olho = MDLabel(
            text="👁",
            halign="center",
            font_size=dp(72),
            size_hint_y=None,
            height=dp(100),
        )
        root.add_widget(olho)

        self._status_lbl = MDLabel(
            text="Verificando licença...",
            halign="center",
            theme_text_color="Custom",
            text_color=CINZA_HEX,
            font_style="Body1",
        )
        root.add_widget(self._status_lbl)

        self._spinner = MDCircularProgressIndicator(
            size_hint=(None, None),
            size=(dp(40), dp(40)),
            pos_hint={"center_x": .5},
        )
        root.add_widget(self._spinner)

        # HWID display (visível se não autorizado)
        self._hwid_card = MDCard(
            orientation="vertical",
            padding=dp(16),
            spacing=dp(8),
            md_bg_color=CARD_COR,
            radius=[dp(12)],
            size_hint_y=None,
            height=dp(120),
        )
        self._hwid_card.add_widget(MDLabel(
            text="ID do seu Dispositivo:",
            theme_text_color="Custom",
            text_color=CINZA_HEX,
            font_style="Caption",
            halign="center",
        ))
        self._hwid_val = MDLabel(
            text=_formatar_hwid(self._hwid),
            theme_text_color="Custom",
            text_color="white",
            font_style="H6",
            bold=True,
            halign="center",
        )
        self._hwid_card.add_widget(self._hwid_val)
        self._hwid_card.add_widget(MDLabel(
            text="Copie e envie no canal de ativação do Discord",
            theme_text_color="Custom",
            text_color=CINZA_HEX,
            font_style="Caption",
            halign="center",
        ))
        self._hwid_card.opacity = 0

        root.add_widget(self._hwid_card)

        self._discord_btn = MDRaisedButton(
            text="Ativar no Discord",
            md_bg_color=ROXO_HEX,
            pos_hint={"center_x": .5},
            opacity=0,
            disabled=True,
        )
        root.add_widget(self._discord_btn)

        self._retry_btn = MDFlatButton(
            text="Tentar novamente",
            theme_text_color="Custom",
            text_color=ROXO_HEX,
            pos_hint={"center_x": .5},
            opacity=0,
            disabled=True,
        )
        self._retry_btn.bind(on_release=lambda *a: self._verificar())
        root.add_widget(self._retry_btn)

        root.add_widget(MDLabel(
            text="discord.com/invite/ksRpjyrKU6",
            halign="center",
            theme_text_color="Custom",
            text_color=CINZA_HEX,
            font_style="Caption",
        ))

        self.add_widget(root)

    def on_enter(self, *args):
        threading.Thread(target=self._verificar_thread, daemon=True).start()

    def _verificar(self, *args):
        self._set_spinner(True)
        self._status("Verificando licença...")
        threading.Thread(target=self._verificar_thread, daemon=True).start()

    def _verificar_thread(self):
        import time
        hwid = self._hwid

        if _cache_valido():
            time.sleep(0.5)
            self._ir_menu()
            return

        resultado = api_verificar(hwid)

        if resultado.get("authorized"):
            _salvar_cache(hwid)
            username = resultado.get("username", "")
            self._status_ok(f"✔ Licença válida! Bem-vindo, {username or 'usuário'}!")
            time.sleep(1.5)
            self._ir_menu()
        else:
            motivo = resultado.get("reason", "Não autorizado.")
            # Tenta cache offline se sem conexão
            if "Sem conexão" in motivo:
                cache = _cache_file()
                if cache.exists():
                    try:
                        d = json.loads(cache.read_text())
                        if d.get("hwid") == hwid:
                            self._status_warn("⚠ Sem conexão. Usando cache offline.")
                            time.sleep(2)
                            self._ir_menu()
                            return
                    except Exception:
                        pass
            self._status_err(f"✘ {motivo}")
            self._mostrar_ativacao()

    @mainthread
    def _status(self, msg, cor=None):
        self._status_lbl.text = msg
        self._status_lbl.text_color = cor or CINZA_HEX

    @mainthread
    def _status_ok(self, msg):
        self._status_lbl.text = msg
        self._status_lbl.text_color = VERDE_HEX
        self._spinner.opacity = 0

    @mainthread
    def _status_warn(self, msg):
        self._status_lbl.text = msg
        self._status_lbl.text_color = AMARELO_HEX
        self._spinner.opacity = 0

    @mainthread
    def _status_err(self, msg):
        self._status_lbl.text = msg
        self._status_lbl.text_color = VERMELHO_HEX
        self._spinner.opacity = 0

    @mainthread
    def _set_spinner(self, vis: bool):
        self._spinner.opacity = 1 if vis else 0

    @mainthread
    def _mostrar_ativacao(self):
        self._hwid_card.opacity = 1
        self._discord_btn.opacity = 1
        self._discord_btn.disabled = False
        self._retry_btn.opacity = 1
        self._retry_btn.disabled = False

    @mainthread
    def _ir_menu(self):
        self.manager.transition = SlideTransition(direction="left")
        self.manager.current = "menu"


# ─────────────────────────────────────────────────────────────────────────────
#  TELA: MENU PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────

class TelaMenu(MDScreen):
    def __init__(self, app_ref, **kw):
        super().__init__(**kw)
        self.name    = "menu"
        self.app_ref = app_ref
        self._build()

    def _build(self):
        root = MDBoxLayout(orientation="vertical", md_bg_color=FUNDO_ESCURO)

        toolbar = MDTopAppBar(
            title="Olho de Deus V2",
            md_bg_color=ROXO_HEX,
            specific_text_color="white",
        )
        root.add_widget(toolbar)

        scroll = MDScrollView()
        content = MDBoxLayout(orientation="vertical", padding=dp(16),
                              spacing=dp(12), adaptive_height=True)

        content.add_widget(MDLabel(
            text="◉  Selecione a Base de Dados",
            theme_text_color="Custom",
            text_color="#a78bfa",
            font_style="H6",
            bold=True,
            size_hint_y=None,
            height=dp(40),
        ))

        for num, nome in DB_NOMES.items():
            card = MDCard(
                orientation="vertical",
                padding=dp(20),
                spacing=dp(8),
                md_bg_color=CARD_COR,
                radius=[dp(14)],
                size_hint_y=None,
                height=dp(90),
                ripple_behavior=True,
            )
            lbl_num = MDLabel(
                text=f"  [{num}]  {nome}",
                theme_text_color="Custom",
                text_color="white",
                font_style="H6",
                bold=True,
            )
            lbl_sub = MDLabel(
                text="  Toque para acessar e buscar credenciais",
                theme_text_color="Custom",
                text_color=CINZA_HEX,
                font_style="Caption",
            )
            card.add_widget(lbl_num)
            card.add_widget(lbl_sub)

            db_num = num
            card.bind(on_release=lambda *a, n=db_num: self._abrir_busca(n))
            content.add_widget(card)

        content.add_widget(MDLabel(
            text="",
            size_hint_y=None,
            height=dp(8),
        ))

        discord_card = MDCard(
            orientation="vertical",
            padding=dp(16),
            md_bg_color=[0.08, 0.10, 0.20, 1],
            radius=[dp(14)],
            size_hint_y=None,
            height=dp(80),
        )
        discord_card.add_widget(MDLabel(
            text="🎮  Discord — Martins Store",
            theme_text_color="Custom",
            text_color="#7289da",
            font_style="Subtitle1",
            bold=True,
        ))
        discord_card.add_widget(MDLabel(
            text="  discord.com/invite/ksRpjyrKU6",
            theme_text_color="Custom",
            text_color=CINZA_HEX,
            font_style="Caption",
        ))
        content.add_widget(discord_card)

        scroll.add_widget(content)
        root.add_widget(scroll)
        self.add_widget(root)

    def _abrir_busca(self, num_db: int):
        tela = self.manager.get_screen("busca")
        tela.preparar(num_db, self.app_ref.hwid)
        self.manager.transition = SlideTransition(direction="left")
        self.manager.current = "busca"


# ─────────────────────────────────────────────────────────────────────────────
#  TELA: BUSCA NA DB
# ─────────────────────────────────────────────────────────────────────────────

class TelaBusca(MDScreen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.name    = "busca"
        self._linhas = []
        self._hwid   = ""
        self._num_db = 1
        self._carregando = False
        self._build()

    def _build(self):
        self._root = MDBoxLayout(orientation="vertical", md_bg_color=FUNDO_ESCURO)

        self._toolbar = MDTopAppBar(
            title="Carregando DB...",
            md_bg_color=ROXO_HEX,
            specific_text_color="white",
            left_action_items=[["arrow-left", lambda *a: self._voltar()]],
        )
        self._root.add_widget(self._toolbar)

        # Status / loading
        self._status_box = MDBoxLayout(orientation="vertical", padding=dp(20),
                                       spacing=dp(10), adaptive_height=True)
        self._status_lbl = MDLabel(
            text="Baixando base de dados...",
            halign="center",
            theme_text_color="Custom",
            text_color=CINZA_HEX,
            font_style="Body1",
        )
        self._spinner = MDCircularProgressIndicator(
            size_hint=(None, None),
            size=(dp(40), dp(40)),
            pos_hint={"center_x": .5},
        )
        self._status_box.add_widget(self._spinner)
        self._status_box.add_widget(self._status_lbl)
        self._root.add_widget(self._status_box)

        # Área de busca (oculta até DB carregar)
        self._busca_box = MDBoxLayout(orientation="vertical", padding=dp(16),
                                      spacing=dp(12))
        self._busca_box.opacity = 0
        self._busca_box.disabled = True

        self._db_info = MDLabel(
            text="",
            theme_text_color="Custom",
            text_color=VERDE_HEX,
            font_style="Caption",
            size_hint_y=None,
            height=dp(24),
        )
        self._busca_box.add_widget(self._db_info)

        self._campo_url = MDTextField(
            hint_text="URL para buscar (ex: site.com.br)",
            helper_text="Digite o domínio ou URL completa",
            helper_text_mode="on_focus",
            mode="rectangle",
            fill_color_normal=CARD_COR,
            text_color_normal="white",
            hint_text_color_normal=CINZA_HEX,
        )
        self._busca_box.add_widget(self._campo_url)

        self._btn_buscar = MDRaisedButton(
            text="🔍  BUSCAR",
            md_bg_color=ROXO_HEX,
            size_hint_x=1,
        )
        self._btn_buscar.bind(on_release=lambda *a: self._fazer_busca())
        self._busca_box.add_widget(self._btn_buscar)

        # Resultados
        scroll = MDScrollView()
        self._lista = MDList(spacing=dp(4))
        scroll.add_widget(self._lista)
        self._busca_box.add_widget(scroll)

        self._root.add_widget(self._busca_box)
        self.add_widget(self._root)

    def preparar(self, num_db: int, hwid: str):
        self._num_db = num_db
        self._hwid   = hwid
        self._linhas = []
        self._campo_url.text = ""
        self._lista.clear_widgets()
        self._toolbar.title = DB_NOMES[num_db]
        self._mostrar_loading(True)
        threading.Thread(target=self._carregar_db, daemon=True).start()

    def _carregar_db(self):
        linhas = api_baixar_db(self._num_db, self._hwid)
        if linhas is None:
            self._set_status_err("Erro ao carregar DB. Verifique licença.")
            return
        self._linhas = linhas
        self._db_pronta(len(linhas))

    @mainthread
    def _mostrar_loading(self, vis: bool):
        self._status_box.opacity  = 1 if vis else 0
        self._status_box.disabled = not vis
        self._busca_box.opacity   = 0 if vis else 1
        self._busca_box.disabled  = vis

    @mainthread
    def _set_status_err(self, msg: str):
        self._status_lbl.text       = msg
        self._status_lbl.text_color = VERMELHO_HEX
        self._spinner.opacity       = 0

    @mainthread
    def _db_pronta(self, total: int):
        self._db_info.text = f"✔  {total:,} registros carregados — {DB_NOMES[self._num_db]}"
        self._mostrar_loading(False)

    def _fazer_busca(self):
        url_busca = self._campo_url.text.strip()
        if not url_busca:
            snack("Digite uma URL para buscar.", VERMELHO_HEX)
            return
        if not self._linhas:
            snack("Base de dados não carregada.", VERMELHO_HEX)
            return

        self._lista.clear_widgets()
        self._btn_buscar.disabled = True
        threading.Thread(target=self._buscar_thread, args=(url_busca,), daemon=True).start()

    def _buscar_thread(self, url_busca: str):
        resultados = buscar_na_db(self._linhas, url_busca)
        self._mostrar_resultados(url_busca, resultados)

    @mainthread
    def _mostrar_resultados(self, url_busca: str, resultados: list):
        self._btn_buscar.disabled = False
        self._lista.clear_widgets()

        if not resultados:
            item = TwoLineIconListItem(
                text="Nenhum resultado encontrado",
                secondary_text=f"'{url_busca}' não está na base. Tente um domínio mais genérico.",
                theme_text_color="Custom",
                text_color=VERMELHO_HEX,
            )
            ico = IconLeftWidget(icon="close-circle", theme_icon_color="Custom",
                                 icon_color=VERMELHO_HEX)
            item.add_widget(ico)
            self._lista.add_widget(item)
            return

        # Header de resultado
        header = MDLabel(
            text=f"  ✔  {len(resultados):,} resultado(s) para '{url_busca}'",
            theme_text_color="Custom",
            text_color=VERDE_HEX,
            font_style="Subtitle2",
            bold=True,
            size_hint_y=None,
            height=dp(32),
        )
        self._lista.add_widget(header)

        for r in resultados:
            card = MDCard(
                orientation="vertical",
                padding=dp(14),
                spacing=dp(6),
                md_bg_color=CARD_COR,
                radius=[dp(10)],
                size_hint_y=None,
                height=dp(110),
            )
            card.add_widget(MDLabel(
                text=f"🔗  {r['url']}",
                theme_text_color="Custom",
                text_color="#a78bfa",
                font_style="Caption",
                bold=True,
            ))
            card.add_widget(MDLabel(
                text=f"👤  Login: {r['login']}",
                theme_text_color="Custom",
                text_color="white",
                font_style="Body2",
            ))
            card.add_widget(MDLabel(
                text=f"🔑  Senha: {r['senha']}",
                theme_text_color="Custom",
                text_color=AMARELO_HEX,
                font_style="Body2",
            ))

            # Botão copiar
            btn_copiar = MDFlatButton(
                text="Copiar",
                theme_text_color="Custom",
                text_color=ROXO_HEX,
                size_hint=(None, None),
                size=(dp(80), dp(32)),
            )
            raw_text = r["raw"]
            btn_copiar.bind(on_release=lambda *a, t=raw_text: self._copiar(t))
            card.add_widget(btn_copiar)
            self._lista.add_widget(card)

    def _copiar(self, texto: str):
        try:
            from kivy.core.clipboard import Clipboard
            Clipboard.copy(texto)
            snack("Copiado!", VERDE_HEX)
        except Exception:
            snack("Não foi possível copiar.", VERMELHO_HEX)

    def _voltar(self):
        self.manager.transition = SlideTransition(direction="right")
        self.manager.current = "menu"


# ─────────────────────────────────────────────────────────────────────────────
#  APP PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────

class OlhoDeusMobile(MDApp):
    hwid: str = ""

    def build(self):
        self.theme_cls.theme_style           = "Dark"
        self.theme_cls.primary_palette       = PALETA_PRIMARIA
        self.theme_cls.accent_palette        = PALETA_ACENTO
        self.theme_cls.primary_hue           = "700"
        self.theme_cls.accent_hue            = "200"
        self.title = "Olho de Deus V2"

        self.hwid = _hardware_id()

        sm = ScreenManager()
        sm.add_widget(TelaLicenca())
        sm.add_widget(TelaMenu(app_ref=self))
        sm.add_widget(TelaBusca())
        sm.current = "licenca"
        return sm


# ─────────────────────────────────────────────────────────────────────────────
#  BUILDOZER — instruções mínimas (crie buildozer.spec para compilar .apk)
# ─────────────────────────────────────────────────────────────────────────────
BUILDOZER_SPEC_EXEMPLO = """
# ── Cole isso em buildozer.spec ───────────────────────────────────────────────
[app]
title = Olho de Deus V2
package.name = olhodeus
package.domain = org.martinsstore
source.dir = .
source.include_exts = py,kv,png,jpg,ttf
version = 2.0
requirements = python3,kivy==2.3.0,kivymd==1.2.0,requests,pillow,jnius
android.permissions = INTERNET
android.api = 34
android.minapi = 21
android.archs = arm64-v8a, armeabi-v7a
orientation = portrait
fullscreen = 0

[buildozer]
log_level = 2
warn_on_root = 1
"""

if __name__ == "__main__":
    OlhoDeusMobile().run()
