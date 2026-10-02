# DirectLane

<img src="assets/directlane-icon.png" alt="Значок DirectLane / DirectLane icon" width="96">

## Русский

DirectLane открывает выбранные сайты через обычное подключение, пока VPN остаётся включённым. Программа пригодится, если в Windows-клиенте VPN нет удобных исключений для отдельных сайтов. Домен можно ввести вручную или выбрать из каталога.

DirectLane узнаёт текущие IPv4-адреса сайта через DNS и создаёт для них маршруты через обычный интернет-шлюз. Остальной трафик продолжает идти через VPN. Найденные адреса можно посмотреть, обновить и удалить вместе с доменом.

### С какими VPN-клиентами пригодится

Речь об исключениях для сайтов. У перечисленных клиентов могут быть другие виды раздельного туннелирования, например по приложениям или IP-адресам.

- [hidemy.name VPN для Windows](https://hide-my-name.cc/faq/vpn/vpn-installation-and-configuration/windows/customization/): в описанных настройках есть просмотр маршрутов и Kill Switch, но нет списка исключений сайтов. DirectLane создавалась для конфигурации hidemy.name, где такие исключения были недоступны.
- [OpenVPN Connect для Windows](https://openvpn.net/connect-docs/app-settings-windows.html) с профилем, направляющим весь трафик через VPN: в настройках клиента нет личного списка исключений сайтов. При этом [раздельное туннелирование можно настроить на сервере OpenVPN](https://openvpn.net/as-docs/v3/tutorials/tutorial--full-and-split-tunnel-vpn.html).
- [Outline Client для Windows](https://github.com/OutlineFoundation/outline-apps/issues/887): выборочная маршрутизация остаётся открытым запросом на функцию. Совместимость с установленной версией нужно проверить, поскольку Outline сам управляет маршрутами.
- [WireGuard для Windows](https://github.com/WireGuard/wireguard-windows/blob/master/docs/netquirk.md): параметр `AllowedIPs` работает с диапазонами IP, а не со списком сайтов. Профиль с маршрутом `/0` включает строгие правила брандмауэра WireGuard, которые могут блокировать обход. DirectLane имеет смысл использовать только с профилем, разрешающим прямой трафик.

Это примеры, а не гарантия совместимости. VPN-клиент должен разрешать Windows отправлять трафик по более точному маршруту через обычный шлюз. Если в клиенте уже работают исключения сайтов, используйте их.

### Скачать и запустить

Скачайте нужный архив на [странице выпусков](https://github.com/greggubarev/DirectLane/releases):

- `DirectLane-v0.1.1-windows-portable.zip`: распакуйте архив целиком и запустите `DirectLane/DirectLane.exe`.
- `DirectLane-v0.1.1-windows-single-file.zip`: распакуйте и запустите `DirectLane.exe`. Эта версия может запускаться дольше.

Windows запросит права администратора для изменения маршрутов. Список доменов хранится в `%LOCALAPPDATA%\DirectLane\domains.json` и не входит в архив. По умолчанию интерфейс на английском; переключатель на русский находится вверху окна. В каталоге 42 сайта, их можно искать по названию или домену.

### Как работает

1. Введите адрес сайта или выберите его из каталога. DirectLane узнает его текущие IPv4-адреса через DNS. Для сайтов из каталога программа может проверить дополнительные домены, например для изображений или входа.
2. Программа находит обычный интернет-шлюз и добавляет маршрут для каждого адреса, который ещё не охвачен прямым маршрутом.
3. Если адреса сайта изменились, выберите домен и нажмите `Обновить IP выбранного`. При удалении домена программа убирает созданные ею маршруты, если они больше не нужны другим добавленным доменам.

Маршруты работают с IP-адресами, а не с отдельными страницами. Сайты с общим IP могут открываться напрямую вместе. IPv6 программа не меняет. Kill Switch VPN-клиента может блокировать прямое соединение. Наличие сайта в [каталоге](catalog.json) не означает, что он обязательно не работает через VPN.

Каталог составлен по категориям проекта [RU Direct](https://github.com/kyoresuas/ru-direct). DirectLane узнаёт адреса при добавлении сайта, не загружает чужие списки маршрутов и не добавляет весь каталог автоматически.

Маршруты, созданные вне DirectLane, показаны на вкладке `Другие маршруты` для справки; программа их не удаляет. Если изменился обычный шлюз или VPN-клиент заменил маршруты при переключении сервера, обновите IP нужных доменов.

### Сборка из исходников

Нужны Windows 10 или 11, Python 3.14 с `tkinter`, PowerShell 5.1 или новее и интернет для установки зависимости сборки. В папке репозитория выполните:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\build.ps1
```

Скрипт создаст локальное виртуальное окружение и соберёт `dist\DirectLane\DirectLane.exe` и `dist-single\DirectLane.exe`. Запуск без сборки: `pyw -3 manager.pyw`. Проверка: `py -3 -m unittest discover -p 'test_*.py' -v`.

Исходные файлы сохранены в UTF-8. При запуске из исходников держите `routes.ps1` и `catalog.json` рядом с `manager.pyw`. Сборка и тесты не меняют маршруты.

### Лицензия

[MIT](LICENSE).

## English

DirectLane opens selected websites through your regular connection while your VPN stays on. It is useful when a Windows VPN client has no convenient exceptions for individual websites. Enter a domain or choose one from the catalog.

DirectLane looks up the site's current IPv4 addresses through DNS and creates Windows routes through your regular internet gateway. Other traffic continues through the VPN. You can inspect the addresses, refresh them, and remove them with the domain.

### VPN clients

The examples below concern website exceptions. These clients may support other kinds of split tunneling, such as app-based or IP-based routing.

- [hidemy.name VPN for Windows](https://hide-my-name.cc/faq/vpn/vpn-installation-and-configuration/windows/customization/): its documented settings show routes and a kill switch, but no website exception list. DirectLane was developed for a hidemy.name setup where site exceptions were unavailable.
- [OpenVPN Connect for Windows](https://openvpn.net/connect-docs/app-settings-windows.html) with a full-tunnel profile: its client settings do not include a personal website exception list. OpenVPN servers can provide [their own split-tunnel rules](https://openvpn.net/as-docs/v3/tutorials/tutorial--full-and-split-tunnel-vpn.html).
- [Outline Client for Windows](https://github.com/OutlineFoundation/outline-apps/issues/887): selective routing remains an open feature request. Test your installed version because Outline also manages system routes.
- [WireGuard for Windows](https://github.com/WireGuard/wireguard-windows/blob/master/docs/netquirk.md): `AllowedIPs` handles IP ranges, not a list of websites. A full-tunnel `/0` profile enables WireGuard's restrictive firewall and can block direct routes. Use DirectLane only with a profile that permits direct traffic.

These are possible use cases, not a compatibility guarantee. The VPN client must let Windows send traffic through a more specific route to the regular gateway. If your client already has working website exceptions, use those instead.

### Download and run

Get an archive from [Releases](https://github.com/greggubarev/DirectLane/releases):

- `DirectLane-v0.1.1-windows-portable.zip`: extract the whole archive and run `DirectLane/DirectLane.exe`.
- `DirectLane-v0.1.1-windows-single-file.zip`: extract and run `DirectLane.exe`. This version may start more slowly.

Windows asks for administrator rights to change routes. The domain list is stored in `%LOCALAPPDATA%\DirectLane\domains.json` and is not included in the archive. The interface starts in English; use the switch at the top of the window to select Russian. The catalog has 42 sites and can be searched by name or domain.

### How it works

1. Enter a website address or select a site from the catalog. DirectLane looks up its current IPv4 addresses through DNS. Catalog entries may include extra domains for images or sign-in.
2. The app finds your regular internet gateway and adds a route for each address that does not already have a direct route.
3. If the site's addresses change, select the domain and click `Refresh selected IPs`. Removing a domain also removes routes created by DirectLane when no other listed domain needs them.

Routes work with IP addresses, not individual pages. Sites sharing an IP may use the direct connection together. The app does not change IPv6 routes. A VPN kill switch may block direct traffic. A site appearing in the [catalog](catalog.json) does not mean it necessarily fails over VPN.

The catalog is selected from the categories in [RU Direct](https://github.com/kyoresuas/ru-direct). DirectLane resolves addresses when you add a site; it does not download another routing list or add the whole catalog automatically.

Routes created outside DirectLane appear on the `Existing routes` tab for reference; the app does not remove them. If your regular gateway changes or the VPN replaces routes when switching servers, refresh the affected domains.

### Build from source

You need Windows 10 or 11, Python 3.14 with `tkinter`, PowerShell 5.1 or newer, and internet access to install the build dependency. In the repository folder, run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\build.ps1
```

The script creates a local virtual environment and builds `dist\DirectLane\DirectLane.exe` and `dist-single\DirectLane.exe`. To run without building, use `pyw -3 manager.pyw`. To run the tests, use `py -3 -m unittest discover -p 'test_*.py' -v`.

Source files are UTF-8. Keep `routes.ps1` and `catalog.json` next to `manager.pyw` when running from source. Building and testing do not change routes.

### License

[MIT](LICENSE).
