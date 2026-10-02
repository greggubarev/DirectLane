import ctypes
import ipaddress
import json
import os
from pathlib import Path
import queue
import re
import socket
import subprocess
import sys
import tempfile
import threading
import tkinter as tk
from tkinter import messagebox, ttk
from urllib.parse import urlsplit


APP_DIR = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
DATA_DIR = Path(os.environ.get("LOCALAPPDATA", APP_DIR)) / "DirectLane"
STATE_PATH = DATA_DIR / "domains.json"
BRIDGE = Path(getattr(sys, "_MEIPASS", APP_DIR)) / "routes.ps1"
CATALOG_PATH = Path(getattr(sys, "_MEIPASS", APP_DIR)) / "catalog.json"
METRIC = 42
LANG = "en"
RU = {
    "Enter a website address.": "Введите адрес сайта.",
    "Enter a domain such as example.com or https://example.com/.": "Нужен адрес вида example.ru или https://example.ru/.",
    "Enter a domain without a login or port number.": "Укажите домен без логина и номера порта.",
    "Invalid domain name.": "Некорректное имя домена.",
    "DNS returned no IPv4 address for {host}.": "DNS не вернул IPv4-адрес для {host}.",
    "No public IPv4 address for {host}.": "Для {host} нет публичных IPv4-адресов.",
    "Could not change the route.": "Не удалось изменить маршрут.",
    "domains.json has an unknown format.": "Файл domains.json имеет неизвестный формат.",
    "A competing route exists for one of these IPs. Nothing changed.": "Есть конкурирующий маршрут к одному из адресов. Правила не изменены.",
    "{domain}: {count} IPs found; {added} routes added.": "{domain}: найдено {count} IP; новых маршрутов: {added}.",
    "The domain is no longer in the list.": "Домен уже удалён из списка.",
    "{domain} removed. Unused routes removed.": "{domain} удалён. Неиспользуемые маршруты удалены.",
    "Previous routes removed.": "Прежние правила удалены.",
    "Removal did not finish.": "Удаление не завершилось.",
    "Domains outside VPN": "Домены без VPN",
    "Enter a website. Its IPs will use your regular connection.": "Введите адрес сайта. Его IP будут открываться через обычный интернет.",
    "Add": "Добавить",
    "My domains": "Мои домены",
    "Popular sites": "Частые сайты",
    "Existing routes": "Другие маршруты",
    "Domain / addresses": "Домен / адреса",
    "Status": "Состояние",
    "Refresh selected IPs": "Обновить IP выбранного",
    "Remove selected": "Удалить выбранный",
    "Refresh view": "Обновить экран",
    "Choose a site and press Add. DNS addresses are checked when you add it.": "Выберите сайт и нажмите «Добавить». IP проверяются при добавлении.",
    "Site": "Сайт",
    "Domain": "Домен",
    "+ Add selected site": "+ Добавить выбранный сайт",
    "These routes were created outside DirectLane and are shown for reference.": "Эти маршруты добавлены вне DirectLane и показаны для справки.",
    "Network": "Сеть",
    "Gateway": "Шлюз",
    "Loading...": "Загрузка...",
    "Checking addresses and routes...": "Проверяю адреса и маршруты...",
    "Error: {error}": "Ошибка: {error}",
    "Could not complete the action": "Не удалось выполнить действие",
    "Bypass active": "В обход VPN",
    "Check: {good}/{total} IPs": "Проверить: {good}/{total} IP",
    "Regular connection: {name} · {gateway}": "Обычный интернет: {name} · {gateway}",
    "IPs can change. If the website stops working, select Refresh selected IPs.": "IP могут меняться. Если сайт перестал работать, нажмите «Обновить IP выбранного».",
    "Select a domain to see its addresses.": "Выберите домен, чтобы увидеть его адреса.",
    "Website address": "Адрес сайта",
    "Could not open the app": "Не удалось открыть программу",
}


def tr(message, **kwargs):
    return (RU.get(message, message) if LANG == "ru" else message).format(**kwargs)


def load_catalog():
    entries = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    return {item["domain"]: item for item in entries}


