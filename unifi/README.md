# UniFi-listat

Itsestään päivittyvät estolistat UniFi Networkin (11.0.81+ / UniFi OS 6.0.10+)
dynaamisiksi **Network Lists** -listoiksi.

GitHub Actions ajaa `unifi/build_lists.py`:n joka yö ja aina kun `list.txt`, `cameleon.txt` tai skripti muuttuu. Skripti hakee lähdelistat, jakaa
jokaisen merkinnän yhteen kategoriaan ja poistaa merkinnät, jotka eivät vastaa
lainkaan. Muutokset tallentuvat `unifi/lists/`-kansioon.

## Listat

| Tiedosto | Tyyppi | Sisältö |
|---|---|---|
| `unifi/lists/windows_spy.txt` | Domain | WindowsSpyBlocker: spy, extra, update |
| `unifi/lists/windows_spy_ip.txt` | IP | WindowsSpyBlocker: firewall/spy |
| `unifi/lists/mainokset.txt` | Domain | Mainos- ja seurantadomainit (StevenBlackin mainososiot, Disconnect, Cameleon) |
| `unifi/lists/suomi_mainokset.txt` | Domain | suomimainostajat-lista ja muiden mainoslistojen `.fi`-domainit (paitsi ei-suomalaiset kuten simpli.fi) |
| `unifi/lists/laitteet.txt` | Domain | HaGeZin native tracker -listat: LG webOS, Samsung, Amazon, Roku, Apple, Xiaomi, Huawei, Oppo/Realme, Vivo, TikTok, Microsoft. GPL-3.0, katso [`LICENSES/`](../LICENSES/README.md) |
| `unifi/lists/host.txt` | Domain | Muut: haittaohjelmat, huijaukset, roskaposti (StevenBlackin muut osiot) |
| `unifi/lists/ip.txt` | IP | Muut IP:t (tällä hetkellä lähteissä ei ole yhtään) |

Jokainen merkintä on vain yhdessä listassa. Etusija on tässä järjestyksessä:
windows spy → suomi mainokset → laitteet → mainokset → host/ip.
HaGeZin domainit ovat vain `laitteet.txt`:ssä, jotta GPL-3.0-lisensoitu data ei
sekoitu muihin listoihin.

Ajon tilastot (kuinka moni merkintä jäi ja kuinka moni poistettiin ja miksi) ovat
tiedostossa `unifi/lists/stats.json`.

### Mitä "ei vastaa" tarkoittaa

* **Domain** poistetaan, jos kaksi eri nimipalvelinta (Cloudflare, Google, Quad9)
  vastaavat NXDOMAIN, SERVFAIL, ei A/AAAA-tietuetta tai pelkkä 0.0.0.0/127.0.0.1.
  Kyselyissä on CD-bitti, joten rikkinäinen DNSSEC ei yksinään pudota domainia.
  Jos nimipalvelimet eivät vastaa ollenkaan (aikakatkaisu), merkintä pidetään.
* **Ratkeava domain** poistetaan, jos mikään sen IPv4-osoitteista ei vastaa
  HTTPS:ään (443), HTTP:hen (80) eikä pingiin. Pelkän IPv6-osoitteen domainit
  pidetään, koska niitä ei voi testata ilman IPv6-yhteyttä.
* **IP** poistetaan, jos se ei vastaa HTTPS:ään, HTTP:hen eikä pingiin.
  Hylätty yhteys (RST) lasketaan vastaukseksi. GitHub Actionsissa ping ei toimi
  (Azure estää ICMP:n), joten siellä ratkaisevat HTTPS ja HTTP.
* Jos jokin lista kutistuisi yhdellä ajolla yli 25 %, ajo keskeytyy eikä mitään
  tallenneta. Tämä suojaa rikkinäiseltä lähteeltä tai verkkovialta.

## Käyttö UniFissa

1. **Networks → Network Lists → Create New**
2. Type: **Domain** (tai **IP** `*_ip.txt`-tiedostoille)
3. Source: **Dynamic**, ja URL esimerkiksi
   `https://raw.githubusercontent.com/iiseppi/suomimainostajat/master/unifi/lists/mainokset.txt`
4. Päivitysväli: 24 h
5. Tee palomuurisääntö (Policy Engine / Zone-Based Firewall), joka estää liikenteen
   tähän listaan.

## Huomioitavaa

* **Domain-listat estävät IP-osoitteita.** UniFi selvittää domainin IP:t ja estää
  ne. CDN-palveluissa (Cloudflare, Google, Azure, Akamai, CloudFront) samaa IP:tä
  käyttävät myös tavalliset sivustot, joten ne voivat estyä samalla. Otoksen
  perusteella (marraskuu 2026) jaetuissa CDN/pilvi-osoitteissa on noin 23 %
  `mainokset.txt`:n ja noin 57 % `windows_spy.txt`:n domaineista.
* Domain-esto toimii vain, jos laitteet käyttävät gatewaytä nimipalvelimenaan.
* Yhteisön mukaan yhden listan raja on noin 100 000 merkintää ja kaikkien listojen
  yhteensä noin 500 000. Ubiquiti ei ole julkaissut virallisia rajoja.
* UniFi Network listat on tehty palomuuria varten. DNS-tason esto (UniFin
  Content Filter tai Pi-hole) ei aiheuta CDN-sivuvaikutuksia. Content Filterin
  käyttöönotto on etusivun [README:ssä](../README.md#esto-unifin-nimipalvelimella-content-filter).

## Paikallinen ajo

```bash
python3 -I unifi/build_lists.py --out unifi/lists
```

Vain Pythonin vakiokirjasto, Python 3.9+.
