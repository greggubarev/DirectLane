# DirectLane

<img src="assets/directlane-icon.png" alt="DirectLane icon" width="96">

DirectLane помогает открывать выбранные сайты через обычное подключение, пока VPN остаётся включённым. Это пригодится, если VPN-клиент не умеет добавлять сайты в исключения. Домен можно ввести вручную или выбрать из списка.

Программа узнаёт IPv4-адреса сайта через DNS и добавляет маршруты через ваш обычный интернет-шлюз. Добавленные домены и адреса видны в окне. Если адреса изменились, их можно обновить. Если исключение больше не нужно, домен можно удалить.

### С какими VPN-клиентами пригодится

DirectLane полезна, когда Windows-клиент VPN не позволяет исключить отдельные сайты. При этом у клиента может быть другой вид раздельного туннелирования, например по приложениям или IP-адресам.

- [hidemy.name VPN для Windows](https://hide-my-name.cc/faq/vpn/vpn-installation-and-configuration/windows/customization/): в описанных настройках есть просмотр маршрутов и Kill Switch, но нет списка исключений сайтов. DirectLane создавалась для конфигурации hidemy.name, где такие исключения были недоступны.
- [OpenVPN Connect для Windows](https://openvpn.net/connect-docs/app-settings-windows.html) с профилем, направляющим весь трафик через VPN: в настройках клиента нет личного списка исключений сайтов. При этом [раздельное туннелирование можно настроить на сервере OpenVPN](https://openvpn.net/as-docs/v3/tutorials/tutorial--full-and-split-tunnel-vpn.html).
- [Outline Client для Windows](https://github.com/OutlineFoundation/outline-apps/issues/887): выборочная маршрутизация остаётся открытым запросом на функцию. Совместимость с установленной версией нужно проверить, поскольку Outline сам управляет маршрутами.
- [WireGuard для Windows](https://github.com/WireGuard/wireguard-windows/blob/master/docs/netquirk.md): параметр `AllowedIPs` работает с диапазонами IP, а не с меняющимися адресами сайтов. Профиль с маршрутом `/0` включает строгие правила брандмауэра WireGuard, которые могут блокировать обход. DirectLane имеет смысл использовать только с профилем, разрешающим прямой трафик.

Это примеры подходящих сценариев, а не гарантия совместимости. VPN-клиент должен разрешать Windows отправлять трафик по более точному маршруту через обычный шлюз. Если в вашем клиенте уже работают исключения сайтов, удобнее использовать их.

Скачайте нужный архив на [странице выпусков](https://github.com/greggubarev/DirectLane/releases). Папочную версию нужно распаковать целиком и запустить `DirectLane/DirectLane.exe`. В архиве `DirectLane-v0.1.1-windows-single-file.zip` находится один `DirectLane.exe`, но он может запускаться дольше. Windows запросит права администратора для изменения маршрутов. Список доменов хранится в `%LOCALAPPDATA%\DirectLane\domains.json` и не входит в архив.

По умолчанию интерфейс на английском. Переключатель на русский находится вверху окна.
Во встроенном списке 42 сайта. Их можно искать по названию или домену.

Маршруты работают с IP-адресами, а не с отдельными страницами. Если несколько сайтов используют один IP, они могут открываться через обычное подключение вместе. IPv6 программа не меняет. VPN-клиент с Kill Switch может блокировать прямое соединение. Сайты в [списке](catalog.json) приведены для удобства: не каждый из них обязательно испытывает проблемы при работе через VPN.

Подборка основана на категориях проекта [RU Direct](https://github.com/kyoresuas/ru-direct). DirectLane узнаёт текущие адреса при добавлении сайта. Программа не загружает чужие списки маршрутов и не добавляет все 42 сайта автоматически.

Правила, созданные вне DirectLane, видны на вкладке `Другие маршруты`, но программа их не удаляет. Если изменился обычный шлюз или VPN-клиент заменил маршруты при переключении сервера, обновите IP нужных доменов.

Для сборки нужны Windows 10 или 11, Python 3.14 с `tkinter`, PowerShell 5.1 или новее и доступ в интернет для установки зависимости. В папке репозитория выполните:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\build.ps1
```

Получатся `dist\DirectLane\DirectLane.exe` и `dist-single\DirectLane.exe`. Запуск без сборки: `pyw -3 manager.pyw`. Проверка: `py -3 -m unittest discover -p 'test_*.py' -v`.

## English
DirectLane opens selected websites outside your VPN on Windows. It is useful when a VPN client does not offer split tunneling for websites. You can add a domain yourself or pick one from the built-in list.

The app looks up the site's IPv4 addresses and adds Windows routes through your regular internet connection. Your VPN stays connected for other traffic. You can see the addresses in the app, refresh them when they change, and remove a domain when you no longer need the exception.

## VPN clients

DirectLane is useful when a Windows VPN client does not let you exclude individual websites, even if it offers other kinds of split tunneling. These are setups where it may help:

- [hidemy.name VPN for Windows](https://hide-my-name.cc/faq/vpn/vpn-installation-and-configuration/windows/customization/): its documented settings show routes and a kill switch, but no website exception list. DirectLane was developed for a hidemy.name setup where site exceptions were unavailable.
- [OpenVPN Connect for Windows](https://openvpn.net/connect-docs/app-settings-windows.html) with a full-tunnel profile: its client settings do not include a personal website exception list. OpenVPN servers can provide [their own split-tunnel rules](https://openvpn.net/as-docs/v3/tutorials/tutorial--full-and-split-tunnel-vpn.html), so this is not a claim that OpenVPN lacks split tunneling.
- [Outline Client for Windows](https://github.com/OutlineFoundation/outline-apps/issues/887): selective routing remains an open feature request. Test your installed version before relying on DirectLane because Outline also manages system routing.
- [WireGuard for Windows](https://github.com/WireGuard/wireguard-windows/blob/master/docs/netquirk.md): its `AllowedIPs` setting handles IP ranges, not a changing list of website addresses. A full-tunnel `/0` profile enables WireGuard's restrictive firewall and can block DirectLane's routes. Use DirectLane only with a profile that permits direct traffic.

This is a list of possible use cases, not a compatibility guarantee. DirectLane works only when the VPN lets Windows send traffic through a more specific route to the regular gateway. If your VPN already has working website exceptions, use those instead.

## Download

Get the latest build from [Releases](https://github.com/greggubarev/DirectLane/releases):

- `DirectLane-v0.1.1-windows-portable.zip`: extract the whole archive and run `DirectLane/DirectLane.exe`.
- `DirectLane-v0.1.1-windows-single-file.zip`: extract and run `DirectLane.exe`. This version may start more slowly.

Windows asks for administrator rights because the app changes network routes. The domain list is stored in `%LOCALAPPDATA%\DirectLane\domains.json`. It is not included in the download.

The interface starts in English. Use the language switch at the top of the window to select Russian.
The built-in list has 42 sites and can be searched by name or domain.

## How it works

1. Enter a website address or select a site from the list. DirectLane asks DNS for its current IPv4 addresses. Sites in the built-in list may have extra domains for images or sign-in.
2. DirectLane finds your regular network gateway and creates a route for each address that does not already have a direct route.
3. If the site stops working after its addresses change, select it and click `Refresh selected IPs`. Removing a domain also removes routes created by DirectLane when no other listed domain uses them.

Windows routes work with IP addresses, not individual URLs. If several sites share an IP address, they may all use the direct connection. The app does not change IPv6 routes. A VPN kill switch may still block traffic outside the tunnel. The built-in [site list](catalog.json) contains examples, not a claim that those sites block VPN users.

The catalog is a small selection of commonly routed services from [RU Direct](https://github.com/kyoresuas/ru-direct). DirectLane resolves their current addresses when you add a site. It does not download a routing list or add every catalog site automatically.

Routes created outside DirectLane are shown on the `Existing routes` tab for reference. The app does not remove them. If your regular gateway changes, refresh the affected domains. If your VPN replaces direct routes when it switches servers, refresh them after the switch.

## Build from source

You need Windows 10 or 11, Python 3.14 with `tkinter`, PowerShell 5.1 or newer, and internet access to install the build dependency. In PowerShell, run from the repository folder:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\build.ps1
```

The script creates a local virtual environment and builds `dist\DirectLane\DirectLane.exe` and `dist-single\DirectLane.exe`. To run without building, use `pyw -3 manager.pyw`. To run the tests, use `py -3 -m unittest discover -p 'test_*.py' -v`.

Source files are UTF-8. Keep `routes.ps1` and `catalog.json` next to `manager.pyw` when running from source. The build script does not add or remove routes.

Лицензия: [MIT](LICENSE).