def normalize_domain(value):
    value = value.strip()
    if not value:
        raise ValueError(tr("Enter a website address."))
    if "://" not in value:
        value = "https://" + value
    parsed = urlsplit(value)
    if parsed.scheme not in {"https", "http"} or not parsed.hostname:
        raise ValueError(tr("Enter a domain such as example.com or https://example.com/."))
    if parsed.username or parsed.password or parsed.port:
        raise ValueError(tr("Enter a domain without a login or port number."))
    try:
        domain = parsed.hostname.rstrip(".").encode("idna").decode("ascii").lower()
    except UnicodeError as exc:
        raise ValueError(tr("Invalid domain name.")) from exc
    if len(domain) > 253 or not all(
        0 < len(part) <= 63 and re.fullmatch(r"[a-z0-9](?:[a-z0-9-]*[a-z0-9])?", part)
        for part in domain.split(".")
    ) or "." not in domain:
        raise ValueError(tr("Invalid domain name."))
    return domain


def resolve_domain(domain, extra_hosts=()):
    hosts = [domain]
    if len(domain.split(".")) == 2 and not domain.startswith("www."):
        hosts.append("www." + domain)
    hosts.extend(extra_hosts)
    hosts = list(dict.fromkeys(hosts))
    found = {}
    for host in hosts:
        try:
            answers = socket.getaddrinfo(host, 443, socket.AF_INET, socket.SOCK_STREAM)
        except socket.gaierror:
            if host == domain:
                raise RuntimeError(tr("DNS returned no IPv4 address for {host}.", host=host))
            continue
        ips = sorted({answer[4][0] for answer in answers}, key=lambda ip: int(ipaddress.IPv4Address(ip)))
        ips = [ip for ip in ips if ipaddress.IPv4Address(ip).is_global]
        if host == domain and not ips:
            raise RuntimeError(tr("No public IPv4 address for {host}.", host=host))
        if ips:
            found[host] = ips
    return found


def run_bridge(action, **kwargs):
    args = ["powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
            "-File", str(BRIDGE), "-Action", action]
    for key, value in kwargs.items():
        args.extend(["-" + key, str(value)])
    result = subprocess.run(args, capture_output=True, text=True, errors="replace", timeout=35,
                            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    if result.returncode:
        raise RuntimeError((result.stderr or result.stdout or tr("Could not change the route.")).strip())
    if action == "Snapshot":
        return json.loads(result.stdout)
    return result.stdout.strip()


def load_state():
    if not STATE_PATH.exists():
        return {"version": 1, "domains": {}, "routes": {}}
    state = json.loads(STATE_PATH.read_text(encoding="utf-8-sig"))
    if state.get("version") != 1 or not isinstance(state.get("domains"), dict) or not isinstance(state.get("routes"), dict):
        raise RuntimeError(tr("domains.json has an unknown format."))
    return state


def save_state(state):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix="domains-", suffix=".tmp", dir=DATA_DIR)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as file:
            json.dump(state, file, ensure_ascii=False, indent=2)
            file.flush()
            os.fsync(file.fileno())
        os.replace(name, STATE_PATH)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def direct_cover(ip, snapshot):
    target = ipaddress.IPv4Address(ip)
    matches = []
    for route in snapshot["routes"]:
        try:
            network = ipaddress.IPv4Network(route["prefix"], strict=False)
        except ValueError:
            continue
        if network.prefixlen > 0 and target in network:
            matches.append((network.prefixlen, route))
    if not matches:
        return None
    best_len = max(length for length, _ in matches)
    best = [route for length, route in matches if length == best_len]
    direct = [route for route in best if route["interface_index"] == snapshot["interface_index"]
              and route["gateway"] == snapshot["gateway"]]
    if direct and len(direct) == len(best):
        return "direct"
    if direct:
        return "conflict"
    return None


def owned_route_present(ip, details, snapshot):
    return any(route["prefix"] == ip + "/32" and route["gateway"] == details["gateway"]
               and route["metric"] == METRIC and route["interface_index"] == snapshot["interface_index"]
               and snapshot["interface_guid"] == details["interface_guid"]
               for route in snapshot["routes"])


def flatten_ips(hosts):
    return sorted({ip for values in hosts.values() for ip in values}, key=lambda ip: int(ipaddress.IPv4Address(ip)))


