# DirectLane — Windows VPN split tunneling by domain

**DirectLane is a lightweight Windows desktop app that lets selected websites bypass a VPN.** Enter a domain or choose a site from the catalog. DirectLane resolves its current IPv4 addresses and creates Windows routes through your normal internet gateway. Inspect the addresses, refresh them after DNS changes, or remove the rule from one window. It works with VPN clients that allow Windows routes to take effect; no subscription or VPN account is needed by DirectLane.

**DirectLane — программа для раздельного туннелирования VPN по доменам в Windows.** Если нужный сайт не открывается с включённым VPN, добавьте его адрес: программа узнает IP через DNS и направит эти IP через обычное интернет-подключение. Добавленные домены видны в списке; IP можно обновить, правило — удалить. По умолчанию интерфейс на английском, русский включается переключателем.

This solves a common split tunneling gap: a VPN app may switch servers automatically but offer no usable website exceptions. DirectLane keeps the VPN app in charge of the connection and adds narrow direct routes for the sites you choose. For example, you can leave the VPN connected for most traffic while opening a banking, government, shopping, or map site through your regular connection. Whether a particular site requires this depends on its own rules and your network.

### When is it useful? / Когда это полезно?

- A website refuses connections from a VPN exit IP, but your VPN client has no website exception list.
- You need the VPN for other apps and sites, so disconnecting it every time is inconvenient.
- The VPN client changes countries or servers, while the same chosen websites should keep using your regular connection.
- Сайт не открывается с VPN, а в VPN-клиенте нет удобного списка исключений по сайтам.
- VPN нужен для других программ и сайтов, поэтому постоянно выключать его неудобно.
- VPN автоматически меняет серверы, а выбранные сайты должны оставаться на обычном подключении.

## Download and run

Download a Windows archive from [Releases](https://github.com/greggubarev/DirectLane/releases), extract it, and run `DirectLane.exe`. Windows will request administrator rights because adding and removing system routes requires them. Keep the portable folder together. The single-file archive offers one executable; its first launch can take longer.

The app stores your domain list at `%LOCALAPPDATA%\DirectLane\domains.json`. The published archives contain no personal domains or route history. Routes created by the app remain after a reboot and can be removed through **My domains**. Routes created by other programs appear under **Existing routes** for reference; DirectLane does not delete them.

## How it works

1. DNS turns a domain into one or more current IPv4 addresses. For a root domain, DirectLane also checks `www`. Catalog entries can include related hosts, such as an image or sign-in domain.
2. The app finds the physical network adapter and its ordinary gateway.
3. It adds a narrow Windows route (`/32`) for each address that is not already covered by a direct route. The route points to the ordinary gateway, so it remains useful if the VPN changes servers.
4. **Refresh selected IPs** resolves DNS again, adds new routes, and removes old routes owned by DirectLane when no listed domain needs them.

The catalog is a convenient list of examples. It does not mean every listed website blocks VPN connections. Domain names and their associated hosts are stored in [`catalog.json`](catalog.json); IPs are resolved when a site is added. You can edit the catalog and rebuild the app.

For a GitHub repository, a concise description is: **“Windows app to open selected websites outside any route-compatible VPN. DNS based domain exceptions, English/Russian UI, no VPN account required.”** Suggested topics: `windows`, `vpn`, `split-tunneling`, `vpn-bypass`, `domain-routing`, `dns`, `python`, `tkinter`.

Windows routes operate on IP addresses, not URLs or individual browser tabs. Other services on a shared IP may also use the direct connection. External resources on unrelated domains may need separate entries. IPv6 is not changed. A VPN kill switch or firewall rule may still block direct traffic. **Status** confirms route selection, not that a website itself responds. If your ordinary gateway changes, refresh the affected domains. If your VPN replaces outside routes, refresh after switching its server.

## Build from source (Windows)

Requirements: Windows 10/11, Python 3.14 with `tkinter`, PowerShell 5.1 or later, and internet access for the build dependency. Run in PowerShell from the repository folder:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\build.ps1
```

The script creates an isolated `.venv`, installs the pinned build dependency from `requirements-build.txt`, and produces:

- `dist\DirectLane\DirectLane.exe` — portable folder build, faster to start.
- `dist-single\DirectLane.exe` — one executable, slower to start.

To run from source without building, use `pyw -3 manager.pyw`. To run the behavior tests: `py -3 -m unittest discover -p 'test_*.py' -v`. Neither test nor build applies routes; only the app's Add, Refresh, and Remove actions change them.

The release archive should contain the entire `dist\DirectLane` folder. Keep `routes.ps1` and `catalog.json` beside `manager.pyw` when running from source. Source files are UTF-8. Route changes are handled by the included PowerShell script and limited to the recorded adapter, gateway, IP, and metric when removing them.

---

## Русский

DirectLane — небольшая программа для Windows, которая открывает выбранные сайты через обычное подключение при работающем VPN. Введите домен или выберите сайт в каталоге. Можно посмотреть найденные IP, обновить их и удалить правило. Язык по умолчанию — английский; переключатель на русский находится вверху окна.

Скачайте архив для Windows со страницы [выпусков](https://github.com/greggubarev/DirectLane/releases), распакуйте его полностью и запустите `DirectLane.exe`. Для изменения маршрутов Windows запросит права администратора. Обычный архив с папкой запускается быстрее; архив с одним EXE удобнее переносить. Список доменов хранится в `%LOCALAPPDATA%\DirectLane\domains.json` и не входит в архивы выпуска. Маршруты, добавленные другими программами, видны во вкладке «Другие маршруты»; удаление их средствами DirectLane отключено.

Программа узнаёт IP домена через DNS, определяет обычный шлюз Windows и добавляет точный маршрут `/32` через него. Если IP уже охвачен существующим прямым маршрутом, повторное правило не создаётся. Кнопка «Обновить IP выбранного» заново опрашивает DNS. Каталог содержит примеры сайтов и связанных доменов, а не утверждение, что все они не работают с VPN. Если изображения или вход работают через другой домен, его можно добавить отдельно.

Для самостоятельной сборки установите Python 3.14 с `tkinter`, откройте PowerShell в папке исходников и выполните:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\build.ps1
```

Получатся папочная версия `dist\DirectLane\` и версия с одним EXE `dist-single\DirectLane.exe`. Запуск без сборки: `pyw -3 manager.pyw`. Проверка: `py -3 -m unittest discover -p 'test_*.py' -v`.

Маршруты относятся к IP, поэтому другие сайты на общем IP тоже могут открываться напрямую. IPv6 не меняется. Если адрес сайта, роутер или обычный шлюз изменился, обновите IP в программе. Функция Kill Switch или правила VPN-клиента могут мешать обходу даже при корректном маршруте.

## License / Лицензия

[MIT License](LICENSE) / [Лицензия MIT](LICENSE).
