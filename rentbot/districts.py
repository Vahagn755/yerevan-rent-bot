"""Yerevan administrative districts: display names and text aliases for parsing."""

DISTRICTS: dict[str, dict] = {
    "ajapnyak": {"hy": "Աջափնյակ", "ru": "Аджапняк", "en": "Ajapnyak",
                 "aliases": ["աջափնյակ", "аджапняк", "ajapnyak"]},
    "arabkir": {"hy": "Արաբկիր", "ru": "Арабкир", "en": "Arabkir",
                "aliases": ["արաբկիր", "арабкир", "arabkir", "կոմիտաս", "комитас", "komitas"]},
    "avan": {"hy": "Ավան", "ru": "Аван", "en": "Avan",
             # "ավանդ" = deposit, "аванс" = advance payment
             "aliases": ["ավան(?!դ)", "аван(?!с)", "avan"]},
    "davtashen": {"hy": "Դավթաշեն", "ru": "Давташен", "en": "Davtashen",
                  "aliases": ["դավթաշեն", "давташен", "davtashen"]},
    "erebuni": {"hy": "Էրեբունի", "ru": "Эребуни", "en": "Erebuni",
                "aliases": ["էրեբունի", "эребуни", "erebuni"]},
    "kanaker": {"hy": "Քանաքեռ-Զեյթուն", "ru": "Канакер-Зейтун", "en": "Kanaker-Zeytun",
                "aliases": ["քանաքեռ", "канакер", "kanaker", "զեյթուն", "зейтун", "zeytun"]},
    "kentron": {"hy": "Կենտրոն", "ru": "Кентрон (центр)", "en": "Kentron (center)",
                "aliases": ["կենտրոն", "кентрон", "центр", "kentron", "city center", "center", "centre"]},
    "malatia": {"hy": "Մալաթիա-Սեբաստիա", "ru": "Малатия-Себастия", "en": "Malatia-Sebastia",
                "aliases": ["մալաթիա", "малатия", "malatia", "սեբաստիա", "себастия", "sebastia"]},
    "nor_nork": {"hy": "Նոր Նորք", "ru": "Нор-Норк", "en": "Nor Nork",
                 "aliases": ["նոր[ -]?նորք", "нор[ -]?норк", "nor[ -]?nork"]},
    "nork_marash": {"hy": "Նորք-Մարաշ", "ru": "Норк-Мараш", "en": "Nork-Marash",
                    "aliases": ["նորք[ -]?մարաշ", "норк[ -]?мараш", "nork[ -]?marash"]},
    "nubarashen": {"hy": "Նուբարաշեն", "ru": "Нубарашен", "en": "Nubarashen",
                   "aliases": ["նուբարաշեն", "нубарашен", "nubarashen"]},
    "shengavit": {"hy": "Շենգավիթ", "ru": "Шенгавит", "en": "Shengavit",
                  "aliases": ["շենգավիթ", "шенгавит", "shengavit"]},
}


def district_name(key: str | None, lang: str) -> str:
    if not key or key not in DISTRICTS:
        return "—"
    return DISTRICTS[key].get(lang) or DISTRICTS[key]["hy"]
