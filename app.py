from flask import Flask, render_template, request, send_from_directory, redirect, url_for, session
import os
from email import policy
from email.parser import BytesParser
from email.utils import parseaddr, parsedate_to_datetime
from collections import Counter
import shutil
import csv
import random
import re
import json

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
# SESSION je potrebná pre uloženie štatistík pri PRG vzore
app.config['SECRET_KEY'] = os.urandom(24) 

# ============================================
# 🏷️ KATEGÓRIE A KLÚČOVÉ SLOVÁ
# ============================================
CATEGORIES = {
    # Shops & eCommerce
    "alza": "Shops",
    "mall": "Shops",
    "notino": "Shops",
    "amazon": "Shops",
    "ebay": "Shops",
    "hm.com": "Shops",
    "zalando": "Shops",
    "decathlon": "Shops",
    "receipt": "Shops",
    "order": "Shops",

    # Banks & Finance
    "tatrabanka": "Banks",
    "vub": "Banks",
    "slsp": "Banks",
    "mbank": "Banks",
    "csob": "Banks",
    "binance": "Investments",
    "trading212": "Investments",
    "etoro": "Investments",
    "invoice": "Banks",
    "payment": "Banks",

    # Health & Fitness
    "fitbit": "Health",
    "myfitnesspal": "Health",
    "zdravie": "Health",
    "doctors": "Health",
    "webmd": "Health",

    # Social & Networking
    "facebook": "Social",
    "instagram": "Social",
    "linkedin": "Social",
    "twitter": "Social",
    "reddit": "Social",
    "tiktok": "Social",

    # Education
    "duolingo": "Education",
    "coursera": "Education",
    "edx": "Education",
    "udemy": "Education",
    "khanacademy": "Education",

    # Travel
    "booking": "Travel",
    "airbnb": "Travel",
    "wizzair": "Travel",
    "ryanair": "Travel",
    "tripadvisor": "Travel",

    # Tech / Software Tools
    "github": "Tech",
    "notion": "Tech",
    "slack": "Tech",
    "dropbox": "Tech",
    "zoom": "Tech",
    "trello": "Tech",
    "google": "Tech",
    "login": "Tech",

    # Utilities / Bills
    "zse": "Utilities",
    "innogy": "Utilities",
    "voda": "Utilities",
    "energie": "Utilities",

    # Entertainment / Games
    "steam": "Entertainment",
    "spotify": "Entertainment",
    "epicgames": "Entertainment",
    "playstation": "Entertainment",
    "netflix": "Entertainment",
    "youtube": "Entertainment",

    # Work / Business
    "profesia": "Work",
    "indeed": "Work",
    "zoom.us": "Work",
    "slack.com": "Work",

    # Promotions / Marketing (Rozšírené)
    "newsletter": "Promotions",
    "promo": "Promotions",
    "offers": "Promotions",
    "marketing": "Promotions",
    "deals": "Promotions",
    "discount": "Promotions",
    "sale": "Promotions",
    "unsubscribe": "Promotions",

    # Spam / Scam (Rozšírené)
    "lotto": "Spam",
    "casino": "Spam",
    "profit": "Spam",
    "click": "Spam",
    "bit.ly": "Spam",
    "win": "Spam",
    "money": "Spam",
    "virus": "Spam",
    "password": "Spam",
    "crypt": "Spam",
    
    # Default
    "gov": "Government",
    "post": "Government",
}

