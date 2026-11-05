"""Short, defensive cybersecurity learning cards; nothing here runs commands."""

LESSONS = {
    "fundamentals": (
        "Cybersecurity basics: keep software updated, use unique passwords with "
        "a password manager, enable MFA, back up important data, and verify "
        "links before opening them. Keep antivirus, Defender, and firewall "
        "protections enabled."
    ),
    "linux": (
        "Kali/Linux command basics (sirf explanation; Aaru commands run nahi "
        "karti): `pwd` current folder dikhata hai; `ls` files list karta hai; "
        "`cd <folder>` folder badalta hai; `whoami` username aur `id` user/group "
        "IDs dikhate hain; `ip addr` apne device ke network interfaces dikhata "
        "hai; `man <command>` manual kholta hai. `sudo su` sudo permission "
        "hone par root (administrator) shell kholta hai. Configuration ke "
        "hisab se yeh aapka password maang sakta hai ya cached sudo login use "
        "kar sakta hai. Jab tak aap `exit` type karke root shell se bahar nahi "
        "aate, commands system-wide changes kar sakti hain; galti se system ya "
        "data ko nuksan ho sakta hai. Jahan "
        "theek ho, poore root shell ke bajay `sudo <one-needed-command>` use "
        "karein; command pehle samjhein aur unknown source se copy-paste na "
        "karein. Kali sirf apne systems ya authorized labs par use karein."
    ),
    "networking": (
        "Networking basics: an IP address identifies a network interface, a "
        "router forwards traffic, DNS maps names to addresses, and HTTPS "
        "encrypts a connection to a website."
    ),
    "nmap": (
        "Nmap is a network inventory and diagnostics tool. Learn it only in a "
        "lab you own or have explicit written permission to test; never scan "
        "public, school, workplace, Wi-Fi, or third-party networks without "
        "authorization. Aaru does not run scans."
    ),
    "wireshark": (
        "Wireshark captures and displays network packets. Use it only on a "
        "network and traffic you are authorized to inspect; packet captures "
        "can contain personal data and credentials."
    ),
    "wifi": (
        "Protect your Wi-Fi with WPA2-AES or WPA3, a unique router-admin "
        "password, current router firmware, and a guest network for visitors. "
        "Do not test networks without the owner's permission."
    ),
    "cctv": (
        "CCTV safety: change default credentials, install firmware updates, "
        "limit remote access, enable MFA where available, and review access "
        "logs. Only administer cameras you own or are authorized to manage."
    ),
    "passwords": (
        "Use a different, long password for every account. A reputable "
        "password manager and multi-factor authentication reduce the impact "
        "of password reuse and phishing."
    ),
    "privacy": (
        "Privacy tips: review app permissions, share less personal data, use "
        "MFA, check browser privacy settings, and do not open unexpected "
        "attachments or sign-in links."
    ),
    "labs": (
        "Practice in intentionally vulnerable local labs such as OWASP Juice "
        "Shop or WebGoat, isolated from public networks. Follow the lab's "
        "scope and do not test real accounts or devices."
    ),
}


def get_lesson(topic):
    key = topic.strip().lower().replace("-", " ").replace("_", " ")
    aliases = {
        "cybersecurity": "fundamentals",
        "security": "fundamentals",
        "ethical hacking": "labs",
        "authorized lab": "labs",
        "network": "networking",
        "wifi security": "wifi",
        "password safety": "passwords",
        "online privacy": "privacy",
        "cctv security": "cctv",
        "n map": "nmap",
    }
    key = aliases.get(key, key)
    return LESSONS.get(
        key,
        "Available defensive lessons: fundamentals, Linux, networking, Nmap, "
        "Wireshark, Wi-Fi, CCTV, passwords, privacy, and authorized labs.",
    )
