import json
import random
import time
from tls_client import Session, response
import imaplib
import email
import concurrent.futures
import os
import platform
from random import choice
from colorama import Fore

def clear():
    if platform.system() == 'Windows':
        os.system('cls')
    elif platform.system() == 'Linux':
        os.system('clear')
def clean_mailbox(email):
    try:
        imap = imaplib.IMAP4_SSL('imap.firstmail.ltd', 993)
        imap.login(email, "Hustlershop123")
        mailbox = 'INBOX'
        imap.select(mailbox)
        status, email_ids = imap.search(None, 'ALL')
        for email_id in email_ids[0].split():
            imap.store(email_id, '+FLAGS', '\\Deleted')
        imap.expunge()
        imap.logout()
        print(Fore.GREEN + "[+] Mailbox cleared successfully" + Fore.RESET)
    except:
        print(Fore.RED + "[-] Error while clearing mailbox" + Fore.RESET)

class Feedback:
    def __init__(self):
        self.session = Session(
            client_identifier="chrome_113",
            random_tls_extension_order=True
        )
        self.config = json.load(open("config.json"))
        self.shop: str = self.config.get("shop")
        self.proxy = (choice(open("./proxies.txt", "r").readlines()).strip()
            if len(open("./proxies.txt", "r").readlines()) != 0
            else None)
        self.session.proxies = {
            "http": "http://" + self.proxy,
            "https": "http://" + self.proxy
        }

    def obtain_mail(self, mail):
        try:
            client = imaplib.IMAP4_SSL('imap.firstmail.ltd', 993)
            client.login(mail, 'Hustlershop123')
            client.select("inbox")
            
            for i in range(20):
                result, data = client.search(None, '(FROM "notice@orders.sellix.io" SUBJECT "order completed")')
                
                if data[0]:
                    latest_email_id = data[0].split()[-1]
                    result, data = client.fetch(latest_email_id, "(RFC822)")
                    raw_email = data[0][1]
                    email_message = email.message_from_bytes(raw_email)
                    
                    if "Completed" in email_message['Subject']:
                        for part in email_message.walk():
                            if part.get_content_type() == "text/plain":
                                url = str(part.get_payload(decode=True).decode('utf-8').split('feedback: ')[-1].split(',')[0])
                                Feedback().complete(url)
                                return
            
            client.logout()
        except Exception as e:
            print(f"An error occurred: {e}")

    def generate_invoice(self):
        with open('mails.txt', 'r') as f:
            mails = f.read().splitlines()
        email = random.choice(mails).split(':')[0]
        print(Fore.YELLOW + f"Email used: {email}" + Fore.RESET)
        clean_mailbox(email)
        global invoices
        try:
            r = self.session.post(
                "https://dev.sellix.io/v1/payments",
                headers={"Authorization": 'Bearer ' + self.config.get("sellix_auth")},
                json={
                    "title": "Title",
                    "return_url": "http://1.1.1.1",
                    "email": email,
                    "currency": "USD",
                    "description": "Test payment",
                    "confirmations": 3,
                    "credit_card": None,
                    "product_id": self.config.get("product_id"),
                    "quantity": 1,
                    "gateway": "",
                }
            )
            if 'Invalid Email' in r.text:
                return self.generate_invoice()
            uniqid = r.json()['data']['uniqid']
            url = r.json()['data']['url']
            
            r = self.session.put(f"https://dev.sellix.io/v1/payments/{uniqid}",
                        headers={"Authorization": 'Bearer ' + self.config.get("sellix_auth")})
            
            Feedback().obtain_mail(email)

        except Exception as e:
            print(e)

    def complete(self, url):
        global reviews
        with open('feedback.txt', 'r') as f:
            feedback = f.read().splitlines()
        quote = random.choice(feedback)

        invoice_id = url.split('/')[-1]
        try:
            headers = {"referer": f"url",
                       "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, "
                                     "like Gecko) Chrome/111.0.0.0 Safari/537.36"}
            score = random.randint(4, 5)
            r = Session(client_identifier="chrome108").post(
                f"https://{self.shop}.mysellix.io/api/shop/feedback/reply",
                json={"feedback": "positive", "message": quote, "score": score, "uniqid": invoice_id}, headers=headers)
            if r.json()['message'] == 'Feedback Sent Successfully.':
                print("Sent Out Feedback Successfully")
                reviews += 1
                return
            else:
                print("Failed To Send Out Feedback")
                return
        except Exception as e:
            print(e)
            self.complete(url)



reviews = 0
if __name__ == '__main__':
    clear()
    amount = int(input("How many reviews: "))
    while reviews < amount:
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(Feedback().generate_invoice) for _ in range(amount-reviews)]
            for future in concurrent.futures.as_completed(futures):
                pass
    

