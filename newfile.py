import asyncio, requests, re, os, json, random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# --- AYARLAR ---
TOKEN= "8502316085:AAHqk51yzmTGE6rEbJrxlbs2oWiAljvjD78"
GRUP_ID = -5107493439
ADMINS = [8518879013] 
USERS_FILE = "kullanicilar.json"
STOK_FILE = "stoklar_wa.json"
API_URL = "https://otp.xclusor.workers.dev/"

# --- BAYRAK ---
COUNTRY_CODES = {
    "994": "🇦🇿", "90": "🇹🇷", "7": "🇷🇺", "49": "🇩🇪", "1": "🇺🇸", "44": "🇬🇧", "33": "🇫🇷", "380": "🇺🇦",
    "263": "🇿🇼", "58": "🇻🇪", "225": "🇨🇮", "998": "🇺🇿", "77": "🇰🇿", "966": "🇸🇦", "55": "🇧🇷",
    "91": "🇮🇳", "92": "🇵🇰", "62": "🇮🇩", "60": "🇲🇾", "66": "🇹🇭", "81": "🇯🇵", "82": "🇰🇷", "86": "🇨🇳"
}

def get_flag(phone):
    phone = re.sub(r'\D', '', phone)
    for length in [3, 2, 1]:
        prefix = phone[:length]
        if prefix in COUNTRY_CODES:
            return COUNTRY_CODES[prefix]
    return "🏳️"

# --- VERİ ---
def veri_yukle(dosya, varsayilan):
    if os.path.exists(dosya):
        try:
            with open(dosya, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return varsayilan
    return varsayilan

def veri_kaydet(dosya, veri):
    with open(dosya, "w", encoding="utf-8") as f:
        json.dump(veri, f, ensure_ascii=False, indent=4)

# --- USER KLAVYE ---
def get_user_kb():
    stok = veri_yukle(STOK_FILE, {})
    kb = []
    ulkeler = list(stok.keys())

    for i in range(0, len(ulkeler), 2):
        row = []
        for u in ulkeler[i:i+2]:
            row.append(
                InlineKeyboardButton(
                    f"🌍 {u}\n {len(stok[u])} adet",
                    callback_data=f"al_{u}"
                )
            )
        kb.append(row)

    if not kb:
        kb.append([InlineKeyboardButton("🚫 STOK YOK", callback_data="none")])

    return InlineKeyboardMarkup(kb)

# --- ADMIN KLAVYE ---
def get_admin_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📥 Stok Ekle", callback_data="adm_ekle"), InlineKeyboardButton("📢 Duyuru", callback_data="adm_duyuru")],
        [InlineKeyboardButton("👤 Admin Ekle", callback_data="adm_user"), InlineKeyboardButton("🗑️ Tek Sil", callback_data="adm_tek_sil")],
        [InlineKeyboardButton("🔥 TÜMÜNÜ SİL", callback_data="adm_full_sil")],
        [InlineKeyboardButton("🌍 Menü", callback_data="baslat")]
    ])

# --- START ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    users = veri_yukle(USERS_FILE, [])
    if uid not in users:
        users.append(uid)
        veri_kaydet(USERS_FILE, users)

    msg = (
        "╭━━━ 🤖 OTP SYSTEM ━━━╮\n"
        "┃\n"
        "┃ 📲 Numara almak için\n"
        "┃ 🌍 Aşağıdan ülke seç\n"
        "┃\n"
        "╰━━━━━━━━━━━━━━━━━━╯"
    )

    if update.message:
        await update.message.reply_text(msg, reply_markup=get_user_kb())
    else:
        await update.callback_query.edit_message_text(msg, reply_markup=get_user_kb())

# --- ADMIN ---
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMINS:
        return

    await update.message.reply_text(
        "╭━━━ ⚙️ ADMIN PANEL ━━━╮\n\n🔧 İşlem seç\n\n╰━━━━━━━━━━━━━━━━━━╯",
        reply_markup=get_admin_kb()
    )

