# suomimainostajat

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
kernel.org

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
  DNS-tason estäjä, kuten Pi-hole tai AdGuard Home, on tarkempi.
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

`list.txt` käy sellaisenaan myös Pi-holen ja AdGuard Homen estolistaksi:

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
