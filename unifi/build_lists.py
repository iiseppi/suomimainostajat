#!/usr/bin/env python3
"""Build UniFi Network (11.0.81+) dynamic Network Lists from public blocklists.

Fetches the sources, puts every entry into exactly one category, drops domains
that no longer resolve and IPs that do not answer at all, and writes plain
lists (one entry per line, no comments) that UniFi can load from a URL.

Category priority: windows_spy > suomi_mainokset > laitteet > mainokset > host / ip

Only the Python standard library is used.
"""
import argparse
import asyncio
import ipaddress
import json
import random
import re
import shutil
import socket
import struct
import subprocess
import sys
import time
import urllib.request
from collections import Counter, defaultdict, deque
from pathlib import Path

# --------------------------------------------------------------------------
# Sources
# kind: hosts = "0.0.0.0 domain" lines, plain = one entry per line
# --------------------------------------------------------------------------
WSB = "https://raw.githubusercontent.com/crazy-max/WindowsSpyBlocker/refs/heads/master/data"
SOURCES = [
    ("stevenblack", "hosts", "https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts"),
    ("wsb_firewall_spy", "plain", f"{WSB}/firewall/spy.txt"),
    ("wsb_spy", "hosts", f"{WSB}/hosts/spy.txt"),
    ("wsb_extra", "hosts", f"{WSB}/hosts/extra.txt"),
    ("wsb_extra_v6", "hosts", f"{WSB}/hosts/extra_v6.txt"),
    ("wsb_update", "hosts", f"{WSB}/hosts/update.txt"),
    ("wsb_update_v6", "hosts", f"{WSB}/hosts/update_v6.txt"),
    ("cameleon", "hosts", "https://raw.githubusercontent.com/iiseppi/suomimainostajat/refs/heads/master/cameleon.txt"),
    ("suomi_list", "plain", "https://raw.githubusercontent.com/iiseppi/suomimainostajat/refs/heads/master/list.txt"),
    ("disconnect_ad", "plain", "https://s3.amazonaws.com/lists.disconnect.me/simple_ad.txt"),
]
# HaGeZi native tracker lists (GPL-3.0): trackers built into devices, apps and
# operating systems. They go to their own list (laitteet.txt), so device tracking
# can be blocked separately from ads. The "-onlydomains" files are plain names;
# the other files use "*.domain" wildcards, which UniFi cannot resolve.
HAGEZI = "https://raw.githubusercontent.com/hagezi/dns-blocklists/main/wildcard"
HAGEZI_NATIVE = ["lgwebos", "samsung", "amazon", "roku", "apple", "xiaomi", "huawei",
                 "oppo-realme", "vivo", "tiktok", "winoffice"]
SOURCES += [(f"hagezi_{n}", "plain", f"{HAGEZI}/native.{n}-onlydomains.txt") for n in HAGEZI_NATIVE]

# StevenBlack sections ("# Start <name>") that are about ads and tracking.
# Everything else in StevenBlack (malware, scam, spam, dead...) goes to "host",
# except the mixed "StevenBlack" section, where the keyword test below decides.
SB_AD_SECTIONS = {"adaway.org", "add.2o7Net", "hostsVN", "mvps.org", "someonewhocares.org",
                  "tiuxo", "UncheckyAds", "yoyo.org"}
AD_SOURCES = {"cameleon", "disconnect_ad"}
# .fi domains of companies that are not Finnish (domain hacks like simpli.fi)
NOT_FINNISH_FI = ("simpli.fi",)