# Rozšírený zoznam podozrivých kľúčových slov
SUSPICIOUS_KEYWORDS = [
    "win", "free", "urgent", "money", "limited", "offer", "click", "verify",
    "lottery", "bonus", "account suspended", "reset password", "security alert"
]
SUSPICIOUS_DOMAIN_CHARS = ["-", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"] 

# ============================================
# ⚙️ POMOCNÉ FUNKCIE
# ============================================

def get_sender_domain(sender):
    if not sender:
        return ""
    _, email_addr = parseaddr(sender)
    parts = email_addr.lower().split("@")
    if len(parts) == 2:
        return parts[1]
    return ""

def get_category(sender, body=""):
    domain = get_sender_domain(sender)
    
    # 1. Kontrola Domény (Priorita)
    for keyword, category in CATEGORIES.items():
        if keyword in domain:
            return category
            
    # 2. Kontrola Telo Emailu (Sekundárna možnosť)
    if body:
        body_lower = body.lower()
        for keyword, category in CATEGORIES.items():
            if len(keyword) > 3 and keyword in body_lower:
                 return category

    return "Unknown"

def get_email_body(msg):
    """Rekurzívne extrahuje čistý text (text/plain) z MIME správy."""
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            cdisp = part.get_content_disposition()

            if ctype == "text/plain" and not cdisp:
                try:
                    return part.get_payload(decode=True).decode(part.get_content_charset() or 'utf-8', errors='replace')
                except:
                    pass 
    else:
        ctype = msg.get_content_type()
        if ctype == "text/plain":
            try:
                return msg.get_payload(decode=True).decode(msg.get_content_charset() or 'utf-8', errors='replace')
            except:
                return ""
    return ""

def calculate_suspicious_score(sender, subject, body=""):
    """Vypočíta skóre podozrivosti od 0 do 100."""
    score = 0
    domain = get_sender_domain(sender)

    # 1. Kontrola podozrivých kľúčových slov (max. 50 bodov)
    subject_lower = subject.lower()
    body_lower = body.lower()
    
    susp_count = sum(1 for word in SUSPICIOUS_KEYWORDS if word in subject_lower)
    susp_count += sum(1 for word in SUSPICIOUS_KEYWORDS if word in body_lower) / 2 

    score += min(50, susp_count * 10) 

    # 2. Kontrola podozrivých znakov v doméne (max. 30 bodov)
    if any(char in domain for char in SUSPICIOUS_DOMAIN_CHARS) or domain.count('.') > 2:
        score += 30

    # 3. Kontrola neznámej kategórie (max. 20 bodov)
    if get_category(sender, body) == "Unknown":
        score += 20
        
    return min(100, int(score))

# ============================================
# 🌐 FLASK TRASY (PRG VZOR)
# ============================================

@app.route("/", methods=["GET", "POST"])
def index():
    """Spracuje nahrávanie súborov a presmeruje na výsledky."""
    if request.method == "POST":
        uploaded_files = request.files.getlist("files")
        category_counts = Counter()
        results_summary = [] 

        for file in uploaded_files:
            if file.filename and file.filename.endswith(".eml"):
                temp_filepath = os.path.join(UPLOAD_FOLDER, file.filename + "_temp")
                file.save(temp_filepath)

                try:
                    with open(temp_filepath, "rb") as f:
                        msg = BytesParser(policy=policy.default).parse(f)

                    sender = msg["From"] or ""
                    subject = msg["Subject"] or ""
                    date_header = msg["Date"]
                    
                    email_date = ""
                    if date_header:
                        dt = parsedate_to_datetime(date_header)
                        if dt:
                            email_date = dt.strftime("%Y-%m-%d %H:%M:%S") 
                    
                    body = get_email_body(msg)
                    category = get_category(sender, body)
                    suspicious_score = calculate_suspicious_score(sender, subject, body)

                    category_counts[category] += 1
                    results_summary.append({
                        "filename": file.filename,
                        "date": email_date,
                        "sender": sender,
                        "subject": subject,
                        "category": category,
                        "score": suspicious_score
                    })
                except Exception as e:
                    print(f"Error parsing file {file.filename}: {e}")
                finally:
                    if os.path.exists(temp_filepath):
                        os.remove(temp_filepath)

        # 1. Uloženie VŠETKÝCH výsledkov do CSV
        output_csv = os.path.join(UPLOAD_FOLDER, "email_summary.csv")
        with open(output_csv, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Filename", "Date", "Sender", "Subject", "Category", "Suspicious Score"])
            for r in results_summary:
                # Používame r["score"] pre CSV
                writer.writerow([r["filename"], r["date"], r["sender"], r["subject"], r["category"], r["score"]])

        # 2. Uloženie KATEGÓRIE štatistík do session
        session['stats'] = dict(category_counts)
        
        # 3. PRESMEROVANIE na novú GET URL (/results)
        return redirect(url_for('results'))

    # GET metóda pre index
    return render_template("index.html")

@app.route("/results", methods=["GET"])
def results():
    """Načíta výsledky a štatistiky. Ak chýbajú, nanovo ich vytvorí z CSV."""
    
    # 1. Načítanie štatistík zo session (session.get, aby sa zachovali pri refreši)
    stats = session.get('stats', None) 

    # 2. Načítanie detailných výsledkov z CSV
    results = []
    output_csv = os.path.join(UPLOAD_FOLDER, "email_summary.csv")
    
    # Ak CSV existuje, načítame výsledky a prípadne nanovo vytvoríme stats
    if os.path.exists(output_csv):
        with open(output_csv, "r", newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            
            # Ak stats chýbajú (prvá návšteva po refreši alebo priamym odkazom), vytvoríme ich nanovo
            if stats is None:
                category_counts = Counter()
            
            for row in reader:
                try:
                    # Premenujeme Suspicious Score na jednoduché 'score'
                    row['score'] = int(row['Suspicious Score'])
                except (ValueError, TypeError):
                    row['score'] = 0
                results.append(row)
                
                # Ak stats chýbajú, počítame kategórie znova
                if stats is None and 'Category' in row:
                    category_counts[row['Category']] += 1
            
            # Ak stats chýbali, priradíme novo vypočítané a uložíme do session pre ďalší refresh
            if stats is None:
                stats = dict(category_counts)
                session['stats'] = stats # Uložíme ich späť do session
        
    # Ak ani po načítaní z CSV nemáme results a stats, presmerujeme na index
    if not results or not stats:
        return redirect(url_for('index'))
        
    # 3. Renderovanie šablóny výsledkov (čistý GET)
    return render_template("results.html", results=results, stats=stats)


@app.route("/download_csv")
def download_csv():
    """Umožňuje stiahnutie vygenerovaného súboru email_summary.csv."""
    
    filename = "email_summary.csv"
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    
    if not os.path.exists(file_path):
        return redirect(url_for('index'))
    
    response = send_from_directory(
        directory=UPLOAD_FOLDER,
        path=filename,
        as_attachment=True,
        mimetype='text/csv',
        download_name="email_analysis_summary.csv" 
    )
    
    return response

# ============================================
# 🚀 Run App
# ============================================

if __name__ == "__main__":
    app.run(debug=True)