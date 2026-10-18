"""All user-facing strings in Armenian (hy), Russian (ru) and English (en)."""

LANGS = ("hy", "ru", "en")

T: dict[str, dict[str, str]] = {
    "welcome": {
        "hy": "Բարև, {name} 👋\n\nԵս օգնում եմ գտնել վարձով բնակարան Երևանում։\n\n"
              "1️⃣ Կարգավորիր ֆիլտրը՝ գին, սենյակներ, թաղամաս\n"
              "2️⃣ Ես կուղարկեմ միայն համապատասխան նոր հայտարարությունները\n"
              "3️⃣ Միջնորդ կամ խաբեբա տեսնե՞ս՝ սեղմիր կոճակը։ 3 բողոքից հետո համարը սև ցուցակ է ընկնում\n\n"
              "Տանտե՞ր ես՝ տեղադրիր հայտարարությունդ անվճար։",
        "ru": "Привет, {name} 👋\n\nЯ помогаю найти квартиру в аренду в Ереване.\n\n"
              "1️⃣ Настрой фильтр: цена, комнаты, район\n"
              "2️⃣ Я буду присылать только подходящие новые объявления\n"
              "3️⃣ Увидел посредника или мошенника — нажми кнопку. После 3 жалоб номер попадает в чёрный список\n\n"
              "Сдаёшь квартиру? Размести объявление бесплатно.",
        "en": "Hi, {name} 👋\n\nI help you find a rental apartment in Yerevan.\n\n"
              "1️⃣ Set your filter: price, rooms, district\n"
              "2️⃣ I'll send you only matching new listings\n"
              "3️⃣ Spot an agent or a scammer? Tap the button. After 3 reports the number is blacklisted\n\n"
              "A landlord? Post your listing for free.",
    },
    "help": {
        "hy": "<b>Հրամաններ</b>\n/filter — ֆիլտրի կարգավորում\n/post — տեղադրել հայտարարություն\n"
              "/my — իմ հայտարարությունները\n/pause, /resume — անջատել/միացնել ծանուցումները\n"
              "/lang — լեզու\n/cancel — չեղարկել",
        "ru": "<b>Команды</b>\n/filter — настроить фильтр\n/post — разместить объявление\n"
              "/my — мои объявления\n/pause, /resume — выкл/вкл уведомления\n"
              "/lang — язык\n/cancel — отмена",
        "en": "<b>Commands</b>\n/filter — set your filter\n/post — post a listing\n"
              "/my — my listings\n/pause, /resume — notifications off/on\n"
              "/lang — language\n/cancel — cancel",
    },
    # main menu
    "btn_filter": {"hy": "🔎 Իմ ֆիլտրը", "ru": "🔎 Мой фильтр", "en": "🔎 My filter"},
    "btn_post": {"hy": "➕ Տեղադրել", "ru": "➕ Разместить", "en": "➕ Post listing"},
    "btn_my": {"hy": "📋 Իմ հայտարարությունները", "ru": "📋 Мои объявления", "en": "📋 My listings"},
    "btn_pause": {"hy": "⏸ Դադար", "ru": "⏸ Пауза", "en": "⏸ Pause"},
    "btn_resume": {"hy": "▶️ Վերսկսել", "ru": "▶️ Продолжить", "en": "▶️ Resume"},
    "btn_lang": {"hy": "🌐 Լեզու", "ru": "🌐 Язык", "en": "🌐 Language"},
    "choose_lang": {k: "Ընտրեք լեզուն / Выберите язык / Choose language" for k in LANGS},
    "lang_set": {"hy": "Լեզուն փոխված է ✅", "ru": "Язык изменён ✅", "en": "Language updated ✅"},
    "paused": {"hy": "⏸ Ծանուցումները դադարեցված են։", "ru": "⏸ Уведомления на паузе.",
               "en": "⏸ Notifications paused."},
    "resumed": {"hy": "▶️ Ծանուցումները միացված են։", "ru": "▶️ Уведомления включены.",
                "en": "▶️ Notifications resumed."},
    "cancel": {"hy": "❌ Չեղարկել", "ru": "❌ Отмена", "en": "❌ Cancel"},
    "cancelled": {"hy": "Չեղարկված է։", "ru": "Отменено.", "en": "Cancelled."},
    "back": {"hy": "⬅️ Հետ", "ru": "⬅️ Назад", "en": "⬅️ Back"},
    "yes": {"hy": "✅ Այո", "ru": "✅ Да", "en": "✅ Yes"},
    "no": {"hy": "❌ Ոչ", "ru": "❌ Нет", "en": "❌ No"},
    "skip": {"hy": "Բաց թողնել ➡️", "ru": "Пропустить ➡️", "en": "Skip ➡️"},
    "not_found": {"hy": "Հայտարարությունը չի գտնվել։", "ru": "Объявление не найдено.",
                  "en": "Listing not found."},
    # filter
    "filter_title": {
        "hy": "🔎 <b>Քո ֆիլտրը</b>\n\n💰 Գին՝ {price}\n🚪 Սենյակներ՝ {rooms}\n📍 Թաղամասեր՝ {districts}\n"
              "🐾 Կենդանիներ՝ {pets}\n\nԸնտրիր, թե ինչ փոխել։",
        "ru": "🔎 <b>Твой фильтр</b>\n\n💰 Цена: {price}\n🚪 Комнаты: {rooms}\n📍 Районы: {districts}\n"
              "🐾 Животные: {pets}\n\nВыбери, что изменить.",
        "en": "🔎 <b>Your filter</b>\n\n💰 Price: {price}\n🚪 Rooms: {rooms}\n📍 Districts: {districts}\n"
              "🐾 Pets: {pets}\n\nChoose what to change.",
    },
    "any": {"hy": "ցանկացած", "ru": "любые", "en": "any"},
    "pets_need": {"hy": "պետք է թույլատրված լինեն", "ru": "обязательно можно", "en": "must be allowed"},
    "upto": {"hy": "մինչև ${v}", "ru": "до ${v}", "en": "up to ${v}"},
    "from": {"hy": "${v}-ից", "ru": "от ${v}", "en": "from ${v}"},
    "f_price": {"hy": "💰 Գին", "ru": "💰 Цена", "en": "💰 Price"},
    "f_rooms": {"hy": "🚪 Սենյակներ", "ru": "🚪 Комнаты", "en": "🚪 Rooms"},
    "f_districts": {"hy": "📍 Թաղամասեր", "ru": "📍 Районы", "en": "📍 Districts"},
    "f_pets": {"hy": "🐾 Կենդանիներ", "ru": "🐾 Животные", "en": "🐾 Pets"},
    "f_reset": {"hy": "♻️ Մաքրել", "ru": "♻️ Сбросить", "en": "♻️ Reset"},
    "f_done": {"hy": "✅ Պահպանել", "ru": "✅ Сохранить", "en": "✅ Save"},
    "ask_price": {
        "hy": "Գրիր գնի միջակայքը, օրինակ՝\n<code>300-600</code> (դոլար)\n<code>150000-250000 դրամ</code>\n"
              "<code>մինչև 500</code>\n\nԳրիր <code>0</code>՝ ցանկացած գնի համար։",
        "ru": "Напиши диапазон цены, например:\n<code>300-600</code> (доллары)\n<code>150000-250000 драм</code>\n"
              "<code>до 500</code>\n\nНапиши <code>0</code> — любая цена.",
        "en": "Send a price range, e.g.:\n<code>300-600</code> (USD)\n<code>150000-250000 AMD</code>\n"
              "<code>up to 500</code>\n\nSend <code>0</code> for any price.",
    },
    "price_bad": {"hy": "Չհասկացա գինը 🤔 Փորձիր այսպես՝ <code>300-600</code>",
                  "ru": "Не понял цену 🤔 Попробуй так: <code>300-600</code>",
                  "en": "Couldn't read the price 🤔 Try: <code>300-600</code>"},
    "choose_rooms": {"hy": "Ընտրիր սենյակների քանակը (կարելի է մի քանիսը)։",
                     "ru": "Выбери количество комнат (можно несколько).",
                     "en": "Choose number of rooms (you can pick several)."},
    "choose_districts": {"hy": "Ընտրիր թաղամասերը (կարելի է մի քանիսը)։",
                         "ru": "Выбери районы (можно несколько).",
                         "en": "Choose districts (you can pick several)."},
    "filter_saved": {"hy": "✅ Ֆիլտրը պահպանված է։ Նոր համապատասխան հայտարարությունները կգան այստեղ։",
                     "ru": "✅ Фильтр сохранён. Новые подходящие объявления придут сюда.",
                     "en": "✅ Filter saved. New matching listings will arrive here."},
    # posting
    "post_limit": {"hy": "Այսօր արդեն տեղադրել ես {n} հայտարարություն։ Փորձիր վաղը։",
                   "ru": "Сегодня ты уже разместил {n} объявл. Попробуй завтра.",
                   "en": "You've already posted {n} listings today. Try again tomorrow."},
    "post_district": {"hy": "➕ <b>Նոր հայտարարություն</b>\n\n📍 Ընտրիր թաղամասը։",
                      "ru": "➕ <b>Новое объявление</b>\n\n📍 Выбери район.",
                      "en": "➕ <b>New listing</b>\n\n📍 Choose the district."},
    "post_rooms": {"hy": "🚪 Քանի՞ սենյակ։", "ru": "🚪 Сколько комнат?", "en": "🚪 How many rooms?"},
    "post_price": {"hy": "💰 Գրիր ամսական գինը, օրինակ՝ <code>450$</code> կամ <code>180000 դրամ</code>",
                   "ru": "💰 Напиши цену в месяц, например: <code>450$</code> или <code>180000 драм</code>",
                   "en": "💰 Monthly price, e.g. <code>450$</code> or <code>180000 AMD</code>"},
    "post_pets": {"hy": "🐾 Կենդանիներ թույլատրվա՞ծ են։", "ru": "🐾 Можно с животными?",
                  "en": "🐾 Are pets allowed?"},
    "post_desc": {"hy": "📝 Գրիր կարճ նկարագրություն (հարկ, վերանորոգում, կահույք...)։ Մինչև 800 նիշ։",
                  "ru": "📝 Короткое описание (этаж, ремонт, мебель...). До 800 символов.",
                  "en": "📝 Short description (floor, renovation, furniture...). Up to 800 characters."},
    "desc_long": {"hy": "Շատ երկար է ({n} նիշ)։ Կրճատիր մինչև 800։",
                  "ru": "Слишком длинно ({n} симв.). Сократи до 800.",
                  "en": "Too long ({n} chars). Keep it under 800."},
    "post_photo": {"hy": "📷 Ուղարկիր մեկ լուսանկար կամ սեղմիր «Բաց թողնել»։",
                   "ru": "📷 Отправь одно фото или нажми «Пропустить».",
                   "en": "📷 Send one photo or tap “Skip”."},
    "post_phone": {"hy": "📞 Ուղարկիր հեռախոսահամարը կոճակով կամ գրիր՝ <code>091 123456</code>",
                   "ru": "📞 Отправь номер кнопкой или напиши: <code>091 123456</code>",
                   "en": "📞 Share your number with the button or type it: <code>091 123456</code>"},
    "share_contact": {"hy": "📱 Ուղարկել իմ համարը", "ru": "📱 Отправить мой номер",
                      "en": "📱 Share my number"},
    "phone_bad": {"hy": "Համարը սխալ է։ Օրինակ՝ <code>091 123456</code> կամ <code>+374 91 123456</code>",
                  "ru": "Неверный номер. Пример: <code>091 123456</code> или <code>+374 91 123456</code>",
                  "en": "Invalid number. Example: <code>091 123456</code> or <code>+374 91 123456</code>"},
    "blacklisted": {"hy": "🚫 Այս համարը սև ցուցակում է բողոքների պատճառով։",
                    "ru": "🚫 Этот номер в чёрном списке из‑за жалоб.",
                    "en": "🚫 This number is blacklisted due to reports."},
    "duplicate": {"hy": "Այս հայտարարությունը արդեն տեղադրված է վերջին 7 օրում։",
                  "ru": "Это объявление уже размещено за последние 7 дней.",
                  "en": "This listing was already posted in the last 7 days."},
    "published": {"hy": "✅ Հրապարակված է։ Ուղարկում եմ նրանց, ում ֆիլտրին համապատասխանում է։",
                  "ru": "✅ Опубликовано. Отправляю тем, чей фильтр подходит.",
                  "en": "✅ Published. Sending it to people whose filter matches."},
    "sent_to": {"hy": "📬 Հայտարարությունդ ուղարկվեց {n} մարդու։",
                "ru": "📬 Твоё объявление получили {n} чел.",
                "en": "📬 Your listing was sent to {n} people."},
    # listing card
    "card_rooms": {"hy": "{n} սենյակ", "ru": "{n}-комн.", "en": "{n}-room"},
    "card_pets_yes": {"hy": "🐾 Կենդանիներ՝ թույլատրված", "ru": "🐾 Животные: можно",
                      "en": "🐾 Pets: allowed"},
    "card_pets_no": {"hy": "🐾 Կենդանիներ՝ ոչ", "ru": "🐾 Животные: нельзя", "en": "🐾 Pets: no"},
    "card_owner": {"hy": "✅ Տեղադրել է սեփականատերը", "ru": "✅ Разместил владелец",
                   "en": "✅ Posted by the owner"},
    "card_source": {"hy": "🔗 Բացել աղբյուրը", "ru": "🔗 Открыть источник", "en": "🔗 Open source"},
    "rep_agent": {"hy": "🏢 Միջնորդ է", "ru": "🏢 Посредник", "en": "🏢 Agent"},
    "rep_fake": {"hy": "🚫 Խաբեություն", "ru": "🚫 Мошенник", "en": "🚫 Scam"},
    "rep_thanks": {"hy": "Շնորհակալություն, բողոքն ընդունված է։", "ru": "Спасибо, жалоба принята.",
                   "en": "Thanks, report received."},
    "rep_already": {"hy": "Դու արդեն բողոքել ես այս հայտարարության մասին։",
                    "ru": "Ты уже жаловался на это объявление.",
                    "en": "You've already reported this listing."},
    "rep_own": {"hy": "Սեփական հայտարարության վրա բողոքել չի կարելի։",
                "ru": "Нельзя пожаловаться на своё объявление.",
                "en": "You can't report your own listing."},
    # my listings
    "my_empty": {"hy": "Դու դեռ ակտիվ հայտարարություն չունես։", "ru": "У тебя нет активных объявлений.",
                 "en": "You have no active listings."},
    "rented": {"hy": "✅ Վարձակալված է, հանել", "ru": "✅ Сдано, снять", "en": "✅ Rented, remove"},
    "removed": {"hy": "Հայտարարությունը հանված է։", "ru": "Объявление снято.", "en": "Listing removed."},
}


def t(key: str, lang: str, **kwargs) -> str:
    variants = T[key]
    text = variants.get(lang) or variants["hy"]
    return text.format(**kwargs) if kwargs else text


def variants(key: str) -> set[str]:
    """Every translation of a button label, to match reply-keyboard presses in any language."""
    return set(T[key].values())
