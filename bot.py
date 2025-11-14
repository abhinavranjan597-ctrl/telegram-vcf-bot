import os
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"

DEFAULT_COUNTRY_CODE = "+60"
BASE_PHONE = 10000000
PHONE_STEP = 123


def detect_country_code(phone_number, provided_code):
    if provided_code:
        return provided_code

    s = str(phone_number)
    if s.startswith("91"):
        return "+91"
    if s.startswith("60"):
        return "+60"
    if s.startswith("62"):
        return "+62"

    return DEFAULT_COUNTRY_CODE


def create_multiple_vcf(name, total_qty, per_file, start_num, base_phone, country_code, base_path):
    file_count = 1
    current_num = start_num
    current_phone = base_phone
    created_files = []

    while total_qty > 0:
        batch_size = min(per_file, total_qty)
        vcf_filename = f"{base_path}_{file_count}.vcf"

        with open(vcf_filename, "w", encoding="utf-8") as vcf:
            for _ in range(batch_size):
                lname = str(current_num)

                vcf.write("BEGIN:VCARD\n")
                vcf.write("VERSION:3.0\n")
                vcf.write(f"N:{lname};{name};;;\n")
                vcf.write(f"FN:{name} {lname}\n")
                vcf.write(f"TEL;TYPE=CELL:{country_code}{current_phone}\n")
                vcf.write("END:VCARD\n\n")

                current_num += 1
                current_phone += PHONE_STEP

        created_files.append(vcf_filename)
        total_qty -= batch_size
        file_count += 1

    return created_files


async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = update.message.document

    if not file.file_name.endswith(".txt"):
        await update.message.reply_text(
            "TXT format:\n"
            "1) Name, TotalQty, PerFile\n"
            "2) Name, TotalQty, PerFile, StartNum\n"
            "3) Name, TotalQty, PerFile, StartNum, CountryCode"
        )
        return

    txt_path = f"input_{file.file_id}.txt"
    base_name = file.file_name.replace(".txt", "")

    telegram_file = await file.get_file()
    await telegram_file.download_to_drive(txt_path)

    with open(txt_path, "r") as f:
        line = f.readline().strip()

    parts = [x.strip() for x in line.split(",")]

    name = parts[0]
    total_qty = int(parts[1])
    per_file = int(parts[2])
    start_num = int(parts[3]) if len(parts) >= 4 else 1
    provided_country = parts[4] if len(parts) >= 5 else None

    country_code = detect_country_code(BASE_PHONE, provided_country)

    created_files = create_multiple_vcf(
        name, total_qty, per_file, start_num,
        BASE_PHONE, country_code, base_name
    )

    for vcf_file in created_files:
        with open(vcf_file, "rb") as v:
            await update.message.reply_document(v)
        os.remove(vcf_file)

    os.remove(txt_path)


async def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.Document.ALL, handle_file))
    await app.run_polling()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
  
