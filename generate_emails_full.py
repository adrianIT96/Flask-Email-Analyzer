import os
from email.message import EmailMessage
import random
from datetime import datetime, timedelta

OUTPUT_DIR = "test_emails_full"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# senders grouped by category (use the list zhora alebo uprav podľa potreby)
senders_by_cat = {
    "Shops": ["offers@alza.cz","promo@notino.com","deals@amazon.com","sale@zalando.com","orders@ebay.com","shop@hm.com","no-reply@decathlon.com"],
    "Banks": ["alert@tatrabanka.sk","info@vub.sk","no-reply@slsp.sk","alerts@mbank.pl","notifications@csob.sk"],
    "Investments": ["news@trading212.com","alerts@binance.com","report@etoro.com"],
    "Health": ["newsletter@fitbit.com","hello@myfitnesspal.com","info@zdravie.sk","updates@webmd.com"],
    "Social": ["notification@facebook.com","noreply@instagram.com","invite@linkedin.com","mention@twitter.com","digest@reddit.com"],
    "Education": ["weekly@coursera.org","no-reply@udemy.com","progress@edx.org","hello@khanacademy.org"],
    "Travel": ["booking@booking.com","confirmations@airbnb.com","deals@ryanair.com","tickets@wizzair.com","alerts@tripadvisor.com"],
    "Tech": ["notifications@github.com","updates@notion.so","slack@slack.com","noreply@dropbox.com","meeting@zoom.us","card@trello.com"],
    "Utilities": ["billing@zse.sk","invoice@energie.com","notice@voda.sk","support@innogy.com"],
    "Entertainment": ["news@spotify.com","offers@steam.com","updates@epicgames.com","hello@netflix.com","promo@youtube.com"],
    "Work": ["jobs@profesia.sk","hr@indeed.com","meeting@zoom.us","recruiter@linkedin.com"],
    "Promotions": ["promo@marketing-agency.com","newsletter@deals.com","offers@promo.example"],
    "Spam": ["win@easycash.biz","prize@lottery-now.com","click@profitfast.io","scam@fakeprize.co"],
    "Government": ["info@post.sk","no-reply@gov.sk","notice@nbs.sk"]
}

subjects_pool = {
    "Shops": ["Your order has been shipped","Flash Sale - 50% off","Discount inside: don't miss out"],
    "Banks": ["Account alert","Your monthly statement is ready","Suspicious login attempt detected"],
    "Investments": ["Weekly portfolio update","Important: margin call","New investment opportunity"],
    "Health": ["Your weekly health summary","Time to move: activity reminder","New health tips for you"],
    "Social": ["You have a new follower","Someone mentioned you","New connection request"],
    "Education": ["Course update: new material","Your certificate is ready","Reminder: continue learning"],
    "Travel": ["Booking confirmation","Your itinerary","Deal: cheap flights this week"],
    "Tech": ["Repo starred","Invitation to collaborate","Security alert for your account"],
    "Utilities": ["Invoice due","Payment reminder","Scheduled maintenance notice"],
    "Entertainment": ["New episodes released","Your playlist update","Limited time offer for members"],
    "Work": ["Interview invitation","Job application received","Team meeting scheduled"],
    "Promotions": ["Exclusive offer just for you","Don't miss our promo","Limited time discount"],
    "Spam": ["YOU'VE WON $10,000!","Click here to claim your prize","Urgent: verify your account NOW"],
    "Government": ["Official notice","Tax information","Service update from the municipality"]
}

bodies = [
    "This is a test email generated for demo purposes.",
    "Hello, this sample message helps testing email categorization.",
    "Thank you for using our service. This is a sample email body.",
    "Reminder: please check your account and follow the instructions if needed."
]

NUM_PER_CAT = 12  # uprav podľa potreby (viac = bohatší graf)

counter = 0
for category, senders in senders_by_cat.items():
    for i in range(NUM_PER_CAT):
        sender = random.choice(senders)
        subject = random.choice(subjects_pool.get(category, ["Test email"]))
        body = random.choice(bodies)
        recipient = "user@example.com"

        # náhodný dátum v posledných 90 dňoch
        days_ago = random.randint(0, 90)
        dt = datetime.now() - timedelta(days=days_ago, hours=random.randint(0,23), minutes=random.randint(0,59))
        date_hdr = dt.strftime("%a, %d %b %Y %H:%M:%S +0000")

        msg = EmailMessage()
        msg["From"] = sender
        msg["To"] = recipient
        msg["Subject"] = subject
        msg["Date"] = date_hdr
        msg.set_content(f"{body}\n\nCategory: {category}\nGenerated for testing purposes.")

        counter += 1
        filename = f"{category}_{i+1}.eml"
        with open(os.path.join(OUTPUT_DIR, filename), "wb") as f:
            f.write(bytes(msg))

print(f"✅ Generated {counter} test .eml files in folder: {OUTPUT_DIR}")
