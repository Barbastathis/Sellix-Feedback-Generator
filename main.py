import json
import random
from tls_client import Session
import imaplib
import email
import concurrent.futures
import os
import platform
from random import choice
from colorama import Fore
from datetime import datetime

def clear():
    if platform.system() == 'Windows':
        os.system('cls')
    elif platform.system() == 'Linux':
        os.system('clear')

class Feedback:
    def __init__(self, mail, password):
        self.mail = mail
        self.password = password
        self.session = Session(
            client_identifier="chrome_113",
            random_tls_extension_order=True
        )
        self.config = json.load(open("config.json", encoding='utf-8'))
        self.shop: str = self.config.get("shop")
        if self.config.get("proxy") == True and len(open("./proxies.txt", "r", encoding='utf-8').readlines()) != 0:
            self.proxy = (choice(open("./proxies.txt", "r", encoding='utf-8').readlines()).strip()
                if len(open("./proxies.txt", "r", encoding='utf-8').readlines()) != 0
                else None)
            self.session.proxies = {
                "http": "http://" + self.proxy,
                "https": "http://" + self.proxy
            }

    def clean_mailbox(self):
        try:
            imap = imaplib.IMAP4_SSL('imap.firstmail.ltd', 993)
            imap.login(self.mail, self.password)
            mailbox = 'INBOX'
            imap.select(mailbox)
            status, email_ids = imap.search(None, 'ALL')
            for email_id in email_ids[0].split():
                imap.store(email_id, '+FLAGS', '\\Deleted')
            imap.expunge()
            imap.logout()
            print(datetime.now().strftime("%H:%M") , f"| {Fore.GREEN}SUCCESS{Fore.WHITE} | Mailbox cleared successfully {self.mail}"+ Fore.RESET)
        except:
            print(datetime.now().strftime("%H:%M") , f"| {Fore.RED}ERROR{Fore.WHITE} | Could not clear mailbox {self.mail}"+ Fore.RESET)

    def get_mail(self):
        try:
            client = imaplib.IMAP4_SSL('imap.firstmail.ltd', 993)
            client.login(self.mail, self.password)
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
                                Feedback(self.mail, self.password).complete(url)
                                return
            
            client.logout()
        except Exception as e:
            print(f"An error occurred: {e}")

    def generate_invoice(self):
        print(datetime.now().strftime("%H:%M") , f"| {Fore.YELLOW}INFO{Fore.WHITE} | Email: {self.mail}" + Fore.RESET)
        self.clean_mailbox()
        global invoices
        try:
            r = self.session.post(
                "https://dev.sellix.io/v1/payments",
                headers={"Authorization": 'Bearer ' + self.config.get("sellix_auth")},
                json={
                    "title": "Title",
                    "return_url": "http://1.1.1.1",
                    "email": self.mail,
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
            
            self.get_mail()

        except Exception as e:
            print(e)

    def complete(self, url):
        global reviews
        with open('feedback.txt', 'r', encoding='utf-8') as f:
            feedback = f.read().splitlines()
        quote = random.choice(feedback)

        invoice_id = url.split('/')[-1]
        try:
            headers = {"referer": f"url",
                       "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, "
                                     "like Gecko) Chrome/111.0.0.0 Safari/537.36"}
            score = 5 #how many stars you want
            r = Session(client_identifier="chrome108").post(
                f"https://{self.shop}.mysellix.io/api/shop/feedback/reply",
                json={"feedback": "positive", "message": quote, "score": score, "uniqid": invoice_id}, headers=headers)
            if r.json()['message'] == 'Feedback Sent Successfully.':
                print(datetime.now().strftime("%H:%M") , f"| {Fore.GREEN}SUCCESS{Fore.WHITE} | Sent Out Feedback Successfully {self.mail}" + Fore.RESET)
                reviews += 1
                return
            else:
                print(datetime.now().strftime("%H:%M") , f"| {Fore.RED}ERROR{Fore.WHITE} | Failed To Send Out Feedback {self.mail}" + Fore.RESET)
                return
        except Exception as e:
            print(e)
            self.complete(url)

reviews = 0
if __name__ == '__main__':
    clear()
    amount = int(input("How many reviews: "))
    clear()
    with open('mails.txt', 'r', encoding='utf-8') as f:
        mails = f.read().splitlines()
    while reviews < amount:
        with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
            futures = [executor.submit(Feedback(mail=mail.split(':')[0], password=mail.split(':')[1]).generate_invoice) for mail in mails[reviews:amount]]
            for future in concurrent.futures.as_completed(futures):
                pass
    

