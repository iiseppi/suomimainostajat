# Lisenssit

Repon listat kootaan muiden julkaisemista estolistoista. Jokaisella lähteellä on
oma lisenssinsä, ja sen ehdot koskevat myös siitä tehtyä listaa. Tämän kansion
tiedostot ovat lähteiden omia lisenssitekstejä sellaisinaan.

## Listat

| Lista | Lähteet | Lisenssit |
|---|---|---|
| `unifi/lists/laitteet.txt` | HaGeZi | GPL-3.0 |
| `unifi/lists/windows_spy.txt`, `windows_spy_ip.txt` | WindowsSpyBlocker | MIT |
| `unifi/lists/mainokset.txt` | StevenBlackin mainososiot, Disconnect, Cameleon | GPL-3.0, MIT, CC BY 3.0, CC BY 4.0, CC BY-NC-SA 4.0, ei-kaupallinen käyttö (ks. alla) |
| `unifi/lists/host.txt` | StevenBlackin muut osiot | MIT, CC BY-SA 4.0, CC0 1.0 (ks. alla) |
| `unifi/lists/suomi_mainokset.txt` | `list.txt` ja muiden mainoslähteiden `.fi`-domainit | kuten `mainokset.txt` |
| `unifi/lists/ip.txt` | (tyhjä) | – |

HaGeZin domainit ovat vain `laitteet.txt`:ssä. `mainokset.txt` ja
`suomi_mainokset.txt` sisältävät kuitenkin sekä Disconnectin GPL-3.0-dataa että
MVPS:n CC BY-NC-SA 4.0 -dataa, eivätkä nämä lisenssit sovi yhteen: GPL-3.0 ei
salli lisärajoituksia, kuten ei-kaupallisen käytön ehtoa.

## Lähteet

| Lähde | Lisenssi | Teksti |
|---|---|---|
| [HaGeZi DNS Blocklists](https://github.com/hagezi/dns-blocklists) | GPL-3.0 | [GPL-3.0.txt](GPL-3.0.txt) |
| [StevenBlack/hosts](https://github.com/StevenBlack/hosts) | MIT, lisäksi alilähteiden lisenssit | [MIT-StevenBlack.txt](MIT-StevenBlack.txt) |
| [WindowsSpyBlocker](https://github.com/crazy-max/WindowsSpyBlocker) | MIT | [MIT-WindowsSpyBlocker.txt](MIT-WindowsSpyBlocker.txt) |
| [Disconnect](https://disconnect.me/), mainoslista [`simple_ad.txt`](https://s3.amazonaws.com/lists.disconnect.me/simple_ad.txt) | GPL-3.0 (tiedoston otsakkeen mukaan) | [GPL-3.0.txt](GPL-3.0.txt) |
| Cameleon (`cameleon.txt`) | ei lisenssimerkintää | – |
| [harriko/suomimainostajat](https://github.com/harriko/suomimainostajat) (`list.txt`, `hosts`) | ei lisenssiä | – |

### StevenBlackin alilähteet

StevenBlackin yhdistetty hosts-tiedosto kokoaa useita listoja. Niiden lisenssit
ovat [StevenBlackin README:ssä](https://github.com/StevenBlack/hosts#sources-of-hosts-data-unified-in-this-variant).

| Osio | Lisenssi | Päätyy listaan |
|---|---|---|
| AdAway | CC BY 3.0 | `mainokset.txt` |
| add.2o7Net | MIT | `mainokset.txt` |
| hostsVN | MIT | `mainokset.txt` |
| MVPS hosts file | CC BY-NC-SA 4.0 ([teksti](CC-BY-NC-SA-4.0.txt)) | `mainokset.txt` |
| someonewhocares (Dan Pollock) | ei-kaupallinen käyttö, lähde mainittava | `mainokset.txt` |
| Tiuxo | CC BY 4.0 | `mainokset.txt` |
| UncheckyAds | MIT | `mainokset.txt` |
| yoyo.org | ei mainittu | `mainokset.txt` |
| Steven Black's ad-hoc list | MIT | `mainokset.txt` tai `host.txt` |
| add.Dead, add.Risk, add.Spam | MIT | `host.txt` |
| Badd Boyz Hosts | MIT | `host.txt` |
| KADhosts | CC BY-SA 4.0 | `host.txt` |
| minecraft-hosts | CC0 1.0 | `host.txt` |

## Mitä tämä tarkoittaa

* `laitteet.txt`:tä saa jakaa ja muokata vain GPL-3.0:n ehdoilla, ja
  lisenssiteksti on pidettävä mukana.
* `mainokset.txt` ja `suomi_mainokset.txt` sisältävät MVPS:n ja
  someonewhocaresin dataa. Niiden ehdot sallivat vain ei-kaupallisen käytön.
* `mainokset.txt` ja `suomi_mainokset.txt` sisältävät myös Disconnectin
  GPL-3.0-dataa.
* Kaikki listat tulevat ilman takuuta.