def cleanup_orphans(state):
    needed = {ip for record in state["domains"].values() for ip in record["ips"]}
    for ip, details in list(state["routes"].items()):
        if ip in needed:
            continue
        run_bridge("Remove", Prefix=ip + "/32", Gateway=details["gateway"],
                   InterfaceGuid=details["interface_guid"], Metric=METRIC)
        state["routes"].pop(ip)
        save_state(state)


def add_or_refresh(domain):
    state = load_state()
    catalog = load_catalog()
    extras = catalog.get(domain, {}).get("hosts", ())
    hosts = resolve_domain(domain, extras)
    ips = flatten_ips(hosts)
    snapshot = run_bridge("Snapshot")
    if any(direct_cover(ip, snapshot) == "conflict" for ip in ips):
        raise RuntimeError(tr("A competing route exists for one of these IPs. Nothing changed."))
    state["domains"][domain] = {"hosts": hosts, "ips": ips}
    save_state(state)
    added = 0
    for ip in ips:
        if direct_cover(ip, snapshot) == "direct":
            continue
        if ip in state["routes"] and owned_route_present(ip, state["routes"][ip], snapshot):
            continue
        details = {"gateway": snapshot["gateway"], "interface_guid": snapshot["interface_guid"]}
        state["routes"][ip] = details
        save_state(state)
        try:
            run_bridge("Add", Prefix=ip + "/32", Gateway=details["gateway"],
                       InterfaceIndex=snapshot["interface_index"], InterfaceGuid=details["interface_guid"], Metric=METRIC)
            added += 1
            snapshot["routes"].append({"prefix": ip + "/32", "gateway": details["gateway"],
                                       "interface_index": snapshot["interface_index"], "metric": METRIC})
        except Exception:
            # Keep the recorded intent so a later refresh or deletion can reconcile an interrupted change.
            raise
    cleanup_orphans(state)
    return tr("{domain}: {count} IPs found; {added} routes added.", domain=domain, count=len(ips), added=added)


def delete_domain(domain):
    state = load_state()
    if domain not in state["domains"]:
        raise RuntimeError(tr("The domain is no longer in the list."))
    del state["domains"][domain]
    save_state(state)
    cleanup_orphans(state)
    return tr("{domain} removed. Unused routes removed.", domain=domain)


