# suomimainostajat

*English version: [below](#suomimainostajat-in-english).*

Estolista suomalaisille mainos- ja seurantapalvelimille. Repossa on myös
itsestään päivittyvät estolistat UniFi Networkin palomuuriin.

Alkuperäinen lista on [harriko/suomimainostajat](https://github.com/harriko/suomimainostajat).

## UniFi Network -listat

Listat on tehty UniFi Networkin (11.0.81+ / UniFi OS 6.0.10+) dynaamisiksi
**Network Lists** -listoiksi. Jokainen merkintä on vain yhdessä listassa.

| Lista | Tyyppi | Sisältö | Koko noin |
|---|---|---|---|
| `suomi_mainokset.txt` | Domain | Suomalaiset mainos- ja seurantadomainit (`list.txt` ja muiden listojen `.fi`-domainit) | 20 |
| `laitteet.txt` | Domain | Laitteiden ja käyttöjärjestelmien omat seurantapalvelimet: LG webOS, Samsung, Amazon, Roku, Apple, Xiaomi, Huawei, Oppo/Realme, Vivo, TikTok, Microsoft (HaGeZi) | 3 000 |
| `mainokset.txt` | Domain | Mainos- ja seurantadomainit (StevenBlack, Disconnect, Cameleon) | 27 600 |
| `windows_spy.txt` | Domain | Windowsin telemetria, lisäpalvelut ja Windows Update (WindowsSpyBlocker) | 430 |
| `windows_spy_ip.txt` | IP | Windowsin telemetrian IP-osoitteet (WindowsSpyBlocker) | 10 |
| `host.txt` | Domain | Haittaohjelmat, huijaukset ja roskaposti (StevenBlack) | 18 600 |

Koot ovat marraskuulta 2026. Ajantasaiset luvut ovat tiedostossa
[`unifi/lists/stats.json`](unifi/lists/stats.json). Lisäksi on `ip.txt` muille
IP-osoitteille, mutta lähteissä ei tällä hetkellä ole yhtään sellaista.

Listojen osoitteet UniFia varten:

```
https://raw.githubusercontent.com/iiseppi/suomimainostajat/master/unifi/lists/suomi_mainokset.txt
https://raw.githubusercontent.com/iiseppi/suomimainostajat/master/unifi/lists/laitteet.txt
https://raw.githubusercontent.com/iiseppi/suomimainostajat/master/unifi/lists/mainokset.txt
https://raw.githubusercontent.com/iiseppi/suomimainostajat/master/unifi/lists/windows_spy.txt
https://raw.githubusercontent.com/iiseppi/suomimainostajat/master/unifi/lists/windows_spy_ip.txt
https://raw.githubusercontent.com/iiseppi/suomimainostajat/master/unifi/lists/host.txt
```

### Käyttöönotto

1. **Networks → Network Lists → Create New**
2. Type: **Domain**, tai **IP** tiedostolle `windows_spy_ip.txt`
3. Source: **Dynamic**, ja URL yllä olevasta luettelosta
4. Päivitysväli: **24 h**
5. Tee palomuurisääntö, joka estää liikenteen listaan:
   **Settings → Policy Table → Create New Policy**, Action **Block**, Source Zone
   **Internal**, Destination Zone **External** ja kohteeksi lista. Network 10:ssä
   polku on Settings → Policy Engine → Policy Table.

### Sivuston salliminen (whitelist)

Jos estolista estää sivuston, jonka haluat pitää käytössä, tee sille oma
sallittujen lista ja Allow-sääntö estosääntöjen yläpuolelle. UniFi käy säännöt
läpi ylhäältä alas, ja ensimmäinen osuva sääntö ratkaisee. Esimerkissä sallitaan
kernel.org.

1. **Tee sallittujen lista.** Network Lists → Create New:
   * Name: `Sallitut`
   * Type: **Domain**
   * Source: käsin syötetty lista (ei Dynamic)
   * Domainit: `kernel.org` ja `www.kernel.org`. Lisää jokainen osoite erikseen,
     koska alidomainit eivät välttämättä sisälly pääverkkotunnukseen.
2. **Tee sallimissääntö.** Settings → Policy Table → Create New Policy:
   * Name: `Salli sallitut sivustot`
   * Action: **Allow**
   * Source Zone: **Internal**
   * Destination Zone: **External**, kohteeksi lista `Sallitut`
3. **Tee estosäännöt**, jos niitä ei vielä ole: samat asetukset, mutta Action
   **Block** ja kohteeksi estolista, esimerkiksi `mainokset`.
4. **Järjestä säännöt.** Avaa Zones-näkymä ja valitse vyöhykepari
   Internal → External. Valitse sääntölistan alta **Reorder** ja siirrä
   `Salli sallitut sivustot` ylimmäksi.

Valmis järjestys vyöhykeparille Internal → External:

| # | Sääntö | Action | Kohde |
|---|---|---|---|
| 1 | Salli sallitut sivustot | Allow | `Sallitut` |
| 2 | Estä mainokset | Block | `mainokset` |
| 3 | Estä laitteiden seuranta | Block | `laitteet` |
| … | Allow All Traffic (oletus) | Allow | kaikki |

Huomioitavaa:

* Sallimissääntö sallii sivuston IP-osoitteet kokonaan. Jos samaa osoitetta
  käyttää myös estetty domain (esimerkiksi CDN:ssä), sekin pääsee läpi.
* Sivu voi hakea sisältöä myös muista domaineista. Jos sivu ei vieläkään toimi,
  kytke estosääntöön **Flows Logging**, katso Insights-näkymästä, mitä estetään,
  ja lisää tarvittavat osoitteet `Sallitut`-listaan.
* Jos verkossa on muitakin sisäisiä vyöhykkeitä (esimerkiksi Hotspot tai oma
  IoT-vyöhyke), tee sallimis- ja estosäännöt jokaiselle.
* Valikkojen nimet vaihtelevat UniFi Networkin versioiden välillä.

### Päivittyminen

* GitHub Actions rakentaa listat uudelleen joka yö klo 02:23 UTC (Suomessa
  talvella 04:23, kesällä 05:23). Ajo käynnistyy myös heti, kun `list.txt`,
  `cameleon.txt` tai `unifi/build_lists.py` muuttuu. Ajo kestää noin puoli tuntia.
* Jokainen ajo hakee lähdelistat uudelleen ja tarkistaa jokaisen merkinnän.
  Merkintä pudotetaan, jos sen domain ei ratkea tai mikään sen osoitteista ei
  vastaa HTTPS:ään, HTTP:hen eikä pingiin. Jos palvelin myöhemmin vastaa taas,
  merkintä palaa listalle seuraavassa ajossa.
* Jos jokin lista kutistuisi yhdellä ajolla yli 25 %, ajo ei tallenna mitään, ja
  edellisen yön listat jäävät voimaan.
* UniFi hakee listan itse valitsemallasi päivitysvälillä.

### Huomioitavaa

* **Domain-esto voi estää muitakin sivustoja.** UniFi estää domainin
  IP-osoitteet. CDN-palveluissa (Cloudflare, Google, Azure, Akamai, CloudFront)
  samoja osoitteita käyttävät myös tavalliset sivustot. Pelkkään mainosestoon
  DNS-tason estäjä, kuten Pi-hole, on tarkempi.
* `laitteet.txt` estää valmistajien seurannan kaikilta laitteilta, joihin sääntö
  kohdistuu. Jos jonkin laitteen toiminto lakkaa, rajaa sääntö pois siltä
  laitteelta.
* `windows_spy.txt` estää myös Windows Updaten. Ilman poikkeusta Windows-koneet
  eivät saa päivityksiä.
* Domain-esto toimii vain, jos laitteet käyttävät gatewaytä nimipalvelimenaan.
* Yhteisön mukaan yhden listan raja on noin 100 000 merkintää ja kaikkien
  listojen yhteensä noin 500 000.

Tarkemmat tiedot ovat tiedostossa [`unifi/README.md`](unifi/README.md).

## Muut tiedostot

| Tiedosto | Sisältö |
|---|---|
| [`list.txt`](list.txt) | Suomalaiset mainos- ja seurantadomainit, yksi per rivi. Tästä syntyy `suomi_mainokset.txt`. |
| [`hosts`](hosts) | Alkuperäisen projektin tiedosto. Sisältö on sama kuin `list.txt`:ssä. |
| [`cameleon.txt`](cameleon.txt) | Cameleonin hosts-lista (2018), yksi `mainokset.txt`:n lähteistä. |
| [`unifi/`](unifi) | UniFi-listojen generaattori ja valmiit listat. |

`list.txt` käy sellaisenaan myös Pi-holen estolistaksi:

```
https://raw.githubusercontent.com/iiseppi/suomimainostajat/master/list.txt
```

## Domainin lisääminen

Lisää domain `list.txt`:hen omalle rivilleen, ilman `http://`-alkua ja polkua.
Kun muutos on masterissa, UniFi-listat rakentuvat uudelleen automaattisesti.

## Lähteet

* [harriko/suomimainostajat](https://github.com/harriko/suomimainostajat)
* [HaGeZi DNS Blocklists](https://github.com/hagezi/dns-blocklists), native tracker -listat
* [StevenBlack/hosts](https://github.com/StevenBlack/hosts)
* [crazy-max/WindowsSpyBlocker](https://github.com/crazy-max/WindowsSpyBlocker)
* [Disconnect](https://disconnect.me/), mainoslista `simple_ad.txt`
* Cameleon (`cameleon.txt`)

## Lisenssit

Jokainen lista noudattaa lähteidensä lisenssejä. `laitteet.txt` on GPL-3.0:n
alainen, ja `mainokset.txt` sekä `suomi_mainokset.txt` sisältävät dataa, jota saa
käyttää vain ei-kaupallisesti. Lähteiden lisenssit ja tarkemmat tiedot ovat
kansiossa [`LICENSES/`](LICENSES/README.md).

## Tietosuoja

Repo ei kerää tietoja listojen käyttäjistä.

* Listat ovat pelkkää tekstiä: yksi domain tai IP-osoite per rivi. Niissä ei ole
  skriptejä, evästeitä eikä mitään muuta, mikä lähettäisi tietoja minnekään.
* Listat rakennetaan GitHub Actionsissa. Generaattori hakee lähdelistat, kysyy
  julkisilta nimipalvelimilta (Cloudflare, Google, Quad9) ja testaa listojen
  palvelimia HTTPS:llä, HTTP:llä ja pingillä. Se ei ota yhteyttä käyttäjien
  verkkoihin eikä laitteisiin.
* README-tiedostoissa ei ole kuvia eikä seurantapikseleitä.
* Kun UniFi hakee listan, pyyntö menee GitHubille (`raw.githubusercontent.com`).
  GitHub näkee verkkosi julkisen IP-osoitteen ja pyynnön ajan kuten minkä tahansa
  web-pyynnön ja käsittelee niitä
  [oman tietosuojaselosteensa](https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement)
  mukaan.
* Repon ylläpitäjä näkee GitHubin Traffic-tilastoista vain koostelukuja repon
  sivujen katseluista ja kloonauksista. Niistä ei näe, kuka listoja käyttää.
* Jos et halua, että GitHub näkee verkkosi osoitteen, jaa listat omalta
  web-palvelimeltasi ja anna UniFille sen osoite.

---

# suomimainostajat (in English)

A blocklist of Finnish ad and tracking servers. The repository also has
self-updating blocklists for the UniFi Network firewall.

The original list is [harriko/suomimainostajat](https://github.com/harriko/suomimainostajat).

## UniFi Network lists

The lists are made for UniFi Network (11.0.81+ / UniFi OS 6.0.10+) dynamic
**Network Lists**. Each entry is in only one list.

| List | Type | Contents | Approx. size |
|---|---|---|---|
| `suomi_mainokset.txt` | Domain | Finnish ad and tracking domains (`list.txt` and `.fi` domains from the other lists) | 20 |
| `laitteet.txt` | Domain | Trackers built into devices and operating systems: LG webOS, Samsung, Amazon, Roku, Apple, Xiaomi, Huawei, Oppo/Realme, Vivo, TikTok, Microsoft (HaGeZi) | 3,000 |
| `mainokset.txt` | Domain | Ad and tracking domains (StevenBlack, Disconnect, Cameleon) | 27,600 |
| `windows_spy.txt` | Domain | Windows telemetry, extra services and Windows Update (WindowsSpyBlocker) | 430 |
| `windows_spy_ip.txt` | IP | Windows telemetry IP addresses (WindowsSpyBlocker) | 10 |
| `host.txt` | Domain | Malware, scams and spam (StevenBlack) | 18,600 |

The file names are Finnish: *suomi_mainokset* means Finnish ads, *laitteet*
devices and *mainokset* ads.

The sizes are from November 2026. Current numbers are in
[`unifi/lists/stats.json`](unifi/lists/stats.json). There is also `ip.txt` for
other IP addresses, but the sources currently have none.

List URLs for UniFi:

```
https://raw.githubusercontent.com/iiseppi/suomimainostajat/master/unifi/lists/suomi_mainokset.txt
https://raw.githubusercontent.com/iiseppi/suomimainostajat/master/unifi/lists/laitteet.txt
https://raw.githubusercontent.com/iiseppi/suomimainostajat/master/unifi/lists/mainokset.txt
https://raw.githubusercontent.com/iiseppi/suomimainostajat/master/unifi/lists/windows_spy.txt
https://raw.githubusercontent.com/iiseppi/suomimainostajat/master/unifi/lists/windows_spy_ip.txt
https://raw.githubusercontent.com/iiseppi/suomimainostajat/master/unifi/lists/host.txt
```

### Setup

1. **Networks → Network Lists → Create New**
2. Type: **Domain**, or **IP** for `windows_spy_ip.txt`
3. Source: **Dynamic**, with a URL from the list above
4. Refresh interval: **24 h**
5. Create a firewall policy that blocks traffic to the list:
   **Settings → Policy Table → Create New Policy**, Action **Block**, Source Zone
   **Internal**, Destination Zone **External**, with the list as the destination.
   In Network 10 the path is Settings → Policy Engine → Policy Table.

### Allowing a site (allowlist)

If a blocklist blocks a site you want to keep using, create an allowlist for it
and an Allow policy above the block policies. UniFi evaluates policies from top
to bottom, and the first matching policy wins. The example allows kernel.org.

1. **Create the allowlist.** Network Lists → Create New:
   * Name: `Allowlist`
   * Type: **Domain**
   * Source: entered by hand (not Dynamic)
   * Domains: `kernel.org` and `www.kernel.org`. Add each name separately,
     because the parent domain may not cover its subdomains.
2. **Create the allow policy.** Settings → Policy Table → Create New Policy:
   * Name: `Allow allowlist`
   * Action: **Allow**
   * Source Zone: **Internal**
   * Destination Zone: **External**, with the list `Allowlist` as the destination
3. **Create the block policies** if you don't have them yet: the same settings,
   but Action **Block** and a blocklist as the destination, for example
   `mainokset`.
4. **Order the policies.** Open the Zones view and select the zone pair
   Internal → External. Choose **Reorder** below the policy list and move
   `Allow allowlist` to the top.

The finished order for Internal → External:

| # | Policy | Action | Destination |
|---|---|---|---|
| 1 | Allow allowlist | Allow | `Allowlist` |
| 2 | Block ads | Block | `mainokset` |
| 3 | Block device tracking | Block | `laitteet` |
| … | Allow All Traffic (default) | Allow | any |

Notes:

* The allow policy allows the site's IP addresses completely. If a blocked
  domain uses the same address (on a CDN, for example), it gets through too.
* A page can load content from other domains as well. If the site still does
  not work, turn on **Flows Logging** in the block policy, check in Insights what
  is being blocked, and add the names you need to `Allowlist`.
* If your network has other internal zones (such as Hotspot or your own IoT
  zone), create the allow and block policies for each of them.
* Menu names vary between UniFi Network versions.

### Updates

* GitHub Actions rebuilds the lists every night at 02:23 UTC. A run also starts
  right away when `list.txt`, `cameleon.txt` or `unifi/build_lists.py` changes.
  A run takes about half an hour.
* Every run fetches the sources again and checks every entry. An entry is
  dropped if its domain does not resolve or none of its addresses answers HTTPS,
  HTTP or ping. If the server answers again later, the entry returns in the next
  run.
* If any list would shrink by more than 25% in one run, nothing is saved and the
  previous lists stay in use.
* UniFi fetches each list by itself at the refresh interval you chose.

### Things to know

* **Domain blocking can block other sites too.** UniFi blocks the domain's IP
  addresses. On CDNs (Cloudflare, Google, Azure, Akamai, CloudFront) ordinary
  sites share the same addresses. For ad blocking alone, a DNS-level blocker such
  as Pi-hole is more precise.
* `laitteet.txt` blocks vendor tracking for every device the policy covers. If a
  feature on some device stops working, exclude that device from the policy.
* `windows_spy.txt` also blocks Windows Update. Without an exception, Windows
  computers get no updates.
* Domain blocking only works if devices use the gateway as their DNS server.
* According to the community, the limit is about 100,000 entries per list and
  about 500,000 for all lists combined.

More details (in Finnish) are in [`unifi/README.md`](unifi/README.md).

## Other files

| File | Contents |
|---|---|
| [`list.txt`](list.txt) | Finnish ad and tracking domains, one per line. `suomi_mainokset.txt` is built from it. |
| [`hosts`](hosts) | The original project's file. Same content as `list.txt`. |
| [`cameleon.txt`](cameleon.txt) | Cameleon's hosts list (2018), one of the sources of `mainokset.txt`. |
| [`unifi/`](unifi) | The generator for the UniFi lists, and the built lists. |

`list.txt` also works as is as a Pi-hole blocklist:

```
https://raw.githubusercontent.com/iiseppi/suomimainostajat/master/list.txt
```

## Adding a domain

Add the domain to `list.txt` on its own line, without `http://` or a path. Once
the change is on master, the UniFi lists are rebuilt automatically.

## Sources

* [harriko/suomimainostajat](https://github.com/harriko/suomimainostajat)
* [HaGeZi DNS Blocklists](https://github.com/hagezi/dns-blocklists), native tracker lists
* [StevenBlack/hosts](https://github.com/StevenBlack/hosts)
* [crazy-max/WindowsSpyBlocker](https://github.com/crazy-max/WindowsSpyBlocker)
* [Disconnect](https://disconnect.me/), ad list `simple_ad.txt`
* Cameleon (`cameleon.txt`)

## Licenses

Each list follows the licenses of its sources. `laitteet.txt` is under GPL-3.0,
and `mainokset.txt` and `suomi_mainokset.txt` contain data that may only be used
non-commercially. The source licenses and details (in Finnish) are in
[`LICENSES/`](LICENSES/README.md).

## Privacy

This repository collects no data about the people who use the lists.

* The lists are plain text: one domain or IP address per line. They contain no
  scripts, cookies or anything else that could send data anywhere.
* The lists are built in GitHub Actions. The generator fetches the source lists,
  queries public DNS resolvers (Cloudflare, Google, Quad9) and tests the listed
  servers over HTTPS, HTTP and ping. It never connects to users' networks or
  devices.
* The README files contain no images or tracking pixels.
* When UniFi fetches a list, the request goes to GitHub
  (`raw.githubusercontent.com`). Like any web request, GitHub sees your
  network's public IP address and the time of the request, and handles them
  under its
  [privacy statement](https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement).
* GitHub's Traffic statistics show the repository maintainer only aggregate
  counts of page views and clones. They do not show who uses the lists.
* If you don't want GitHub to see your network's address, serve the lists from
  your own web server and give UniFi that URL.