AD_KEYWORDS = re.compile(
    r"(^|[.\-_])(ads?|adv|adserv\w*|advert\w*|advertising|adsystem|adserver|banners?|"
    r"track\w*|analytics?|metrics?|stats?|statistics|pixel|telemetry|beacons?|counter|"
    r"clicks?|affiliates?|popunder\w*|popups?|rtb|bidder|tagmanager)([.\-_0-9]|$)"
    r"|doubleclick|googlesyndication|googleadservices|adnxs|taboola|outbrain|criteo|"
    r"adform|smartadserver|appsflyer|adjust\.com|mopub|unityads|applovin|vungle|"
    r"chartboost|inmobi|adcolony|pubmatic|rubiconproject|openx|casalemedia|moatads|"
    r"scorecardresearch|quantserve|hotjar|mixpanel|amplitude|omtrdc|2o7\.net|demdex|"
    r"everesttech|adsrvr|bidswitch|admob|adtech|adsafeprotected|doubleverify|"
    r"exoclick|propellerads|popads|adcash|juicyads|trafficjunky|ero-advertising|"
    r"yieldmo|sharethrough|teads|smaato|startapp|tapjoy|fyber|ironsrc|branch\.io|"
    r"kochava|localytics|crashlytics|datatrics|meetrics|heytapmobile|adx\.")

# Output files: category -> (file name, entry kind)
OUTPUTS = {
    "windows_spy": ("windows_spy.txt", "domain"),
    "windows_spy_ip": ("windows_spy_ip.txt", "ip"),
    "mainokset": ("mainokset.txt", "domain"),
    "suomi_mainokset": ("suomi_mainokset.txt", "domain"),
    "laitteet": ("laitteet.txt", "domain"),
    "host": ("host.txt", "domain"),
    "ip": ("ip.txt", "ip"),
}

UNIFI_LIST_LIMIT = 100_000  # community-reported per-list cap

SKIP = {"localhost", "localhost.localdomain", "local", "broadcasthost", "ip6-localhost",
        "ip6-loopback", "ip6-localnet", "ip6-mcastprefix", "ip6-allnodes", "ip6-allrouters",
        "ip6-allhosts", "0.0.0.0"}
HOST_RE = re.compile(r"^(?=.{1,253}$)([a-z0-9_]([a-z0-9_-]{0,61}[a-z0-9_])?\.)+[a-z0-9-]{2,63}$")


def log(*args):
    print(time.strftime("%H:%M:%S"), *args, flush=True)


# --------------------------------------------------------------------------
# Fetch and parse
# --------------------------------------------------------------------------
# Sources that live in this repository are read from the checkout, so edits to
# them are used right away instead of after raw.githubusercontent.com caching.
LOCAL_FILES = {"cameleon": "cameleon.txt", "suomi_list": "list.txt"}
REPO_ROOT = Path(__file__).resolve().parent.parent


