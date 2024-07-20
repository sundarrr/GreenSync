import smtplib
from email.mime.text import MIMEText
import traceback

def send_email(recipient_email, subject, message):
    try:
        body = f"""
    <html>
<body style="
display: flex;
align-items: center;
justify-content: center;">
<div class="container" style="background: #fff;
padding: 35px 65px;
border-radius: 12px;
text-align: -webkit-center;
row-gap: 20px;
box-shadow: 0 5px 10px rgba(0, 0, 0, 0.1);">
<header style=" height: 75px;text-align: -webkit-center;color: #fff;">
<img style=" height: 75px;"
src="https://media.licdn.com/dms/image/D560BAQHObNJRmUcxDw/company-logo_200_200/0/1719256775362/kerigreen_logo?e=1729123200&v=beta&t=S_xHM_d--9krewK_l-EigIMu-FANeRPhYKtjRUsOyeg"/>
</header>
<h4>{message}</h4>
</div>
</body>
</html>
    """
        html_message = MIMEText(body, 'html')
        html_message['Subject'] = subject
        # print("subject")
        # print(subject)
        # print(recipient_email)
        # print(html_message.as_string())
        html_message['From'] = "bcstechnologies.in@gmail.com"
        html_message['To'] = recipient_email
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login("bcstechnologies.in@gmail.com", "zltsqeimgeimdgue")
            server.sendmail("bcstechnologies.in@gmail.com", recipient_email, html_message.as_string())
    except Exception as e:
        print(traceback.format_exc())