# --- CALLBACK ---
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data, uid = query.data, query.from_user.id
    await query.answer()
    stok = veri_yukle(STOK_FILE, {})

    if data == "baslat":
        return await start(update, context)

    elif data.startswith("al_"):
        u = data.replace("al_", "")

        if not stok.get(u):
            return await query.message.reply_text("⚠️ Stok yok!")

        num = stok[u].pop(random.randrange(len(stok[u])))
        veri_kaydet(STOK_FILE, stok)

        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Değiştir", callback_data=f"al_{u}"), InlineKeyboardButton("🌍 Ülke", callback_data="baslat")],
            [InlineKeyboardButton("📱 OTP Grup", url="https://t.me/sorgupanelinn")]
        ])

        await query.edit_message_text(
            f"""
╭━━━ 📲 NUMARA ━━━╮

📞 {get_flag(num)} {num}

⏳ OTP bekleniyor...

╰━━━━━━━━━━━━━━╯
""",
            reply_markup=kb
        )

    if uid not in ADMINS:
        return

    if data == "adm_ekle":
        context.user_data['step'] = 'FILE'
        await query.message.reply_text("📎 .txt dosyası gönder")
    elif data == "adm_duyuru":
        context.user_data['step'] = 'DUYURU'
        await query.message.reply_text("📢 Mesaj yaz")
    elif data == "adm_user":
        context.user_data['step'] = 'ADD_ADMIN'
        await query.message.reply_text("👤 ID gir")
    elif data == "adm_tek_sil":
        kb = [[InlineKeyboardButton(u, callback_data=f"del_{u}")] for u in stok.keys()]
        await query.message.reply_text("Silinecek ülke:", reply_markup=InlineKeyboardMarkup(kb))
    elif data.startswith("del_"):
        stok.pop(data.replace("del_", ""), None)
        veri_kaydet(STOK_FILE, stok)
        await query.message.reply_text("✅ Silindi", reply_markup=get_admin_kb())
    elif data == "adm_full_sil":
        veri_kaydet(STOK_FILE, {})
        await query.message.reply_text("🔥 Hepsi silindi", reply_markup=get_admin_kb())

# --- MESAJ ---
async def mesaj_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    step = context.user_data.get('step')

    if uid not in ADMINS or not step:
        return

    if step == 'FILE' and update.message.document:
        f = await update.message.document.get_file()
        context.user_data['tmp_nums'] = requests.get(f.file_path).text.splitlines()
        context.user_data['step'] = 'ULKE'
        await update.message.reply_text("Ülke adı yaz")

    elif step == 'ULKE':
        stok = veri_yukle(STOK_FILE, {})
        stok.setdefault(update.message.text, []).extend(context.user_data['tmp_nums'])
        veri_kaydet(STOK_FILE, stok)
        context.user_data['step'] = None
        await update.message.reply_text("✅ Eklendi", reply_markup=get_admin_kb())

    elif step == 'DUYURU':
        for u in veri_yukle(USERS_FILE, []):
            try:
                await context.bot.send_message(u, update.message.text)
            except:
                pass
        await update.message.reply_text("✅ Gönderildi", reply_markup=get_admin_kb())
        context.user_data['step'] = None

    elif step == 'ADD_ADMIN':
        ADMINS.append(int(update.message.text))
        await update.message.reply_text("✅ Admin eklendi", reply_markup=get_admin_kb())
        context.user_data['step'] = None

# --- API TAKİP ---
async def api_izle(app):
    seen = set()
    while True:
        try:
            r = requests.get(API_URL, timeout=10).json()
            for row in reversed(r[:15]):
                no, msg = str(row[1]), str(row[2])
                uid = f"{no}_{msg[:12]}"
                if uid not in seen:
                    otp = re.search(r'\d{3,}-\d{3,}|\d{4,6}', msg)
                    otp = otp.group(0) if otp else "⏳"
                    txt = f" **NEW WHATSAPP OTP!**\n\n📱 **No:** {get_flag(no)} `{no}`\n🔑 **OTP:** `{otp}`\n\n💬 **SMS:** `{msg}`"
                    kb = InlineKeyboardMarkup([[InlineKeyboardButton("🤖 Bot", url="https://t.me/SEXEOtpBot"), InlineKeyboardButton("📢 Channel", url="https://t.me/sorgupanelinn")]])
                    await app.bot.send_message(GRUP_ID, txt, reply_markup=kb, parse_mode="Markdown")
                    seen.add(uid)
            await asyncio.sleep(3)
        except:
            await asyncio.sleep(5)

# --- RUN ---
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.ALL, mesaj_handler))

    asyncio.get_event_loop().create_task(api_izle(app))

    app.run_polling()