def fetch(url, cache_dir, name):
    local = LOCAL_FILES.get(name)
    if local and (REPO_ROOT / local).is_file():
        return (REPO_ROOT / local).read_text(encoding="utf-8", errors="replace")
    if cache_dir:
        cached = Path(cache_dir) / f"{name}.txt"
        if cached.exists():
            return cached.read_text(encoding="utf-8", errors="replace")
    req = urllib.request.Request(url, headers={"User-Agent": "unifi-listat/1.0"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                text = resp.read().decode("utf-8", errors="replace")
            if cache_dir:
                (Path(cache_dir) / f"{name}.txt").write_text(text, encoding="utf-8")
            return text
        except OSError as exc:
            log(f"fetch {name} failed ({exc}), attempt {attempt + 1}/3")
            time.sleep(5)
    raise SystemExit(f"could not fetch {name}: {url}")


def normalize(token):
    """Return ('ip'|'domain', value) or None."""
    token = token.strip().lower().rstrip(".")
    if not token or token in SKIP:
        return None
    try:
        return "ip", str(ipaddress.ip_address(token))
    except ValueError:
        pass
    if "/" in token:
        try:
            return "ip", str(ipaddress.ip_network(token, strict=False))
        except ValueError:
            return None  # URL paths etc. cannot be used in UniFi lists
    if HOST_RE.match(token):
        return "domain", token
    return None


def parse_source(name, kind, text, entries, dropped):
    section = None
    for line in text.splitlines():
        if name == "stevenblack":
            m = re.match(r"^# Start (.+)$", line)
            if m:
                section = m.group(1).strip()
                continue
            if line.startswith("# End "):
                section = None
                continue
        body = line.split("#", 1)[0].split()
        if not body:
            continue
        tokens = body[1:] if kind == "hosts" else body
        if kind == "hosts" and len(body) == 1:
            tokens = body  # tolerate bare domains in hosts files
        tag = f"sb:{section}" if name == "stevenblack" else name.replace("_v6", "")
        if name == "stevenblack" and not section:
            continue  # header block (localhost etc.)
        for tok in tokens:
            res = normalize(tok)
            if res:
                entries[res].add(tag)
            else:
                t = tok.strip().lower()
                if t and t not in SKIP and not t.startswith(("0.0.0.0", "127.", "::")):
                    dropped[name].append(t)


def categorize(kind, value, tags):
    if any(t.startswith("wsb") for t in tags):
        return "windows_spy_ip" if kind == "ip" else "windows_spy"
    if "suomi_list" in tags:
        return "suomi_mainokset"
    if any(t.startswith("hagezi_") for t in tags):
        return "ip" if kind == "ip" else "laitteet"
    is_ad = any(t in AD_SOURCES or (t.startswith("sb:") and t[3:] in SB_AD_SECTIONS) for t in tags)
    if not is_ad and kind == "domain" and "sb:StevenBlack" in tags and AD_KEYWORDS.search(value):
        is_ad = True
    if is_ad:
        if kind == "ip":
            return "ip"
        finnish = value.endswith(".fi") and not any(
            value == d or value.endswith("." + d) for d in NOT_FINNISH_FI)
        return "suomi_mainokset" if finnish else "mainokset"
    return "ip" if kind == "ip" else "host"


# --------------------------------------------------------------------------
# DNS check (raw UDP to public resolvers, so local filtering does not matter)
# --------------------------------------------------------------------------
# Unfiltered public resolvers. Each provider is paced separately and slows down
# on its own when it starts dropping queries (rate limiting).
PROVIDERS = {
    "cloudflare": ["1.1.1.1", "1.0.0.1"],
    "google": ["8.8.8.8", "8.8.4.4"],
    "quad9": ["9.9.9.10", "149.112.112.10"],  # .10 = no malware filtering
}
DEAD = {"nxdomain", "servfail", "nodata", "sinkhole"}


def build_query(qid, name, qtype):
    header = struct.pack(">HHHHHH", qid, 0x0110, 1, 0, 0, 0)  # RD + CD
    qname = b"".join(bytes([len(p)]) + p.encode("ascii") for p in name.split(".")) + b"\x00"
    return header + qname + struct.pack(">HH", qtype, 1)


def skip_name(data, off):
    while True:
        length = data[off]
        if length == 0:
            return off + 1
        if length & 0xC0 == 0xC0:
            return off + 2
        off += 1 + length


def parse_response(data):
    _, flags, qd, an, _, _ = struct.unpack(">HHHHHH", data[:12])
    rcode, truncated = flags & 0xF, bool(flags & 0x200)
    off = 12
    for _ in range(qd):
        off = skip_name(data, off) + 4
    ips = []
    try:
        for _ in range(an):
            off = skip_name(data, off)
            rtype, _, _, rdlen = struct.unpack(">HHIH", data[off:off + 10])
            off += 10
            rdata = data[off:off + rdlen]
            off += rdlen
            if rtype == 1 and rdlen == 4:
                ips.append(socket.inet_ntop(socket.AF_INET, rdata))
            elif rtype == 28 and rdlen == 16:
                ips.append(socket.inet_ntop(socket.AF_INET6, rdata))
    except (struct.error, IndexError):
        truncated = True
    return rcode, ips, truncated


def usable_v4(ips):
    out = []
    for ip in ips:
        addr = ipaddress.ip_address(ip)
        if addr.version == 4 and not (addr.is_unspecified or addr.is_loopback):
            out.append(ip)
    return out


def usable(ips):
    for ip in ips:
        addr = ipaddress.ip_address(ip)
        if not (addr.is_unspecified or addr.is_loopback):
            return True
    return False


class DnsSocket(asyncio.DatagramProtocol):
    def __init__(self):
        self.pending = {}
        self.transport = None

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        if len(data) < 12:
            return
        qid = struct.unpack(">H", data[:2])[0]
        fut = self.pending.pop(qid, None)
        if fut and not fut.done():
            fut.set_result(data)

    def error_received(self, exc):
        pass


class Provider:
    """Paces queries to one provider and adapts the rate to its drop rate."""

    WINDOW = 200

    def __init__(self, name, servers, qps):
        self.name = name
        self.servers = servers
        self.qps = qps
        self.max_qps = qps
        self.next_slot = 0.0
        self.results = deque(maxlen=self.WINDOW)
        self.socks = []
        self.turn = 0

    async def start(self):
        loop = asyncio.get_running_loop()
        for ip in self.servers:
            _, proto = await loop.create_datagram_endpoint(DnsSocket, remote_addr=(ip, 53))
            self.socks.append(proto)

    async def pace(self):
        loop = asyncio.get_running_loop()
        now = loop.time()
        if self.next_slot < now:
            self.next_slot = now
        wait = self.next_slot - now
        self.next_slot += 1.0 / self.qps
        if wait > 0:
            await asyncio.sleep(wait)

    def record(self, answered):
        self.results.append(answered)
        if len(self.results) < self.WINDOW:
            return
        drop = self.results.count(False) / self.WINDOW
        if drop > 0.15:
            self.qps = max(10.0, self.qps / 2)
            self.results.clear()
            # back off: push the next slot a little into the future
            self.next_slot = asyncio.get_running_loop().time() + 2.0
        elif drop < 0.02 and self.qps < self.max_qps:
            self.qps = min(self.max_qps, self.qps * 1.25)
            self.results.clear()


class Resolver:
    def __init__(self, qps_per_provider, timeout):
        self.timeout = timeout
        self.providers = [Provider(n, s, qps_per_provider) for n, s in PROVIDERS.items()]

    async def start(self):
        for prov in self.providers:
            await prov.start()

    def rates(self):
        return " ".join(f"{p.name}={p.qps:.0f}/s" for p in self.providers)

    async def query(self, prov, name, qtype):
        await prov.pace()
        proto = prov.socks[prov.turn % len(prov.socks)]
        prov.turn += 1
        qid = random.randrange(65536)
        while qid in proto.pending:
            qid = random.randrange(65536)
        fut = asyncio.get_running_loop().create_future()
        proto.pending[qid] = fut
        proto.transport.sendto(build_query(qid, name, qtype))
        try:
            data = await asyncio.wait_for(fut, self.timeout)
        except asyncio.TimeoutError:
            proto.pending.pop(qid, None)
            prov.record(False)
            return None
        prov.record(True)
        return parse_response(data)

    async def check(self, name):
        """Return (status, ipv4s). status: alive | nxdomain | servfail | nodata |
        sinkhole | unknown.

        Alive as soon as one provider returns a usable address. Dead only when
        two different providers both give a dead answer."""
        verdicts = {}
        tries = Counter()
        for _ in range(3 * len(self.providers)):
            # least-tried provider first, then the one with the shortest queue
            cands = [p for p in self.providers if p.name not in verdicts]
            prov = min(cands, key=lambda p: (tries[p.name], p.next_slot))
            tries[prov.name] += 1
            res = await self.query(prov, name, 1)
            if res is None:
                continue
            rcode, ips, truncated = res
            if rcode == 0:
                if truncated or usable(ips):
                    return "alive", usable_v4(ips)
                verdict = "sinkhole" if ips else "nodata"
                if not ips:
                    res6 = await self.query(prov, name, 28)
                    if res6 and res6[0] == 0 and (res6[2] or usable(res6[1])):
                        return "alive", []  # IPv6 only: cannot be tested here
            elif rcode == 3:
                verdict = "nxdomain"
            else:
                verdict = "servfail"
            verdicts[prov.name] = verdict
            if len(verdicts) == 2:
                return next(iter(verdicts.values())), []
        return "unknown", []


async def check_domains(domains, qps, concurrency, timeout, passes=3):
    results = {}
    addrs = {}
    todo = list(domains)
    for n in range(1, passes + 1):
        if not todo:
            break
        resolver = Resolver(qps / len(PROVIDERS), timeout)
        await resolver.start()
        sem = asyncio.Semaphore(concurrency)
        done = 0
        total = len(todo)

        async def one(name):
            nonlocal done
            async with sem:
                results[name], addrs[name] = await resolver.check(name)
            done += 1
            if done % 10000 == 0 or done == total:
                c = Counter(results[d] for d in todo if d in results)
                log(f"DNS pass {n}: {done}/{total}  [{resolver.rates()}]  " +
                    "  ".join(f"{k}={v}" for k, v in sorted(c.items())))

        await asyncio.gather(*(one(d) for d in todo))
        todo = [d for d in todo if results[d] == "unknown"]
        # slower and more patient on each retry pass
        qps, concurrency, timeout = qps / 2, max(50, concurrency // 2), timeout * 1.5
    return results, addrs


# --------------------------------------------------------------------------
# IP check: TCP 443/80 (a refused connection is an answer) + ICMP if fping exists
# --------------------------------------------------------------------------
async def tcp_answers(ip, port, timeout):
    try:
        _, writer = await asyncio.wait_for(asyncio.open_connection(ip, port), timeout)
        writer.close()
        return True
    except ConnectionRefusedError:
        return True
    except (OSError, asyncio.TimeoutError):
        return False


def icmp_alive(ips):
    fping = shutil.which("fping")
    if not fping or not ips:
        return set()
    proc = subprocess.run([fping, "-a", "-q", "-r", "2", "-t", "1000"], input="\n".join(ips),
                          capture_output=True, text=True)
    return set(proc.stdout.split())


async def tcp_pass(ips, results, concurrency, timeout, label):
    """One TCP pass over ips; sets results[ip] to alive / no_answer."""
    sem = asyncio.Semaphore(concurrency)
    done = 0

    async def one(ip):
        nonlocal done
        async with sem:
            hits = await asyncio.gather(tcp_answers(ip, 443, timeout),
                                        tcp_answers(ip, 80, timeout))
        results[ip] = "alive" if any(hits) else "no_answer"
        done += 1
        if done % 5000 == 0:
            log(f"TCP {label}: {done}/{len(ips)}")

    await asyncio.gather(*(one(ip) for ip in ips))
    return [ip for ip in ips if results[ip] == "no_answer"]


async def check_ips(values):
    """alive if the address answers HTTPS (443), HTTP (80) or ping.

    Too many parallel connection attempts make NAT gateways and IPS drop SYNs,
    which looks like "no answer". So: a moderate first pass, then a slow and
    patient second pass for everything that stayed silent."""
    singles = [v for v in values if "/" not in v]
    results = {v: "alive" for v in values if "/" in v}  # networks are kept as is
    silent = await tcp_pass(singles, results, 200, 4.0, "pass 1")
    log(f"TCP pass 1: {len(singles) - len(silent)}/{len(singles)} answer")
    silent2 = await tcp_pass(silent, results, 30, 6.0, "pass 2")
    log(f"TCP pass 2: {len(silent) - len(silent2)}/{len(silent)} more answer")
    pinged = icmp_alive(silent2)
    for ip in pinged:
        results[ip] = "alive"
    log(f"IP check: {len(singles)} addresses, {len(silent2)} silent on 443/80, "
        f"{len(pinged)} of those answer ping")
    return results


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default="lists", help="output directory")
    ap.add_argument("--cache", help="reuse/store downloaded sources here")
    ap.add_argument("--qps", type=float, default=600,
                    help="DNS queries per second in total (split between providers)")
    ap.add_argument("--concurrency", type=int, default=400)
    ap.add_argument("--timeout", type=float, default=2.5)
    ap.add_argument("--max-shrink", type=float, default=0.25,
                    help="refuse to write a list that shrinks more than this fraction")
    ap.add_argument("--force", action="store_true", help="write even if a list shrinks a lot")
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    if args.cache:
        Path(args.cache).mkdir(parents=True, exist_ok=True)

    entries = defaultdict(set)
    dropped = defaultdict(list)
    for name, kind, url in SOURCES:
        text = fetch(url, args.cache, name)
        parse_source(name, kind, text, entries, dropped)
        log(f"source {name}: ok")
    for name, toks in dropped.items():
        log(f"unusable entries in {name} ({len(toks)}): {toks[:5]}")

    cats = {key: categorize(key[0], key[1], tags) for key, tags in entries.items()}
    log(f"unique entries: {len(entries)}  " +
        "  ".join(f"{k}={v}" for k, v in sorted(Counter(cats.values()).items())))

    domains = sorted(v for (k, v) in entries if k == "domain")
    ips = sorted(v for (k, v) in entries if k == "ip")
    t0 = time.time()
    dns, addrs = asyncio.run(check_domains(domains, args.qps, args.concurrency, args.timeout))
    log(f"DNS done in {time.time() - t0:.0f}s")
    # Resolving is not enough: one of the addresses must answer HTTPS, HTTP or ping.
    to_test = set(ips)
    for d, st in dns.items():
        if st == "alive":
            to_test.update(addrs[d][:2])
    ipres = asyncio.run(check_ips(sorted(to_test)))
    for d, st in dns.items():
        if st == "alive" and addrs[d] and not any(ipres[a] == "alive" for a in addrs[d][:2]):
            dns[d] = "no_answer"
    log(f"checks done in {time.time() - t0:.0f}s")

    unknown = sum(1 for v in dns.values() if v == "unknown")
    if domains and unknown / len(domains) > 0.05:
        raise SystemExit(f"too many unanswered DNS queries ({unknown}), network problem? not writing")

    status = {}
    for key in entries:
        status[key] = dns[key[1]] if key[0] == "domain" else ipres[key[1]]

    stats = {"updated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "lists": {}}
    new_lists = {}
    for cat, (fname, _) in OUTPUTS.items():
        keys = [k for k, c in cats.items() if c == cat]
        kept = sorted(k[1] for k in keys if status[k] not in DEAD and status[k] != "no_answer")
        removed = Counter(status[k] for k in keys if status[k] in DEAD or status[k] == "no_answer")
        new_lists[cat] = kept
        stats["lists"][fname] = {"entries": len(kept), "source_entries": len(keys),
                                 "removed": dict(sorted(removed.items()))}
        if len(kept) > UNIFI_LIST_LIMIT:
            log(f"WARNING {fname}: {len(kept)} entries exceeds UniFi list cap {UNIFI_LIST_LIMIT}")

    # Safety: a sudden big shrink usually means a broken source or network.
    problems = []
    for cat, (fname, _) in OUTPUTS.items():
        old = out / fname
        if old.exists():
            old_n = sum(1 for line in old.read_text().splitlines() if line.strip())
            new_n = len(new_lists[cat])
            if old_n >= 50 and new_n < old_n * (1 - args.max_shrink):
                problems.append(f"{fname}: {old_n} -> {new_n}")
    if problems and not args.force:
        raise SystemExit("lists shrank too much, not writing: " + "; ".join(problems))

    for cat, (fname, _) in OUTPUTS.items():
        body = "\n".join(new_lists[cat])
        (out / fname).write_text(body + "\n" if body else "", encoding="utf-8")
    (out / "stats.json").write_text(json.dumps(stats, indent=2, ensure_ascii=False) + "\n")

    for fname, s in stats["lists"].items():
        log(f"{fname}: {s['entries']} kept of {s['source_entries']}  removed={s['removed']}")


if __name__ == "__main__":
    sys.exit(main())
