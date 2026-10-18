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


# Streets, squares and metro stations that clearly belong to one district.
# Used only when the post does not name the district itself. Streets that run across
# several districts (Baghramyan, Tigran Mets, Isakov…) are left out on purpose.
STREETS: dict[str, list[str]] = {
    "kentron": [
        "աբովյան", "ամիրյան", "մաշտոց", "սայաթ-նովա", "թումանյան", "պուշկին", "տերյան", "նալբանդյան",
        "կողբացի", "սարյան", "իսահակյան", "բուզանդ", "հյուսիսային պող", "հանրապետության հրապարակ",
        "կասկադ", "խանջյան", "խորենացի", "պարպեցի", "վարդանանց", "մոսկովյան", "լալայանց", "երիտասարդական",
        "абовян", "амирян", "маштоц", "саят-нов", "туманян", "пушкин", "терян", "налбандян", "когбаци",
        "сарьян", "исаакян", "бузанд", "северн\\w* проспект", "площад\\w* республики", "каскад", "ханджян",
        "хоренаци", "парпеци", "вардананц", "московян", "лалаянц", "еритасардакан",
        "abovyan", "amiryan", "mashtots", "sayat[- ]nova", "tumanyan", "pushkin", "teryan", "nalbandyan",
        "koghbatsi", "saryan", "isahakyan", "buzand", "northern avenue", "republic square", "cascade",
        "khanjyan", "khorenatsi", "parpetsi", "vardanants", "moskovyan", "lalayants", "yeritasardakan",
    ],
    "arabkir": [
        "կիևյան", "մամիկոնյանց", "գյուլբենկյան", "քոչար", "վաղարշյան", "ազատության", "բարեկամություն", "կասյան",
        "киевян", "мамиконянц", "гюльбенкян", "кочар", "вагаршян", "азатутян", "барекамутюн", "касьян",
        "kievyan", "mamikonyants", "g[yu]+lbenkyan", "kochar", "vagharshyan", "azatutyan", "barekamutyun", "kasyan",
    ],
    "ajapnyak": [
        "հալաբյան", "նազարբեկյան", "լվովյան", "սիլիկյան",
        "[гх]алабян", "назарбекян", "львовян", "силикян",
        "halabyan", "nazarbekyan", "lvovyan", "silikyan",
    ],
    "avan": ["աճառյան", "ачарян", "acharyan"],
    "kanaker": ["սևակ", "севак", "sevak"],
    "nor_nork": ["մոլդովական", "молдовакан", "moldovakan", "գայի պող", "гая(?!н)", "gai ave"],
    "shengavit": ["բագրատունյաց", "նժդեհ", "չարբախ", "багратуняц", "нжде", "чарбах",
                  "bagratunyats", "nzhdeh", "charbakh"],
    "erebuni": ["արտաշիսյան", "նոր արեշ", "վարդաշեն", "սասունցի", "арташисян", "нор[- ]ареш", "вардашен",
                "сасунци", "artashisyan", "nor aresh", "vardashen", "sasuntsi"],
    "malatia": ["րաֆֆի", "раффи", "raffi"],
}