class Window:
    def __init__(self, root):
        global LANG
        LANG = load_state().get("language", "en")
        self.root = root
        self.root.geometry("790x560")
        self.root.minsize(670, 470)
        self.events = queue.Queue()
        self.busy = False
        self.snapshot = None
        self.catalog = load_catalog()
        self.build()
        self.set_language(LANG, persist=False)
        self.root.after(100, self.poll)
        self.reload()

    def build(self):
        outer = ttk.Frame(self.root, padding=16)
        outer.pack(fill="both", expand=True)
        header = ttk.Frame(outer)
        header.pack(fill="x")
        self.heading = ttk.Label(header, font=("Segoe UI", 17, "bold"))
        self.heading.pack(side="left")
        self.language_value = tk.StringVar(value="English")
        language = ttk.Combobox(header, textvariable=self.language_value, values=("English", "Русский"),
                                state="readonly", width=11)
        language.pack(side="right")
        language.bind("<<ComboboxSelected>>", lambda _: self.set_language("ru" if self.language_value.get() == "Русский" else "en"))
        self.subtitle = ttk.Label(outer)
        self.subtitle.pack(anchor="w", pady=(2, 12))
        row = ttk.Frame(outer)
        row.pack(fill="x")
        self.domain_value = tk.StringVar()
        entry = ttk.Entry(row, textvariable=self.domain_value)
        entry.pack(side="left", fill="x", expand=True)
        entry.bind("<Return>", lambda _: self.add())
        self.add_button = ttk.Button(row, command=self.add)
        self.add_button.pack(side="left", padx=(8, 0))
        tabs = ttk.Notebook(outer)
        tabs.pack(fill="both", expand=True, pady=(14, 0))
        main = ttk.Frame(tabs, padding=10)
        popular = ttk.Frame(tabs, padding=10)
        old = ttk.Frame(tabs, padding=10)
        tabs.add(main)
        tabs.add(popular)
        tabs.add(old)
        self.tabs = tabs
        self.domains = ttk.Treeview(main, columns=("ips", "status"), show="headings", height=8)
        self.domains.column("ips", width=420)
        self.domains.column("status", width=260)
        self.domains.pack(fill="both", expand=True)
        self.domains.bind("<<TreeviewSelect>>", lambda _: self.show_details())
        actions = ttk.Frame(main)
        actions.pack(fill="x", pady=(8, 4))
        self.update_button = ttk.Button(actions, command=self.update)
        self.update_button.pack(side="left")
        self.delete_button = ttk.Button(actions, command=self.delete)
        self.delete_button.pack(side="left", padx=8)
        self.reload_button = ttk.Button(actions, command=self.reload)
        self.reload_button.pack(side="right")
        self.details = tk.Text(main, height=5, wrap="word", relief="flat", background="#f4f6f8")
        self.details.pack(fill="x", pady=(4, 0))
        self.details.configure(state="disabled")
        self.catalog_intro = ttk.Label(popular)
        self.catalog_intro.pack(anchor="w", pady=(0, 8))
        self.catalog_tree = ttk.Treeview(popular, columns=("site", "domain"), show="headings")
        self.catalog_tree.column("site", width=300)
        self.catalog_tree.column("domain", width=320)
        self.catalog_tree.pack(fill="both", expand=True)
        self.catalog_tree.bind("<Double-1>", lambda _: self.add_from_catalog())
        self.catalog_button = ttk.Button(popular, command=self.add_from_catalog)
        self.catalog_button.pack(anchor="w", pady=(8, 0))
        self.old_intro = ttk.Label(old)
        self.old_intro.pack(anchor="w", pady=(0, 8))
        self.existing_tree = ttk.Treeview(old, columns=("network", "gateway"), show="headings")
        self.existing_tree.column("network", width=330)
        self.existing_tree.column("gateway", width=290)
        self.existing_tree.pack(fill="both", expand=True)
        self.status = tk.StringVar()
        ttk.Label(outer, textvariable=self.status).pack(anchor="w", pady=(10, 0))

    def set_language(self, value, persist=True):
        global LANG
        LANG = value
        self.language_value.set("Русский" if LANG == "ru" else "English")
        self.root.title("DirectLane — " + tr("Domains outside VPN"))
        self.heading.configure(text="DirectLane")
        self.subtitle.configure(text=tr("Enter a website. Its IPs will use your regular connection."))
        self.add_button.configure(text=tr("Add"))
        self.tabs.tab(0, text=tr("My domains"))
        self.tabs.tab(1, text=tr("Popular sites"))
        self.tabs.tab(2, text=tr("Existing routes"))
        self.domains.heading("ips", text=tr("Domain / addresses"))
        self.domains.heading("status", text=tr("Status"))
        self.update_button.configure(text=tr("Refresh selected IPs"))
        self.delete_button.configure(text=tr("Remove selected"))
        self.reload_button.configure(text=tr("Refresh view"))
        self.catalog_intro.configure(text=tr("Choose a site and press Add. DNS addresses are checked when you add it."))
        self.catalog_tree.heading("site", text=tr("Site"))
        self.catalog_tree.heading("domain", text=tr("Domain"))
        self.catalog_button.configure(text=tr("+ Add selected site"))
        self.catalog_tree.delete(*self.catalog_tree.get_children())
        for domain, item in self.catalog.items():
            self.catalog_tree.insert("", "end", iid=domain,
                                     values=(item["name_ru"] if LANG == "ru" else item["name_en"], domain))
        self.old_intro.configure(text=tr("These routes were created outside DirectLane and are shown for reference."))
        self.existing_tree.heading("network", text=tr("Network"))
        self.existing_tree.heading("gateway", text=tr("Gateway"))
        self.status.set(tr("Loading..."))
        if persist:
            state = load_state()
            state["language"] = LANG
            save_state(state)
            if self.snapshot:
                self.render(state, self.snapshot)

    def start(self, operation, done):
        if self.busy:
            return
        self.busy = True
        self.status.set(tr("Checking addresses and routes..."))
        for button in (self.add_button, self.update_button, self.delete_button, self.reload_button, self.catalog_button):
            button.configure(state="disabled")

        def worker():
            try:
                self.events.put((done, operation(), None))
            except Exception as exc:
                self.events.put((done, None, str(exc)))
        threading.Thread(target=worker, daemon=True).start()

    def poll(self):
        try:
            while True:
                done, value, error = self.events.get_nowait()
                self.busy = False
                for button in (self.add_button, self.update_button, self.delete_button, self.reload_button, self.catalog_button):
                    button.configure(state="normal")
                if error:
                    self.status.set(tr("Error: {error}", error=error.splitlines()[-1]))
                    messagebox.showerror(tr("Could not complete the action"), error)
                else:
                    done(value)
        except queue.Empty:
            pass
        self.root.after(100, self.poll)

    def reload(self, notice=""):
        def work():
            return load_state(), run_bridge("Snapshot")
        self.start(work, lambda value: self.render(*value, notice=notice))

    def render(self, state, snapshot, notice=""):
        selected = self.selected_domain()
        self.snapshot = snapshot
        self.domains.delete(*self.domains.get_children())
        for domain, record in sorted(state["domains"].items()):
            ips = record["ips"]
            good = sum(direct_cover(ip, snapshot) == "direct" for ip in ips)
            status = tr("Bypass active") if good == len(ips) else tr("Check: {good}/{total} IPs", good=good, total=len(ips))
            self.domains.insert("", "end", iid=domain, values=(f"{domain} · {len(ips)} IP", status))
        if selected in self.domains.get_children():
            self.domains.selection_set(selected)
        self.show_details()
        self.existing_tree.delete(*self.existing_tree.get_children())
        owned = {ip + "/32" for ip in state["routes"]}
        for route in sorted(snapshot["routes"], key=lambda item: item["prefix"]):
            if (route["interface_index"] == snapshot["interface_index"] and
                route["gateway"] == snapshot["gateway"] and route["prefix"] != "0.0.0.0/0" and
                route["prefix"] not in owned):
                self.existing_tree.insert("", "end", values=(route["prefix"], route["gateway"]))
        self.status.set(notice or tr("Regular connection: {name} · {gateway}", name=snapshot['interface_name'], gateway=snapshot['gateway']))

    def selected_domain(self):
        selected = self.domains.selection()
        return selected[0] if selected else None

    def show_details(self):
        self.details.configure(state="normal")
        self.details.delete("1.0", "end")
        domain = self.selected_domain()
        if domain:
            record = load_state()["domains"].get(domain, {})
            lines = []
            for host, ips in record.get("hosts", {}).items():
                lines.append(f"{host}: {', '.join(ips)}")
            lines.append(tr("IPs can change. If the website stops working, select Refresh selected IPs."))
            self.details.insert("1.0", "\n".join(lines))
        else:
            self.details.insert("1.0", tr("Select a domain to see its addresses."))
        self.details.configure(state="disabled")

    def add(self):
        try:
            domain = normalize_domain(self.domain_value.get())
        except ValueError as exc:
            messagebox.showerror(tr("Website address"), str(exc))
            return
        self.start(lambda: add_or_refresh(domain), lambda notice: self.reload(notice))

    def update(self):
        domain = self.selected_domain()
        if domain:
            self.start(lambda: add_or_refresh(domain), lambda notice: self.reload(notice))

    def delete(self):
        domain = self.selected_domain()
        if domain:
            self.start(lambda: delete_domain(domain), lambda notice: self.reload(notice))

    def add_from_catalog(self):
        selected = self.catalog_tree.selection()
        if selected:
            domain = selected[0]
            self.start(lambda: add_or_refresh(domain), lambda notice: self.reload(notice))


def main():
    if sys.platform != "win32":
        raise SystemExit("Программа работает в Windows.")
    if len(sys.argv) == 3 and sys.argv[1] == "--self-check":
        report = {"catalog_entries": len(load_catalog()),
                  "gateway": run_bridge("Snapshot")["gateway"],
                  "bridge_present": BRIDGE.is_file()}
        Path(sys.argv[2]).write_text(json.dumps(report), encoding="utf-8")
        return
    if not ctypes.windll.shell32.IsUserAnAdmin():
        params = subprocess.list2cmdline(([str(Path(__file__).resolve())] if not getattr(sys, "frozen", False) else []) + ["--elevated"])
        result = ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, str(APP_DIR), 1)
        if result <= 32:
            raise SystemExit("Для управления маршрутами нужны права администратора.")
        return
    root = tk.Tk()
    try:
        Window(root)
    except Exception as exc:
        messagebox.showerror(tr("Could not open the app"), str(exc))
        root.destroy()
        return
    root.mainloop()


if __name__ == "__main__":
    main()
